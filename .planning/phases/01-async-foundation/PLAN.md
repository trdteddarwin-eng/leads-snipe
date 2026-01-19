# Phase 1 Plan: Async Foundation

**Phase:** 1 of 7
**Goal:** Replace synchronous email verification with async system using aiosmtplib/aiodns
**Output:** `execution/async_verifier.py`

## Requirements Coverage

| Requirement | Task | Status |
|-------------|------|--------|
| ASYNC-01: Async email verification with aiosmtplib | Task 1.1 | Pending |
| ASYNC-02: Async MX resolution with aiodns | Task 1.2 | Pending |
| ASYNC-03: Parallel verification (50+ concurrent) | Task 1.3 | Pending |
| ASYNC-04: Catch-all domain detection | Task 1.4 | Pending |
| ASYNC-05: Greylist retry logic | Task 1.5 | Pending |

## Implementation Plan

### Wave 1: Core Infrastructure (Sequential Dependencies)

#### Task 1.1: Async SMTP Verification Core
**File:** `execution/async_verifier.py`
**Requirement:** ASYNC-01

Create the base `AsyncEmailVerifier` class with SMTP RCPT TO verification:

```python
# Core structure
class AsyncEmailVerifier:
    async def verify_single(self, email: str, mx_host: str) -> VerificationResult
```

**Implementation:**
1. Create `VerificationResult` dataclass with fields: email, valid, code, message, error, catch_all, greylist
2. Implement SMTP connection with aiosmtplib:
   - Port 25, no TLS
   - Valid HELO hostname ("verify.leadsnipe.io")
   - Empty MAIL FROM (standard verification)
   - RCPT TO for actual verification
3. Handle response codes: 250 (valid), 550 (invalid), 450/451 (greylist)
4. Set timeouts: 10s connect, 30s operation
5. Proper connection cleanup with `quit()`

**Acceptance:**
- [ ] Single email verification returns correct result
- [ ] Handles connection errors gracefully
- [ ] Timeouts work correctly

---

#### Task 1.2: Async MX Resolution with Caching
**File:** `execution/async_verifier.py`
**Requirement:** ASYNC-02

Add `MXResolver` class with aiodns and caching:

```python
class MXResolver:
    async def resolve(self, domain: str) -> list[str]
```

**Implementation:**
1. Initialize aiodns.DNSResolver
2. Query MX records, sort by priority
3. Cache results with 1-hour TTL
4. Handle DNS errors (return empty list)
5. Strip trailing dots from hostnames

**Acceptance:**
- [ ] MX resolution returns sorted list
- [ ] Cache hits don't make DNS queries
- [ ] DNS failures return empty list (not exception)

---

### Wave 2: Concurrency & Detection (Can run in parallel)

#### Task 1.3: Parallel Batch Verification
**File:** `execution/async_verifier.py`
**Requirement:** ASYNC-03

Add batch verification with semaphore control:

```python
async def verify_batch(self, emails: list[str]) -> list[VerificationResult]
```

**Implementation:**
1. Global semaphore for 50 max concurrent connections
2. Per-domain semaphore for 5 max concurrent (prevent single-domain abuse)
3. Use `asyncio.gather()` for parallel execution
4. Handle exceptions without failing entire batch
5. Group emails by domain for efficient MX reuse

**Acceptance:**
- [ ] 50 emails complete in <30 seconds
- [ ] No more than 50 concurrent connections
- [ ] No more than 5 connections per domain
- [ ] Single failure doesn't crash batch

---

#### Task 1.4: Catch-All Domain Detection
**File:** `execution/async_verifier.py`
**Requirement:** ASYNC-04

Add catch-all detection before verification:

```python
async def is_catch_all(self, domain: str) -> bool
```

**Implementation:**
1. Generate random 20-char email with timestamp
2. Test via SMTP RCPT TO
3. If random email accepted = catch-all domain
4. Cache results per domain (permanent for session)
5. Return `confidence: "low"` for emails on catch-all domains

**Acceptance:**
- [ ] Correctly identifies known catch-all domains
- [ ] Cache prevents repeated tests
- [ ] Catch-all emails marked with low confidence

---

#### Task 1.5: Greylist Retry Logic
**File:** `execution/async_verifier.py`
**Requirement:** ASYNC-05

Add non-blocking greylist retry:

```python
async def verify_with_retry(self, email: str) -> VerificationResult
```

**Implementation:**
1. Detect 450/451 response codes as greylist
2. Queue greylisted emails for retry
3. Wait 45 seconds before retry
4. Max 2 retries per email
5. Non-blocking: other emails continue while waiting

**Acceptance:**
- [ ] Greylisted emails are retried after delay
- [ ] Retry doesn't block other verifications
- [ ] After max retries, returns "greylist_timeout"

---

### Wave 3: Integration & Testing

#### Task 1.6: Public API & Sync Wrapper
**File:** `execution/async_verifier.py`

Create clean public API:

```python
# Async API
async def verify_emails(emails: list[str]) -> list[VerificationResult]

# Sync wrapper for non-async callers
def verify_emails_sync(emails: list[str]) -> list[VerificationResult]
```

**Implementation:**
1. Top-level function that instantiates verifier
2. Sync wrapper using `asyncio.run()`
3. Progress callback support (optional)
4. Summary statistics (valid, invalid, catch-all, greylist counts)

**Acceptance:**
- [ ] Can be called from sync code
- [ ] Returns structured results
- [ ] No event loop conflicts

---

#### Task 1.7: Unit Tests
**File:** `execution/test_async_verifier.py`

**Test Cases:**
1. `test_valid_email` - Known valid email returns valid=True
2. `test_invalid_email` - Known invalid email returns valid=False
3. `test_no_mx` - Domain without MX returns error
4. `test_catch_all_detection` - Catch-all domain detected correctly
5. `test_batch_concurrency` - 50 emails complete in <30s
6. `test_domain_rate_limit` - No more than 5 per domain concurrent
7. `test_greylist_retry` - Greylisted email retried after delay
8. `test_timeout_handling` - Slow server doesn't block batch

**Implementation:**
- Use pytest-asyncio
- Mock SMTP for unit tests
- Real SMTP for integration tests (optional, requires network)

---

## Execution Order

```
Wave 1 (Sequential):
  Task 1.1 → Task 1.2

Wave 2 (Parallel, after Wave 1):
  Task 1.3 | Task 1.4 | Task 1.5

Wave 3 (Sequential, after Wave 2):
  Task 1.6 → Task 1.7
```

## Success Criteria Verification

| Criterion | How to Verify |
|-----------|---------------|
| 50 emails in <30s | Run batch test with timer |
| Catch-all detection | Test against known catch-all (e.g., gmail.com is NOT catch-all, some corporate domains ARE) |
| Greylist retry works | Mock greylist response, verify retry happens |
| No blocking calls | Code review: no sync imports (smtplib, dns.resolver) |

## Dependencies

```
aiosmtplib>=3.0.1
aiodns>=3.2.0
pytest-asyncio>=0.23.0 (dev)
```

## Risks & Mitigations

| Risk | Mitigation | Task |
|------|------------|------|
| IP gets blacklisted | Rate limit per domain, valid HELO | 1.3 |
| Catch-all false positives | Test random email first | 1.4 |
| Event loop conflicts | asyncio.run() only at top level | 1.6 |

---
*Plan created: 2026-01-18*
