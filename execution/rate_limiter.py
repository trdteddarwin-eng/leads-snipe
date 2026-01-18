#!/usr/bin/env python3
"""
Adaptive Rate Limiter for LeadSnipe

Smart rate limiting to avoid bans while maximizing throughput:
- Per-domain request tracking
- Adaptive delays based on response codes (429, 503 = slow down)
- User-Agent rotation with quality scoring
- Backoff on consecutive failures

Usage:
    from rate_limiter import RateLimiter

    limiter = RateLimiter()
    headers = await limiter.acquire("example.com")
    response = requests.get(url, headers=headers)
    limiter.report_response("example.com", response.status_code)
"""

import time
import random
import threading
from collections import defaultdict
from typing import Dict, Optional, List
from datetime import datetime, timedelta


# High-quality User-Agent pool (weighted towards Chrome/Safari)
USER_AGENTS = [
    # Chrome on Windows (40% weight)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Chrome on macOS (25% weight)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Safari on macOS (15% weight)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Firefox (10% weight)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Edge (10% weight)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Weights for User-Agent selection (higher = more likely)
USER_AGENT_WEIGHTS = [
    4, 4, 3, 3,  # Chrome Windows
    3, 3, 2,     # Chrome macOS
    2, 2,        # Safari
    1, 1,        # Firefox
    1, 1,        # Edge
]

# Default rate limits by target type
RATE_LIMITS = {
    "serpapi": {
        "requests_per_second": 5,
        "base_delay": 0.2,
        "max_delay": 2.0,
    },
    "website": {
        "requests_per_domain_per_minute": 3,
        "base_delay": 1.0,
        "max_delay": 10.0,
    },
    "duckduckgo": {
        "requests_per_minute": 30,
        "base_delay": 2.0,
        "max_delay": 15.0,
    },
    "google": {
        "requests_per_minute": 10,
        "base_delay": 3.0,
        "max_delay": 20.0,
    },
    "smtp": {
        "connections_per_server": 2,
        "base_delay": 0.5,
        "max_delay": 5.0,
    },
}


class RateLimiter:
    """
    Adaptive rate limiter for web scraping and API calls.

    Features:
    - Per-domain request tracking
    - Adaptive delays based on response codes
    - User-Agent rotation with weighted selection
    - Thread-safe operation
    """

    def __init__(self, target_type: str = "website"):
        """
        Initialize rate limiter.

        Args:
            target_type: Type of target (website, duckduckgo, google, serpapi, smtp)
        """
        self.config = RATE_LIMITS.get(target_type, RATE_LIMITS["website"])
        self.target_type = target_type

        # Per-domain tracking
        self.domain_requests: Dict[str, List[float]] = defaultdict(list)  # timestamps
        self.domain_delays: Dict[str, float] = {}  # current delay per domain
        self.domain_failures: Dict[str, int] = defaultdict(int)  # consecutive failures

        # Thread safety
        self._lock = threading.Lock()

        # Stats
        self.stats = {
            "requests": 0,
            "rate_limited": 0,
            "delays_added": 0.0,
        }

    def _get_domain(self, url_or_domain: str) -> str:
        """Extract domain from URL or return as-is."""
        if "://" in url_or_domain:
            from urllib.parse import urlparse
            return urlparse(url_or_domain).netloc
        return url_or_domain

    def _clean_old_requests(self, domain: str, window_seconds: int = 60):
        """Remove request timestamps older than window."""
        cutoff = time.time() - window_seconds
        self.domain_requests[domain] = [
            ts for ts in self.domain_requests[domain] if ts > cutoff
        ]

    def _get_current_delay(self, domain: str) -> float:
        """Get current delay for a domain."""
        return self.domain_delays.get(domain, self.config["base_delay"])

    def _calculate_wait_time(self, domain: str) -> float:
        """Calculate how long to wait before next request."""
        with self._lock:
            self._clean_old_requests(domain)

            # Check requests in last minute
            recent_requests = len(self.domain_requests[domain])
            max_per_minute = self.config.get("requests_per_domain_per_minute",
                                              self.config.get("requests_per_minute", 30))

            if recent_requests >= max_per_minute:
                # Calculate wait time until oldest request expires
                if self.domain_requests[domain]:
                    oldest = min(self.domain_requests[domain])
                    wait = (oldest + 60) - time.time()
                    return max(0, wait)

            # Return current delay for this domain
            return self._get_current_delay(domain)

    def acquire(self, url_or_domain: str) -> Dict[str, str]:
        """
        Get permission to make a request, returns headers.
        Blocks until it's safe to proceed.

        Args:
            url_or_domain: URL or domain to request

        Returns:
            Dict of headers to use for the request
        """
        domain = self._get_domain(url_or_domain)

        # Wait if needed
        wait_time = self._calculate_wait_time(domain)
        if wait_time > 0:
            time.sleep(wait_time)
            with self._lock:
                self.stats["delays_added"] += wait_time

        # Record this request
        with self._lock:
            self.domain_requests[domain].append(time.time())
            self.stats["requests"] += 1

        # Return headers with rotated User-Agent
        return self._get_headers()

    def acquire_async(self, url_or_domain: str) -> Dict[str, str]:
        """
        Non-blocking version - returns headers immediately.
        Use report_response() to adjust delays.
        """
        domain = self._get_domain(url_or_domain)

        with self._lock:
            self.domain_requests[domain].append(time.time())
            self.stats["requests"] += 1

        return self._get_headers()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with rotated User-Agent."""
        ua = random.choices(USER_AGENTS, weights=USER_AGENT_WEIGHTS, k=1)[0]

        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    def report_response(self, url_or_domain: str, status_code: int):
        """
        Adjust delays based on response code.

        Args:
            url_or_domain: URL or domain that was requested
            status_code: HTTP status code received
        """
        domain = self._get_domain(url_or_domain)

        with self._lock:
            current_delay = self._get_current_delay(domain)

            if status_code == 429 or status_code == 503:
                # Rate limited - increase delay significantly
                new_delay = min(current_delay * 2.5, self.config["max_delay"])
                self.domain_delays[domain] = new_delay
                self.domain_failures[domain] += 1
                self.stats["rate_limited"] += 1

            elif status_code == 403:
                # Forbidden - might be blocked, increase delay
                new_delay = min(current_delay * 2.0, self.config["max_delay"])
                self.domain_delays[domain] = new_delay
                self.domain_failures[domain] += 1

            elif status_code >= 500:
                # Server error - slight increase
                new_delay = min(current_delay * 1.5, self.config["max_delay"])
                self.domain_delays[domain] = new_delay

            elif status_code == 200:
                # Success - gradually decrease delay
                new_delay = max(current_delay * 0.9, self.config["base_delay"])
                self.domain_delays[domain] = new_delay
                self.domain_failures[domain] = 0  # Reset failures

    def get_delay_for_domain(self, url_or_domain: str) -> float:
        """Get current delay for a specific domain."""
        domain = self._get_domain(url_or_domain)
        return self._get_current_delay(domain)

    def is_domain_blocked(self, url_or_domain: str, threshold: int = 5) -> bool:
        """Check if a domain appears to be blocking us."""
        domain = self._get_domain(url_or_domain)
        with self._lock:
            return self.domain_failures.get(domain, 0) >= threshold

    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                **self.stats,
                "domains_tracked": len(self.domain_requests),
                "domains_with_elevated_delays": sum(
                    1 for d, delay in self.domain_delays.items()
                    if delay > self.config["base_delay"]
                ),
            }

    def reset_domain(self, url_or_domain: str):
        """Reset tracking for a specific domain."""
        domain = self._get_domain(url_or_domain)
        with self._lock:
            self.domain_requests[domain] = []
            self.domain_delays.pop(domain, None)
            self.domain_failures[domain] = 0


class MultiRateLimiter:
    """
    Manages multiple rate limiters for different target types.
    """

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.Lock()

    def get(self, target_type: str) -> RateLimiter:
        """Get or create a rate limiter for a target type."""
        with self._lock:
            if target_type not in self.limiters:
                self.limiters[target_type] = RateLimiter(target_type)
            return self.limiters[target_type]

    def get_all_stats(self) -> Dict:
        """Get stats from all limiters."""
        with self._lock:
            return {
                name: limiter.get_stats()
                for name, limiter in self.limiters.items()
            }


# Global instance for easy access
_global_limiter = MultiRateLimiter()


def get_limiter(target_type: str = "website") -> RateLimiter:
    """Get the global rate limiter for a target type."""
    return _global_limiter.get(target_type)


if __name__ == "__main__":
    # Demo/test
    limiter = RateLimiter("website")

    print("Rate Limiter Demo")
    print("=" * 40)

    # Simulate requests
    for i in range(5):
        domain = f"example{i % 2}.com"
        headers = limiter.acquire(domain)
        print(f"Request {i+1} to {domain}")
        print(f"  User-Agent: {headers['User-Agent'][:50]}...")

        # Simulate response
        status = 200 if i < 3 else 429
        limiter.report_response(domain, status)
        print(f"  Status: {status}")
        print(f"  Current delay: {limiter.get_delay_for_domain(domain):.2f}s")

    print("\nStats:", limiter.get_stats())
