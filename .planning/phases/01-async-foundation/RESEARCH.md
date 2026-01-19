# Phase 1 Research: Async Foundation

## aiosmtplib API for Email Verification

### Basic RCPT TO Verification Pattern

```python
import aiosmtplib
from email.utils import formataddr

async def verify_email_smtp(email: str, mx_host: str) -> dict:
    """Verify email via SMTP RCPT TO without sending."""
    try:
        smtp = aiosmtplib.SMTP(
            hostname=mx_host,
            port=25,
            timeout=10,
            use_tls=False,
            start_tls=False
        )
        await smtp.connect()
        await smtp.ehlo("verify.leadsnipe.io")  # Valid HELO hostname

        # MAIL FROM with null sender (standard verification)
        await smtp.mail("")

        # RCPT TO - this is where verification happens
        code, message = await smtp.rcpt(email)

        await smtp.quit()

        # 250 = valid, 550 = invalid, 450/451 = greylist
        return {
            "email": email,
            "valid": code == 250,
            "code": code,
            "message": message,
            "greylist": code in (450, 451)
        }
    except aiosmtplib.SMTPException as e:
        return {"email": email, "valid": False, "error": str(e)}
```

### Key Points
- Use port 25 (standard SMTP), not 587 (submission)
- Empty MAIL FROM is standard for verification
- RCPT TO response codes: 250 (valid), 550 (invalid), 450/451 (greylist), 552 (mailbox full)
- Always call quit() to close cleanly

## Concurrency Control with Semaphores

### Pattern for 50 Concurrent Connections

```python
import asyncio
from typing import List

class AsyncEmailVerifier:
    def __init__(self, max_concurrent: int = 50):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.mx_cache: dict[str, list[str]] = {}

    async def verify_with_semaphore(self, email: str) -> dict:
        async with self.semaphore:
            return await self._verify_single(email)

    async def verify_batch(self, emails: List[str]) -> List[dict]:
        tasks = [self.verify_with_semaphore(email) for email in emails]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### Per-Domain Rate Limiting

```python
from collections import defaultdict

class DomainRateLimiter:
    def __init__(self, max_per_domain: int = 5):
        self.domain_semaphores: dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(max_per_domain)
        )

    async def acquire(self, domain: str):
        await self.domain_semaphores[domain].acquire()

    def release(self, domain: str):
        self.domain_semaphores[domain].release()
```

## Catch-All Detection Algorithm

### Strategy: Test Random Email First

```python
import secrets
import string

def generate_random_email(domain: str) -> str:
    """Generate obviously invalid email for catch-all test."""
    random_part = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(20))
    timestamp = int(time.time())
    return f"{random_part}{timestamp}@{domain}"

async def is_catch_all(domain: str, mx_host: str) -> bool:
    """
    Test if domain is catch-all by verifying random email.
    If random email is accepted, domain accepts anything.
    """
    test_email = generate_random_email(domain)
    result = await verify_email_smtp(test_email, mx_host)
    return result.get("valid", False)
```

### Integration with Verification

```python
async def verify_with_catch_all_check(email: str) -> dict:
    domain = email.split("@")[1]
    mx_records = await resolve_mx(domain)

    if not mx_records:
        return {"email": email, "valid": False, "reason": "no_mx"}

    mx_host = mx_records[0]

    # Check catch-all first (cache result per domain)
    if domain not in catch_all_cache:
        catch_all_cache[domain] = await is_catch_all(domain, mx_host)

    if catch_all_cache[domain]:
        return {
            "email": email,
            "valid": None,  # Unknown - could be valid
            "catch_all": True,
            "confidence": "low"
        }

    # Not catch-all, proceed with verification
    return await verify_email_smtp(email, mx_host)
```

## Greylist Retry Implementation

### Non-Blocking Retry Pattern

```python
async def verify_with_greylist_retry(
    email: str,
    mx_host: str,
    retry_delay: int = 45,
    max_retries: int = 2
) -> dict:
    """Verify email with greylist retry support."""

    for attempt in range(max_retries + 1):
        result = await verify_email_smtp(email, mx_host)

        if not result.get("greylist"):
            return result

        if attempt < max_retries:
            # Don't block - schedule retry and continue
            await asyncio.sleep(retry_delay)

    # Still greylisted after retries
    return {
        "email": email,
        "valid": None,
        "reason": "greylist_timeout",
        "attempts": max_retries + 1
    }
```

### Batch Greylist Handling

```python
async def verify_batch_with_greylist(emails: List[str]) -> List[dict]:
    """
    Verify batch, collecting greylisted emails for retry.
    Non-greylisted results return immediately.
    """
    results = {}
    pending = list(emails)
    greylist_queue = []

    # First pass
    first_pass = await asyncio.gather(*[
        verify_email_smtp(e, await get_mx(e)) for e in pending
    ])

    for email, result in zip(pending, first_pass):
        if result.get("greylist"):
            greylist_queue.append(email)
        else:
            results[email] = result

    # Retry greylisted after delay
    if greylist_queue:
        await asyncio.sleep(45)
        retry_results = await asyncio.gather(*[
            verify_email_smtp(e, await get_mx(e)) for e in greylist_queue
        ])
        for email, result in zip(greylist_queue, retry_results):
            results[email] = result

    return [results[e] for e in emails]
```

## MX Record Caching with aiodns

### Async MX Resolution

```python
import aiodns

class MXResolver:
    def __init__(self, ttl_seconds: int = 3600):
        self.resolver = aiodns.DNSResolver()
        self.cache: dict[str, tuple[list[str], float]] = {}
        self.ttl = ttl_seconds

    async def resolve(self, domain: str) -> list[str]:
        """Resolve MX records with caching."""
        now = time.time()

        # Check cache
        if domain in self.cache:
            records, cached_at = self.cache[domain]
            if now - cached_at < self.ttl:
                return records

        # Resolve fresh
        try:
            mx_records = await self.resolver.query(domain, "MX")
            # Sort by priority (lower = higher priority)
            sorted_mx = sorted(mx_records, key=lambda x: x.priority)
            hosts = [str(mx.host).rstrip('.') for mx in sorted_mx]

            self.cache[domain] = (hosts, now)
            return hosts
        except aiodns.error.DNSError:
            return []
```

## Complete Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AsyncEmailVerifier                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  MXResolver  │    │ CatchAllCache│    │ Semaphore │ │
│  │  (aiodns)    │    │ (per-domain) │    │ (50 max)  │ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
├─────────────────────────────────────────────────────────┤
│                    verify_batch()                        │
│  1. Resolve MX (cached)                                 │
│  2. Check catch-all (cached)                            │
│  3. SMTP RCPT TO verify                                 │
│  4. Handle greylist retry                               │
│  5. Return results                                      │
└─────────────────────────────────────────────────────────┘
```

## Dependencies

```
aiosmtplib>=3.0.1
aiodns>=3.2.0
```

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| IP blacklisting | Per-domain semaphore (5 concurrent), valid HELO |
| Catch-all false positives | Random email test before verification |
| Greylist delays | Non-blocking retry with 45s delay |
| Timeout cascades | 10s connect, 30s operation timeout |
| Event loop conflicts | Top-level asyncio.run() only |

---
*Research completed: 2026-01-18*
