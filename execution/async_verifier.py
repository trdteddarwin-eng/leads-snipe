"""
Async Email Verifier - Stealth Hybrid Lead Engine

High-performance async email verification using aiosmtplib and aiodns.
Verifies 50+ emails in parallel with catch-all detection and greylist retry.

Requirements covered:
- ASYNC-01: Async email verification with aiosmtplib
- ASYNC-02: Async MX resolution with aiodns
- ASYNC-03: Parallel verification (50+ concurrent)
- ASYNC-04: Catch-all domain detection
- ASYNC-05: Greylist retry logic
"""

import asyncio
import time
import secrets
import string
from dataclasses import dataclass, field
from typing import Optional, Callable
from collections import defaultdict

import aiosmtplib
import aiodns


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class VerificationResult:
    """Result of email verification."""
    email: str
    valid: Optional[bool] = None  # None = unknown (catch-all or error)
    code: Optional[int] = None
    message: str = ""
    error: Optional[str] = None
    catch_all: bool = False
    greylist: bool = False
    confidence: str = "high"  # high, low (catch-all), unknown
    method: str = "smtp"
    attempts: int = 1


@dataclass
class VerificationStats:
    """Summary statistics for batch verification."""
    total: int = 0
    valid: int = 0
    invalid: int = 0
    catch_all: int = 0
    greylist: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


# =============================================================================
# MX Resolver (ASYNC-02)
# =============================================================================

class MXResolver:
    """
    Async MX record resolver with caching.

    Uses aiodns for non-blocking DNS queries.
    Caches results for 1 hour to minimize DNS load.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.resolver = aiodns.DNSResolver()
        self._cache: dict[str, tuple[list[str], float]] = {}
        self.ttl = ttl_seconds

    async def resolve(self, domain: str) -> list[str]:
        """
        Resolve MX records for domain.

        Returns list of MX hostnames sorted by priority (lowest first).
        Returns empty list on DNS failure.
        """
        now = time.time()

        # Check cache
        if domain in self._cache:
            records, cached_at = self._cache[domain]
            if now - cached_at < self.ttl:
                return records

        # Resolve fresh
        try:
            mx_records = await self.resolver.query(domain, "MX")
            # Sort by priority (lower = higher priority)
            sorted_mx = sorted(mx_records, key=lambda x: x.priority)
            # Strip trailing dots from hostnames
            hosts = [str(mx.host).rstrip('.') for mx in sorted_mx]

            self._cache[domain] = (hosts, now)
            return hosts
        except aiodns.error.DNSError:
            # Cache negative result to avoid repeated failures
            self._cache[domain] = ([], now)
            return []
        except Exception:
            return []

    def clear_cache(self):
        """Clear the MX cache."""
        self._cache.clear()


# =============================================================================
# Async Email Verifier (ASYNC-01, ASYNC-03, ASYNC-04, ASYNC-05)
# =============================================================================

class AsyncEmailVerifier:
    """
    High-performance async email verifier.

    Features:
    - SMTP RCPT TO verification without sending
    - Parallel verification with configurable concurrency
    - Per-domain rate limiting
    - Catch-all domain detection
    - Greylist retry logic
    """

    def __init__(
        self,
        max_concurrent: int = 50,
        max_per_domain: int = 5,
        helo_hostname: str = "verify.leadsnipe.io",
        connect_timeout: int = 10,
        operation_timeout: int = 30,
        greylist_retry_delay: int = 45,
        greylist_max_retries: int = 2
    ):
        self.max_concurrent = max_concurrent
        self.max_per_domain = max_per_domain
        self.helo_hostname = helo_hostname
        self.connect_timeout = connect_timeout
        self.operation_timeout = operation_timeout
        self.greylist_retry_delay = greylist_retry_delay
        self.greylist_max_retries = greylist_max_retries

        # Shared resources
        self._mx_resolver = MXResolver()
        self._global_semaphore: Optional[asyncio.Semaphore] = None
        self._domain_semaphores: dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(self.max_per_domain)
        )
        self._catch_all_cache: dict[str, bool] = {}

    def _get_domain(self, email: str) -> str:
        """Extract domain from email address."""
        return email.split("@")[1].lower() if "@" in email else ""

    def _generate_random_email(self, domain: str) -> str:
        """Generate random email for catch-all testing."""
        random_part = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(20))
        timestamp = int(time.time())
        return f"{random_part}{timestamp}@{domain}"

    async def _smtp_verify(self, email: str, mx_host: str) -> VerificationResult:
        """
        Verify single email via SMTP RCPT TO.

        Response codes:
        - 250: Valid
        - 550, 551, 552, 553: Invalid
        - 450, 451: Greylist (temporary rejection)
        """
        result = VerificationResult(email=email)

        try:
            smtp = aiosmtplib.SMTP(
                hostname=mx_host,
                port=25,
                timeout=self.connect_timeout,
                use_tls=False,
                start_tls=False
            )

            await asyncio.wait_for(
                smtp.connect(),
                timeout=self.connect_timeout
            )

            try:
                await smtp.ehlo(self.helo_hostname)
                await smtp.mail("")  # Empty MAIL FROM for verification

                code, message = await asyncio.wait_for(
                    smtp.rcpt(email),
                    timeout=self.operation_timeout
                )

                result.code = code
                result.message = message

                if code == 250:
                    result.valid = True
                elif code in (450, 451):
                    result.valid = None
                    result.greylist = True
                    result.confidence = "unknown"
                elif code in (550, 551, 552, 553, 554):
                    result.valid = False
                else:
                    result.valid = None
                    result.confidence = "unknown"

            finally:
                try:
                    await smtp.quit()
                except Exception:
                    pass

        except asyncio.TimeoutError:
            result.error = "timeout"
            result.valid = None
            result.confidence = "unknown"
        except aiosmtplib.SMTPException as e:
            result.error = f"smtp_error: {str(e)}"
            result.valid = None
            result.confidence = "unknown"
        except Exception as e:
            result.error = f"error: {str(e)}"
            result.valid = None
            result.confidence = "unknown"

        return result

    async def is_catch_all(self, domain: str) -> bool:
        """
        Detect if domain is catch-all (accepts any email).

        Tests by verifying a random email - if accepted, domain is catch-all.
        Results are cached per domain for the session.
        """
        if domain in self._catch_all_cache:
            return self._catch_all_cache[domain]

        mx_records = await self._mx_resolver.resolve(domain)
        if not mx_records:
            self._catch_all_cache[domain] = False
            return False

        test_email = self._generate_random_email(domain)
        result = await self._smtp_verify(test_email, mx_records[0])

        is_catch_all = result.valid is True
        self._catch_all_cache[domain] = is_catch_all
        return is_catch_all

    async def verify_single(self, email: str) -> VerificationResult:
        """
        Verify a single email address.

        Includes catch-all detection and greylist retry.
        """
        domain = self._get_domain(email)
        if not domain:
            return VerificationResult(
                email=email,
                valid=False,
                error="invalid_format"
            )

        # Resolve MX
        mx_records = await self._mx_resolver.resolve(domain)
        if not mx_records:
            return VerificationResult(
                email=email,
                valid=False,
                error="no_mx_records"
            )

        mx_host = mx_records[0]

        # Check catch-all first
        if await self.is_catch_all(domain):
            return VerificationResult(
                email=email,
                valid=None,
                catch_all=True,
                confidence="low",
                message="Domain is catch-all, cannot verify individual addresses"
            )

        # Verify email with greylist retry
        return await self._verify_with_greylist_retry(email, mx_host)

    async def _verify_with_greylist_retry(
        self,
        email: str,
        mx_host: str
    ) -> VerificationResult:
        """
        Verify email with automatic greylist retry.

        Retries up to max_retries times with delay between attempts.
        """
        for attempt in range(self.greylist_max_retries + 1):
            result = await self._smtp_verify(email, mx_host)
            result.attempts = attempt + 1

            if not result.greylist:
                return result

            if attempt < self.greylist_max_retries:
                await asyncio.sleep(self.greylist_retry_delay)

        # Still greylisted after all retries
        result.error = "greylist_timeout"
        return result

    async def _verify_with_semaphores(self, email: str) -> VerificationResult:
        """Verify email with global and per-domain semaphore control."""
        domain = self._get_domain(email)

        async with self._global_semaphore:
            async with self._domain_semaphores[domain]:
                return await self.verify_single(email)

    async def verify_batch(
        self,
        emails: list[str],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list[VerificationResult]:
        """
        Verify multiple emails in parallel.

        Uses semaphores to control:
        - Global concurrency (max 50 simultaneous)
        - Per-domain concurrency (max 5 per domain)

        Args:
            emails: List of email addresses to verify
            progress_callback: Optional callback(completed, total) for progress updates

        Returns:
            List of VerificationResult in same order as input
        """
        if not emails:
            return []

        # Initialize global semaphore for this batch
        self._global_semaphore = asyncio.Semaphore(self.max_concurrent)

        # Create tasks
        tasks = [self._verify_with_semaphores(email) for email in emails]

        # Execute all in parallel (semaphores control actual concurrency)
        results = []
        completed = 0

        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1
            if progress_callback:
                progress_callback(completed, len(emails))

        # Reorder results to match input order
        email_to_result = {r.email: r for r in results}
        return [email_to_result[email] for email in emails]

    def clear_caches(self):
        """Clear MX and catch-all caches."""
        self._mx_resolver.clear_cache()
        self._catch_all_cache.clear()


# =============================================================================
# Public API (Task 1.6)
# =============================================================================

async def verify_emails(
    emails: list[str],
    max_concurrent: int = 50,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> tuple[list[VerificationResult], VerificationStats]:
    """
    Async API: Verify multiple emails in parallel.

    Args:
        emails: List of email addresses to verify
        max_concurrent: Maximum concurrent verifications (default 50)
        progress_callback: Optional callback(completed, total)

    Returns:
        Tuple of (results list, statistics)

    Example:
        results, stats = await verify_emails(["test@example.com", "user@domain.com"])
        for r in results:
            print(f"{r.email}: {'valid' if r.valid else 'invalid'}")
    """
    start_time = time.time()

    verifier = AsyncEmailVerifier(max_concurrent=max_concurrent)
    results = await verifier.verify_batch(emails, progress_callback)

    duration = time.time() - start_time

    # Calculate statistics
    stats = VerificationStats(
        total=len(results),
        valid=sum(1 for r in results if r.valid is True),
        invalid=sum(1 for r in results if r.valid is False),
        catch_all=sum(1 for r in results if r.catch_all),
        greylist=sum(1 for r in results if r.greylist and not r.catch_all),
        errors=sum(1 for r in results if r.error and not r.catch_all),
        duration_seconds=duration
    )

    return results, stats


def verify_emails_sync(
    emails: list[str],
    max_concurrent: int = 50,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> tuple[list[VerificationResult], VerificationStats]:
    """
    Sync wrapper: Verify multiple emails in parallel.

    Use this from synchronous code. Creates new event loop.

    Args:
        emails: List of email addresses to verify
        max_concurrent: Maximum concurrent verifications (default 50)
        progress_callback: Optional callback(completed, total)

    Returns:
        Tuple of (results list, statistics)

    Example:
        results, stats = verify_emails_sync(["test@example.com"])
        print(f"Valid: {stats.valid}/{stats.total}")
    """
    return asyncio.run(verify_emails(emails, max_concurrent, progress_callback))


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python async_verifier.py email1@domain.com email2@domain.com ...")
        print("\nExample:")
        print("  python async_verifier.py test@gmail.com user@company.com")
        sys.exit(1)

    emails_to_verify = sys.argv[1:]

    print(f"\nVerifying {len(emails_to_verify)} email(s)...\n")

    def progress(completed: int, total: int):
        print(f"Progress: {completed}/{total}", end="\r")

    results, stats = verify_emails_sync(emails_to_verify, progress_callback=progress)

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)

    for result in results:
        status = "VALID" if result.valid else "INVALID" if result.valid is False else "UNKNOWN"
        if result.catch_all:
            status = "CATCH-ALL"
        if result.error:
            status = f"ERROR ({result.error})"
        print(f"  {result.email}: {status}")

    print("\n" + "=" * 60)
    print("Statistics:")
    print("=" * 60)
    print(f"  Total:     {stats.total}")
    print(f"  Valid:     {stats.valid}")
    print(f"  Invalid:   {stats.invalid}")
    print(f"  Catch-all: {stats.catch_all}")
    print(f"  Greylist:  {stats.greylist}")
    print(f"  Errors:    {stats.errors}")
    print(f"  Duration:  {stats.duration_seconds:.2f}s")
