#!/usr/bin/env python3
"""
Redis Caching Layer for LeadSnipe Pipeline

Provides ultra-fast caching for:
- Decision maker emails by domain
- LinkedIn profiles by company/person
- Google Maps results by query

Installation:
    pip install redis

Setup (local development):
    brew install redis
    redis-server

Setup (production):
    Use Redis Cloud free tier: https://redis.com/try-free/

Usage:
    from cache_redis import LeadCache

    cache = LeadCache()

    # Check cache
    cached = cache.get_decision_maker("example.com")
    if cached:
        return cached

    # Store in cache
    cache.set_decision_maker("example.com", email_data)
"""

import os
import json
import hashlib
from typing import Optional, Dict, List
from datetime import timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not installed. Run: pip install redis")


class LeadCache:
    """
    Redis cache for lead generation pipeline.

    Falls back to no-op if Redis unavailable.
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (default: from env or localhost)
        """
        self.enabled = REDIS_AVAILABLE
        self.redis = None

        if not REDIS_AVAILABLE:
            return

        try:
            # Get Redis URL from env or use localhost
            redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

            # Connect to Redis
            self.redis = redis.from_url(redis_url, decode_responses=True)

            # Test connection
            self.redis.ping()

            print("✅ Redis cache connected")

        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("   Continuing without cache...")
            self.enabled = False

    def _make_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key."""
        # Hash long identifiers to keep keys short
        if len(identifier) > 50:
            identifier = hashlib.md5(identifier.encode()).hexdigest()
        return f"leadsnipe:{prefix}:{identifier}"

    # ========================================================================
    # Decision Maker Email Cache
    # ========================================================================

    def get_decision_maker(self, domain: str) -> Optional[Dict]:
        """
        Get cached decision maker email by domain.

        Args:
            domain: Company domain (e.g., "example.com")

        Returns:
            Cached decision maker dict or None
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key("dm", domain.lower())
            data = self.redis.get(key)

            if data:
                return json.loads(data)

        except Exception as e:
            print(f"   ⚠️  Cache read error: {e}")

        return None

    def set_decision_maker(self, domain: str, data: Dict, ttl_days: int = 30):
        """
        Cache decision maker email by domain.

        Args:
            domain: Company domain
            data: Decision maker dict (email, name, title, etc.)
            ttl_days: Cache TTL in days (default: 30)
        """
        if not self.enabled:
            return

        try:
            key = self._make_key("dm", domain.lower())
            self.redis.setex(
                key,
                timedelta(days=ttl_days),
                json.dumps(data)
            )
        except Exception as e:
            print(f"   ⚠️  Cache write error: {e}")

    # ========================================================================
    # LinkedIn Profile Cache
    # ========================================================================

    def get_linkedin(self, person_key: str) -> Optional[str]:
        """
        Get cached LinkedIn URL by person identifier.

        Args:
            person_key: Unique person identifier (e.g., "John Doe|Example Corp")

        Returns:
            LinkedIn URL or None
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key("li", person_key.lower())
            return self.redis.get(key)
        except Exception as e:
            print(f"   ⚠️  Cache read error: {e}")
            return None

    def set_linkedin(self, person_key: str, linkedin_url: str, ttl_days: int = 90):
        """
        Cache LinkedIn URL by person identifier.

        Args:
            person_key: Unique person identifier
            linkedin_url: LinkedIn profile URL
            ttl_days: Cache TTL in days (default: 90)
        """
        if not self.enabled:
            return

        try:
            key = self._make_key("li", person_key.lower())
            self.redis.setex(
                key,
                timedelta(days=ttl_days),
                linkedin_url
            )
        except Exception as e:
            print(f"   ⚠️  Cache write error: {e}")

    # ========================================================================
    # Google Maps Results Cache
    # ========================================================================

    def get_gmaps_results(self, query: str) -> Optional[List[Dict]]:
        """
        Get cached Google Maps results by query.

        Args:
            query: Search query (e.g., "HVAC contractor in Newark, NJ")

        Returns:
            List of business dicts or None
        """
        if not self.enabled:
            return None

        try:
            key = self._make_key("gmaps", query.lower())
            data = self.redis.get(key)

            if data:
                return json.loads(data)
        except Exception as e:
            print(f"   ⚠️  Cache read error: {e}")

        return None

    def set_gmaps_results(self, query: str, results: List[Dict], ttl_days: int = 7):
        """
        Cache Google Maps results by query.

        Args:
            query: Search query
            results: List of business dicts
            ttl_days: Cache TTL in days (default: 7)
        """
        if not self.enabled:
            return

        try:
            key = self._make_key("gmaps", query.lower())
            self.redis.setex(
                key,
                timedelta(days=ttl_days),
                json.dumps(results)
            )
        except Exception as e:
            print(f"   ⚠️  Cache write error: {e}")

    # ========================================================================
    # Batch Operations
    # ========================================================================

    def get_many_decision_makers(self, domains: List[str]) -> Dict[str, Dict]:
        """
        Get multiple decision makers in one call.

        Args:
            domains: List of company domains

        Returns:
            Dict mapping domain → decision maker data
        """
        if not self.enabled:
            return {}

        try:
            # Build keys
            keys = [self._make_key("dm", d.lower()) for d in domains]

            # Batch get
            pipeline = self.redis.pipeline()
            for key in keys:
                pipeline.get(key)
            results = pipeline.execute()

            # Parse results
            cached = {}
            for domain, data in zip(domains, results):
                if data:
                    cached[domain] = json.loads(data)

            return cached

        except Exception as e:
            print(f"   ⚠️  Batch cache read error: {e}")
            return {}

    # ========================================================================
    # Stats & Utilities
    # ========================================================================

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self.redis.info("stats")

            return {
                "enabled": True,
                "keys": self.redis.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1
                )
            }
        except Exception as e:
            print(f"   ⚠️  Stats error: {e}")
            return {"enabled": True, "error": str(e)}

    def clear_all(self):
        """Clear all LeadSnipe cache keys."""
        if not self.enabled:
            return

        try:
            keys = self.redis.keys("leadsnipe:*")
            if keys:
                self.redis.delete(*keys)
                print(f"🗑️  Cleared {len(keys)} cache keys")
        except Exception as e:
            print(f"   ⚠️  Clear error: {e}")


# Singleton instance
_cache_instance = None

def get_cache() -> LeadCache:
    """Get or create cache singleton."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LeadCache()
    return _cache_instance


if __name__ == '__main__':
    # Test cache
    cache = LeadCache()

    if cache.enabled:
        print("\n✅ Cache is enabled")

        # Test decision maker cache
        print("\n📧 Testing decision maker cache...")
        test_data = {
            "email": "john@example.com",
            "full_name": "John Doe",
            "job_title": "CEO"
        }
        cache.set_decision_maker("example.com", test_data)
        cached = cache.get_decision_maker("example.com")
        print(f"   Cached: {cached}")

        # Test stats
        print("\n📊 Cache stats:")
        stats = cache.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print("\n❌ Cache is not enabled")
        print("   Install Redis: brew install redis")
        print("   Start Redis: redis-server")
