#!/usr/bin/env python3
"""
LinkedIn Stealth Search Module

Discover LinkedIn profiles without direct LinkedIn requests.
Uses search engines (DuckDuckGo, Bing) to find profiles indirectly.

Key Features:
- DuckDuckGo search (primary - no rate limits, no API key)
- Bing fallback (when DDG fails or rate limits)
- Snippet parsing (extract name/title from search results)
- No direct linkedin.com requests (avoids ToS issues)

Usage:
    from execution.linkedin_stealth import search_duckduckgo, search_bing, parse_linkedin_snippet

    # Search for a LinkedIn profile
    result = await search_duckduckgo("John Smith", "Acme Corp")
    if result:
        parsed = parse_linkedin_snippet(result['title'], result['body'])
        print(f"Found: {parsed['name']} - {parsed['title']}")
"""

import re
import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from functools import partial

try:
    from duckduckgo_search import DDGS
    HAS_DDG = True
except ImportError:
    HAS_DDG = False

try:
    import httpx
    from bs4 import BeautifulSoup
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# =============================================================================
# Constants and Patterns
# =============================================================================

# LinkedIn profile URL pattern
# Handles: linkedin.com/in/username, www.linkedin.com/in/username
# Also handles country codes like uk.linkedin.com/in/username
LINKEDIN_PROFILE_PATTERN = re.compile(
    r'https?://(?:[a-z]{2}\.)?(?:www\.)?(?:mobile\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?(?:\?.*)?$',
    re.IGNORECASE
)

# Usernames that are not real profiles (common LinkedIn paths to filter)
INVALID_USERNAMES = frozenset({
    'share',
    'company',
    'jobs',
    'feed',
    'in',
    'posts',
    'pulse',
    'login',
    'signup',
    'learning',
    'sales',
    'talent',
    'ads',
    'business',
    'help',
    'legal',
    'about',
    'premium',
})

# User agent rotation for Bing requests
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]


@dataclass
class LinkedInResult:
    """Result of a LinkedIn profile discovery."""
    linkedin_url: Optional[str] = None
    owner_name: Optional[str] = None
    owner_title: Optional[str] = None
    source: str = ""  # 'duckduckgo' or 'bing'
    confidence: float = 0.0  # 0.0-1.0 confidence score
    raw_result: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'linkedin_url': self.linkedin_url,
            'owner_name': self.owner_name,
            'owner_title': self.owner_title,
            'source': self.source,
            'confidence': self.confidence,
        }


# =============================================================================
# Task 4.1: DuckDuckGo LinkedIn Search
# =============================================================================

def _is_valid_linkedin_url(url: str) -> bool:
    """
    Check if URL is a valid LinkedIn profile URL.

    Filters out non-profile paths like /company/, /jobs/, etc.
    """
    if not url:
        return False

    match = LINKEDIN_PROFILE_PATTERN.match(url)
    if not match:
        return False

    username = match.group(1).lower()
    return username not in INVALID_USERNAMES


def _extract_linkedin_url(href: str) -> Optional[str]:
    """
    Extract and normalize a LinkedIn profile URL from a search result href.

    Returns normalized URL or None if not a valid profile.
    """
    if not href:
        return None

    # Handle DuckDuckGo redirect URLs
    if 'uddg=' in href:
        # Extract actual URL from DDG tracking
        import urllib.parse
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        if 'uddg' in parsed:
            href = parsed['uddg'][0]

    match = LINKEDIN_PROFILE_PATTERN.match(href)
    if match:
        username = match.group(1)
        if username.lower() not in INVALID_USERNAMES:
            return f"https://linkedin.com/in/{username}/"

    return None


async def search_duckduckgo(name: str, company: str, max_retries: int = 3) -> Optional[Dict]:
    """
    Search DuckDuckGo for LinkedIn profiles.

    Uses site:linkedin.com/in search with name and company.
    Runs DDGS in thread executor for async compatibility.

    Args:
        name: Person's name to search for
        company: Company name for context
        max_retries: Number of retry attempts on rate limit (default 3)

    Returns:
        Dict with keys: href, title, body - or None if not found

    Example:
        result = await search_duckduckgo("John Smith", "Acme Corp")
        if result:
            print(f"Found: {result['href']}")
    """
    if not HAS_DDG:
        return None

    if not name or not company:
        return None

    # Build search query
    query = f'site:linkedin.com/in "{name}" "{company}"'

    def _do_search():
        """Synchronous DDG search to run in executor."""
        try:
            ddgs = DDGS()
            results = ddgs.text(query, backend="html", max_results=5)
            return list(results) if results else []
        except Exception:
            return []

    loop = asyncio.get_event_loop()

    for attempt in range(max_retries):
        try:
            # Run sync DDGS in thread executor
            results = await loop.run_in_executor(None, _do_search)

            if not results:
                return None

            # Filter to valid LinkedIn profile URLs
            for result in results:
                href = result.get('href', '')
                linkedin_url = _extract_linkedin_url(href)

                if linkedin_url:
                    return {
                        'href': linkedin_url,
                        'title': result.get('title', ''),
                        'body': result.get('body', ''),
                    }

            # No valid LinkedIn URLs found
            return None

        except Exception as e:
            error_str = str(e).lower()

            # Check for rate limiting (202 status or rate limit message)
            if '202' in error_str or 'rate' in error_str:
                if attempt < max_retries - 1:
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = 2 ** (attempt + 1)
                    await asyncio.sleep(wait_time)
                    continue

            # Other errors - return None
            return None

    return None


# Placeholder for tasks 4.2 and 4.3 - will be added in subsequent tasks
