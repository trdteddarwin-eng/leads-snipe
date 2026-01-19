"""
Unit Tests for Async Email Verifier

Tests cover all ASYNC requirements:
- ASYNC-01: Async email verification with aiosmtplib
- ASYNC-02: Async MX resolution with aiodns
- ASYNC-03: Parallel verification (50+ concurrent)
- ASYNC-04: Catch-all domain detection
- ASYNC-05: Greylist retry logic
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio

from async_verifier import (
    AsyncEmailVerifier,
    MXResolver,
    VerificationResult,
    verify_emails,
    verify_emails_sync,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def verifier():
    """Create a fresh verifier instance for each test."""
    return AsyncEmailVerifier(
        max_concurrent=50,
        max_per_domain=5,
        greylist_retry_delay=1,  # Short delay for tests
        greylist_max_retries=2
    )


@pytest.fixture
def mx_resolver():
    """Create a fresh MX resolver for each test."""
    return MXResolver(ttl_seconds=3600)


# =============================================================================
# MX Resolution Tests (ASYNC-02)
# =============================================================================

class TestMXResolver:
    """Tests for MX record resolution."""

    @pytest.mark.asyncio
    async def test_resolve_returns_sorted_list(self, mx_resolver):
        """MX resolution returns list sorted by priority."""
        # Mock aiodns response
        mock_mx1 = MagicMock()
        mock_mx1.priority = 10
        mock_mx1.host = "mx1.example.com."

        mock_mx2 = MagicMock()
        mock_mx2.priority = 5
        mock_mx2.host = "mx2.example.com."

        with patch.object(mx_resolver.resolver, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_mx1, mock_mx2]

            result = await mx_resolver.resolve("example.com")

            assert result == ["mx2.example.com", "mx1.example.com"]  # Sorted by priority
            assert result[0] == "mx2.example.com"  # Priority 5 first

    @pytest.mark.asyncio
    async def test_cache_hits_dont_query(self, mx_resolver):
        """Cache hits should not make DNS queries."""
        mock_mx = MagicMock()
        mock_mx.priority = 10
        mock_mx.host = "mx.example.com."

        with patch.object(mx_resolver.resolver, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_mx]

            # First call - should query
            await mx_resolver.resolve("example.com")
            assert mock_query.call_count == 1

            # Second call - should use cache
            await mx_resolver.resolve("example.com")
            assert mock_query.call_count == 1  # Still 1, not 2

    @pytest.mark.asyncio
    async def test_dns_failure_returns_empty_list(self, mx_resolver):
        """DNS failures should return empty list, not raise."""
        import aiodns

        with patch.object(mx_resolver.resolver, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = aiodns.error.DNSError()

            result = await mx_resolver.resolve("nonexistent.invalid")

            assert result == []

    @pytest.mark.asyncio
    async def test_strips_trailing_dots(self, mx_resolver):
        """Hostnames should have trailing dots stripped."""
        mock_mx = MagicMock()
        mock_mx.priority = 10
        mock_mx.host = "mx.example.com."  # With trailing dot

        with patch.object(mx_resolver.resolver, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_mx]

            result = await mx_resolver.resolve("example.com")

            assert result == ["mx.example.com"]  # No trailing dot


# =============================================================================
# SMTP Verification Tests (ASYNC-01)
# =============================================================================

class TestSMTPVerification:
    """Tests for SMTP email verification."""

    @pytest.mark.asyncio
    async def test_valid_email_returns_valid(self, verifier):
        """Valid email (250 response) should return valid=True."""
        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.example.com"]

            # Mock SMTP instance
            mock_smtp = AsyncMock()
            mock_smtp.connect = AsyncMock()
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = AsyncMock(return_value=(250, "OK"))
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            # Mock catch-all check to return False
            verifier._catch_all_cache["example.com"] = False

            result = await verifier.verify_single("test@example.com")

            assert result.valid is True
            assert result.code == 250

    @pytest.mark.asyncio
    async def test_invalid_email_returns_invalid(self, verifier):
        """Invalid email (550 response) should return valid=False."""
        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.example.com"]

            mock_smtp = AsyncMock()
            mock_smtp.connect = AsyncMock()
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = AsyncMock(return_value=(550, "User not found"))
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["example.com"] = False

            result = await verifier.verify_single("invalid@example.com")

            assert result.valid is False
            assert result.code == 550

    @pytest.mark.asyncio
    async def test_no_mx_returns_error(self, verifier):
        """Domain without MX records should return error."""
        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx:
            mock_mx.return_value = []  # No MX records

            result = await verifier.verify_single("test@nomx.invalid")

            assert result.valid is False
            assert result.error == "no_mx_records"

    @pytest.mark.asyncio
    async def test_handles_connection_errors(self, verifier):
        """Connection errors should be handled gracefully."""
        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.example.com"]

            mock_smtp = AsyncMock()
            mock_smtp.connect = AsyncMock(side_effect=ConnectionRefusedError())
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["example.com"] = False

            result = await verifier.verify_single("test@example.com")

            assert result.valid is None
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_timeout_handling(self, verifier):
        """Slow server should timeout, not block batch."""
        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.example.com"]

            async def slow_connect():
                await asyncio.sleep(100)  # Very slow

            mock_smtp = AsyncMock()
            mock_smtp.connect = slow_connect
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["example.com"] = False

            # Should timeout, not hang
            result = await asyncio.wait_for(
                verifier.verify_single("test@example.com"),
                timeout=15
            )

            assert result.error == "timeout"


# =============================================================================
# Catch-All Detection Tests (ASYNC-04)
# =============================================================================

class TestCatchAllDetection:
    """Tests for catch-all domain detection."""

    @pytest.mark.asyncio
    async def test_catch_all_detected_correctly(self, verifier):
        """Catch-all domain (accepts random email) should be detected."""
        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.catchall.com"]

            # Catch-all accepts any email
            mock_smtp = AsyncMock()
            mock_smtp.connect = AsyncMock()
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = AsyncMock(return_value=(250, "OK"))
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            is_catch_all = await verifier.is_catch_all("catchall.com")

            assert is_catch_all is True

    @pytest.mark.asyncio
    async def test_cache_prevents_repeated_tests(self, verifier):
        """Catch-all cache should prevent repeated tests."""
        verifier._catch_all_cache["cached.com"] = True

        # No mock needed - should use cache
        is_catch_all = await verifier.is_catch_all("cached.com")

        assert is_catch_all is True

    @pytest.mark.asyncio
    async def test_catch_all_emails_marked_low_confidence(self, verifier):
        """Emails on catch-all domains should have low confidence."""
        # Pre-populate catch-all cache
        verifier._catch_all_cache["catchall.com"] = True

        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx:
            mock_mx.return_value = ["mx.catchall.com"]

            result = await verifier.verify_single("anyone@catchall.com")

            assert result.catch_all is True
            assert result.confidence == "low"
            assert result.valid is None  # Unknown, not valid


# =============================================================================
# Greylist Retry Tests (ASYNC-05)
# =============================================================================

class TestGreylistRetry:
    """Tests for greylist retry logic."""

    @pytest.mark.asyncio
    async def test_greylist_retried_after_delay(self, verifier):
        """Greylisted emails should be retried after delay."""
        call_count = 0

        async def mock_rcpt(email):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (450, "Try again later")
            return (250, "OK")

        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.greylist.com"]

            mock_smtp = AsyncMock()
            mock_smtp.connect = AsyncMock()
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = mock_rcpt
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["greylist.com"] = False

            result = await verifier.verify_single("test@greylist.com")

            assert call_count >= 2  # Was retried
            assert result.valid is True  # Eventually succeeded
            assert result.attempts >= 2

    @pytest.mark.asyncio
    async def test_greylist_timeout_after_max_retries(self, verifier):
        """After max retries, should return greylist_timeout."""
        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.stubborn.com"]

            # Always greylist
            mock_smtp = AsyncMock()
            mock_smtp.connect = AsyncMock()
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = AsyncMock(return_value=(451, "Try again"))
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["stubborn.com"] = False

            result = await verifier.verify_single("test@stubborn.com")

            assert result.greylist is True
            assert result.error == "greylist_timeout"
            assert result.attempts == verifier.greylist_max_retries + 1


# =============================================================================
# Batch Concurrency Tests (ASYNC-03)
# =============================================================================

class TestBatchConcurrency:
    """Tests for parallel batch verification."""

    @pytest.mark.asyncio
    async def test_batch_completes_in_time(self, verifier):
        """50 emails should complete in reasonable time."""
        emails = [f"user{i}@example.com" for i in range(50)]

        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.example.com"]

            async def quick_connect():
                await asyncio.sleep(0.01)  # 10ms per connection

            mock_smtp = AsyncMock()
            mock_smtp.connect = quick_connect
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = AsyncMock(return_value=(250, "OK"))
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["example.com"] = False

            start = time.time()
            results = await verifier.verify_batch(emails)
            duration = time.time() - start

            assert len(results) == 50
            # With 50 concurrent, 50 emails at 10ms each should take ~10ms + overhead
            # Be generous with the assertion
            assert duration < 10  # Should be much faster than 10 seconds

    @pytest.mark.asyncio
    async def test_single_failure_doesnt_crash_batch(self, verifier):
        """One email failure should not crash the entire batch."""
        emails = ["good@example.com", "bad@example.com", "also_good@example.com"]

        call_count = 0

        async def mock_rcpt(email):
            nonlocal call_count
            call_count += 1
            if "bad" in email:
                return (550, "User not found")
            return (250, "OK")

        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.example.com"]

            mock_smtp = AsyncMock()
            mock_smtp.connect = AsyncMock()
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = mock_rcpt
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["example.com"] = False

            results = await verifier.verify_batch(emails)

            assert len(results) == 3
            # Results should be in input order
            assert results[0].email == "good@example.com"
            assert results[0].valid is True
            assert results[1].email == "bad@example.com"
            assert results[1].valid is False
            assert results[2].email == "also_good@example.com"
            assert results[2].valid is True

    @pytest.mark.asyncio
    async def test_domain_rate_limit(self, verifier):
        """Should not exceed max_per_domain concurrent connections."""
        verifier.max_per_domain = 2
        verifier._domain_semaphores.clear()  # Reset

        # Track concurrent connections per domain
        concurrent_counts = []
        current_concurrent = 0
        lock = asyncio.Lock()

        async def tracked_connect():
            nonlocal current_concurrent
            async with lock:
                current_concurrent += 1
                concurrent_counts.append(current_concurrent)
            await asyncio.sleep(0.05)  # Simulate work
            async with lock:
                current_concurrent -= 1

        emails = [f"user{i}@same-domain.com" for i in range(10)]

        with patch.object(verifier._mx_resolver, 'resolve', new_callable=AsyncMock) as mock_mx, \
             patch('aiosmtplib.SMTP') as mock_smtp_class:

            mock_mx.return_value = ["mx.same-domain.com"]

            mock_smtp = AsyncMock()
            mock_smtp.connect = tracked_connect
            mock_smtp.ehlo = AsyncMock()
            mock_smtp.mail = AsyncMock()
            mock_smtp.rcpt = AsyncMock(return_value=(250, "OK"))
            mock_smtp.quit = AsyncMock()
            mock_smtp_class.return_value = mock_smtp

            verifier._catch_all_cache["same-domain.com"] = False

            await verifier.verify_batch(emails)

            # Should never exceed max_per_domain
            max_concurrent = max(concurrent_counts) if concurrent_counts else 0
            assert max_concurrent <= verifier.max_per_domain


# =============================================================================
# Public API Tests (Task 1.6)
# =============================================================================

class TestPublicAPI:
    """Tests for public API functions."""

    @pytest.mark.asyncio
    async def test_verify_emails_returns_stats(self):
        """verify_emails should return results and statistics."""
        with patch('async_verifier.AsyncEmailVerifier') as mock_class:
            mock_verifier = AsyncMock()
            mock_verifier.verify_batch = AsyncMock(return_value=[
                VerificationResult(email="test@example.com", valid=True),
                VerificationResult(email="bad@example.com", valid=False),
            ])
            mock_class.return_value = mock_verifier

            results, stats = await verify_emails(["test@example.com", "bad@example.com"])

            assert len(results) == 2
            assert stats.total == 2
            assert stats.valid == 1
            assert stats.invalid == 1

    def test_sync_wrapper_works(self):
        """Sync wrapper should work from non-async code."""
        with patch('async_verifier.AsyncEmailVerifier') as mock_class:
            mock_verifier = AsyncMock()
            mock_verifier.verify_batch = AsyncMock(return_value=[
                VerificationResult(email="test@example.com", valid=True),
            ])
            mock_class.return_value = mock_verifier

            results, stats = verify_emails_sync(["test@example.com"])

            assert len(results) == 1
            assert stats.total == 1


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
