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
- Batch processing with concurrency control

Public API:
    from execution.linkedin_stealth import find_linkedin, find_linkedin_batch, find_linkedin_sync

    # Async single search (recommended)
    result = await find_linkedin("John Smith", "Acme Corp")
    if result.linkedin_url:
        print(f"Found: {result.linkedin_url}")

    # Sync wrapper for non-async code
    result = find_linkedin_sync("John Smith", "Acme Corp")

    # Batch processing with concurrency control
    leads = [{'name': 'John', 'company': 'Acme'}, ...]
    results = await find_linkedin_batch(leads, max_concurrent=5)

CLI:
    python linkedin_stealth.py "John Smith" "Acme Corp"
"""

import re
import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable
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


# =============================================================================
# Task 4.2: Snippet Name/Title Extraction
# =============================================================================

# Common LinkedIn title suffixes to strip
LINKEDIN_SUFFIXES = [
    ' | LinkedIn',
    ' - LinkedIn',
    ' on LinkedIn',
    ' LinkedIn',
]

# Patterns for name validation
NAME_MIN_LENGTH = 3
NAME_MAX_LENGTH = 50
NAME_MIN_WORDS = 2

# Title prefixes/suffixes to preserve in names
NAME_PREFIXES = {'dr', 'dr.', 'mr', 'mr.', 'mrs', 'mrs.', 'ms', 'ms.', 'prof', 'prof.'}
NAME_SUFFIXES = {'jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv', 'phd', 'md', 'esq', 'cpa'}


def _clean_linkedin_title(title: str) -> str:
    """Remove LinkedIn branding from title string."""
    if not title:
        return ""

    cleaned = title.strip()
    for suffix in LINKEDIN_SUFFIXES:
        if cleaned.lower().endswith(suffix.lower()):
            cleaned = cleaned[:-len(suffix)].strip()

    return cleaned


def _is_valid_name(name: str) -> bool:
    """
    Validate if a string looks like a person's name.

    Rules:
    - 2+ words (allows Dr. Jane, Jr. suffixes, etc.)
    - Reasonable length (3-50 chars)
    - Not all uppercase (probably acronym)
    - Not all lowercase (probably not a name)
    """
    if not name:
        return False

    name = name.strip()

    # Length check
    if len(name) < NAME_MIN_LENGTH or len(name) > NAME_MAX_LENGTH:
        return False

    # Word count check
    words = name.split()
    if len(words) < NAME_MIN_WORDS:
        return False

    # Not all uppercase (unless 2 letters like initials)
    if name.isupper() and len(name) > 4:
        return False

    # At least one word should be capitalized (not all lowercase)
    has_capitalized = any(
        word[0].isupper()
        for word in words
        if word and word[0].isalpha()
    )
    if not has_capitalized:
        return False

    return True


def _extract_name_from_title(title_part: str) -> Optional[str]:
    """Extract and validate a name from the first part of a title."""
    if not title_part:
        return None

    name = title_part.strip()

    # Handle case where name has trailing comma
    if ',' in name:
        name = name.split(',')[0].strip()

    # Validate
    if _is_valid_name(name):
        return name

    return None


def _extract_title_from_part(title_part: str) -> Optional[str]:
    """Extract job title from a title part, handling 'at Company' format."""
    if not title_part:
        return None

    title = title_part.strip()

    # Handle "Title at Company" format
    if ' at ' in title.lower():
        idx = title.lower().find(' at ')
        title = title[:idx].strip()

    # Handle trailing commas
    if ',' in title:
        title = title.split(',')[0].strip()

    # Basic validation - not empty, reasonable length
    if title and 2 < len(title) < 100:
        return title

    return None


def parse_linkedin_snippet(title: str, body: str) -> Dict[str, Optional[str]]:
    """
    Parse LinkedIn search snippet to extract name and job title.

    Handles common LinkedIn title formats:
    - "John Smith - CEO - Company Inc | LinkedIn"
    - "John Smith | LinkedIn"
    - "Dr. Jane Doe - VP of Engineering | LinkedIn"
    - "John Smith - Software Engineer at Company | LinkedIn"

    Args:
        title: The search result title (usually "Name - Title | LinkedIn")
        body: The search result body/snippet (for additional context)

    Returns:
        Dict with keys 'name' and 'title', each Optional[str]
        Never throws on malformed input.

    Examples:
        >>> parse_linkedin_snippet("John Smith - CEO | LinkedIn", "")
        {'name': 'John Smith', 'title': 'CEO'}

        >>> parse_linkedin_snippet("John Smith | LinkedIn", "")
        {'name': 'John Smith', 'title': None}
    """
    result = {'name': None, 'title': None}

    try:
        if not title:
            return result

        # Clean LinkedIn branding
        cleaned = _clean_linkedin_title(title)
        if not cleaned:
            return result

        # Split by common delimiters
        # Try ' - ' first (most common), then ' | '
        if ' - ' in cleaned:
            parts = cleaned.split(' - ')
        elif ' | ' in cleaned:
            parts = cleaned.split(' | ')
        else:
            # No delimiter - whole thing might be a name
            if _is_valid_name(cleaned):
                result['name'] = cleaned
            return result

        # First part is typically the name
        if parts:
            name = _extract_name_from_title(parts[0])
            if name:
                result['name'] = name

        # Second part (if exists) is typically the title
        if len(parts) > 1:
            job_title = _extract_title_from_part(parts[1])
            if job_title:
                result['title'] = job_title

    except Exception:
        # Never throw on malformed input
        pass

    return result


# =============================================================================
# Task 4.3: Bing Fallback Search
# =============================================================================

# Bing search URL
BING_SEARCH_URL = "https://www.bing.com/search"

# Minimum delay between Bing requests (seconds)
BING_MIN_DELAY = 3.0
BING_MAX_DELAY = 5.0


def _get_bing_headers() -> Dict[str, str]:
    """
    Get realistic headers for Bing requests.

    Uses random user agent rotation to avoid detection.
    """
    user_agent = random.choice(USER_AGENTS)

    return {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.bing.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def _extract_linkedin_from_bing_result(element) -> Optional[Dict]:
    """
    Extract LinkedIn URL and metadata from a Bing search result element.

    Args:
        element: BeautifulSoup element (li.b_algo)

    Returns:
        Dict with href, title, body or None
    """
    try:
        # Find the title link
        h2 = element.find('h2')
        if not h2:
            return None

        link = h2.find('a', href=True)
        if not link:
            return None

        href = link.get('href', '')

        # Validate it's a LinkedIn profile URL
        linkedin_url = _extract_linkedin_url(href)
        if not linkedin_url:
            return None

        # Get title text
        title = link.get_text(strip=True)

        # Get snippet/body (usually in p tag or div.b_caption)
        body = ""
        caption = element.find('div', class_='b_caption')
        if caption:
            p = caption.find('p')
            if p:
                body = p.get_text(strip=True)

        return {
            'href': linkedin_url,
            'title': title,
            'body': body,
        }

    except Exception:
        return None


async def search_bing(name: str, company: str) -> Optional[Dict]:
    """
    Search Bing for LinkedIn profiles as fallback when DDG fails.

    Uses HTML scraping with realistic headers to avoid bot detection.
    More conservative delays (3-5s) as Bing is aggressive on rate limiting.

    Args:
        name: Person's name to search for
        company: Company name for context

    Returns:
        Dict with keys: href, title, body - or None if not found/blocked

    Note:
        - Returns None immediately on 403/CAPTCHA (does not retry)
        - Uses 3-5 second random delays
        - Rotates User-Agent on each request
    """
    if not HAS_HTTPX:
        return None

    if not name or not company:
        return None

    # Build search query
    query = f'site:linkedin.com/in "{name}" "{company}"'

    # Build URL with query params
    import urllib.parse
    params = {
        'q': query,
        'count': '10',
    }
    url = f"{BING_SEARCH_URL}?{urllib.parse.urlencode(params)}"

    # Random delay before request (3-5 seconds)
    delay = random.uniform(BING_MIN_DELAY, BING_MAX_DELAY)
    await asyncio.sleep(delay)

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            headers = _get_bing_headers()
            response = await client.get(url, headers=headers)

            # Handle rate limiting / blocking
            if response.status_code in (403, 429):
                # Blocked or rate limited - return None, don't retry
                return None

            if response.status_code != 200:
                return None

            # Check for CAPTCHA in response
            if 'captcha' in response.text.lower() or 'unusual traffic' in response.text.lower():
                return None

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find search results (li.b_algo > h2 a)
            results = soup.find_all('li', class_='b_algo')

            for result_elem in results:
                result = _extract_linkedin_from_bing_result(result_elem)
                if result:
                    return result

            # No valid LinkedIn URLs found
            return None

    except httpx.TimeoutException:
        return None
    except httpx.RequestError:
        return None
    except Exception:
        return None


# =============================================================================
# Task 4.4: Public API & Multi-Strategy Orchestration
# =============================================================================

# Default confidence for snippet-extracted data (low - unverified)
DEFAULT_CONFIDENCE = 0.3


async def find_linkedin(name: str, company: str, location: str = "") -> LinkedInResult:
    """
    Find LinkedIn profile for a person using multi-strategy search.

    Primary search uses DuckDuckGo. Falls back to Bing on DDG failure/rate-limit.
    Never makes direct requests to linkedin.com.

    Args:
        name: Person's full name (e.g., "John Smith")
        company: Company name for context (e.g., "Acme Corp")
        location: Optional location hint (currently unused, for future expansion)

    Returns:
        LinkedInResult with linkedin_url, owner_name, owner_title, source, confidence
        On failure, returns LinkedInResult with all fields None/empty

    Example:
        result = await find_linkedin("John Smith", "Acme Corp")
        if result.linkedin_url:
            print(f"Found: {result.linkedin_url}")
            print(f"Name: {result.owner_name}, Title: {result.owner_title}")
    """
    # Validate inputs
    if not name or not company:
        return LinkedInResult()

    # Strategy 1: DuckDuckGo (primary - no rate limits, no API key)
    ddg_result = await search_duckduckgo(name, company)

    if ddg_result:
        # Parse snippet for name/title
        parsed = parse_linkedin_snippet(ddg_result.get('title', ''), ddg_result.get('body', ''))

        return LinkedInResult(
            linkedin_url=ddg_result.get('href'),
            owner_name=parsed.get('name'),
            owner_title=parsed.get('title'),
            source='duckduckgo',
            confidence=DEFAULT_CONFIDENCE,
            raw_result=ddg_result,
        )

    # Strategy 2: Bing fallback (on DDG failure/rate-limit)
    bing_result = await search_bing(name, company)

    if bing_result:
        # Parse snippet for name/title
        parsed = parse_linkedin_snippet(bing_result.get('title', ''), bing_result.get('body', ''))

        return LinkedInResult(
            linkedin_url=bing_result.get('href'),
            owner_name=parsed.get('name'),
            owner_title=parsed.get('title'),
            source='bing',
            confidence=DEFAULT_CONFIDENCE,
            raw_result=bing_result,
        )

    # Both strategies failed - return empty result
    return LinkedInResult()


async def find_linkedin_batch(
    leads: List[Dict],
    max_concurrent: int = 5,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Dict]:
    """
    Find LinkedIn profiles for multiple leads with concurrency control.

    Processes leads in parallel within semaphore limit (default 5 concurrent).
    Uses asyncio.Semaphore to prevent overwhelming search engines.

    Args:
        leads: List of dicts with 'name' and 'company' keys
               Example: [{'name': 'John Smith', 'company': 'Acme Corp'}, ...]
        max_concurrent: Maximum concurrent searches (default 5, conservative)
        progress_callback: Optional callback(completed: int, total: int) for progress

    Returns:
        List of dicts with original lead data plus:
        - linkedin_url: Profile URL or None
        - owner_name: Parsed name or None
        - owner_title: Parsed title or None
        - source: 'duckduckgo', 'bing', or '' if not found

    Example:
        leads = [
            {'name': 'John Smith', 'company': 'Acme Corp', 'email': 'john@acme.com'},
            {'name': 'Jane Doe', 'company': 'Tech Inc', 'email': 'jane@tech.com'},
        ]
        results = await find_linkedin_batch(leads, max_concurrent=3)
        for r in results:
            print(f"{r['name']}: {r.get('linkedin_url', 'Not found')}")
    """
    if not leads:
        return []

    semaphore = asyncio.Semaphore(max_concurrent)
    completed = 0
    total = len(leads)

    async def process_lead(lead: Dict) -> Dict:
        nonlocal completed

        async with semaphore:
            name = lead.get('name', '')
            company = lead.get('company', '')

            result = await find_linkedin(name, company)

            # Merge original lead data with result
            enriched = lead.copy()
            enriched['linkedin_url'] = result.linkedin_url
            enriched['owner_name'] = result.owner_name
            enriched['owner_title'] = result.owner_title
            enriched['source'] = result.source

            completed += 1
            if progress_callback:
                try:
                    progress_callback(completed, total)
                except Exception:
                    pass  # Don't let callback errors break processing

            return enriched

    # Process all leads with concurrency control
    tasks = [process_lead(lead) for lead in leads]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and return valid results
    return [r for r in results if isinstance(r, dict)]


def find_linkedin_sync(name: str, company: str, location: str = "") -> LinkedInResult:
    """
    Synchronous wrapper for find_linkedin().

    Convenience function for non-async code paths. Creates new event loop
    if none exists, otherwise uses existing loop.

    Args:
        name: Person's full name
        company: Company name for context
        location: Optional location hint

    Returns:
        LinkedInResult (same as find_linkedin)

    Example:
        result = find_linkedin_sync("John Smith", "Acme Corp")
        print(f"Found: {result.linkedin_url}")
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - use asyncio.run()
        return asyncio.run(find_linkedin(name, company, location))

    # If there's already a running loop, we need to handle differently
    # This is a rare case (usually from Jupyter notebooks or nested async)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(asyncio.run, find_linkedin(name, company, location))
        return future.result()


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys

    def main():
        """CLI entry point for manual testing."""
        if len(sys.argv) < 3:
            print("Usage: python linkedin_stealth.py \"Name\" \"Company\"")
            print("Example: python linkedin_stealth.py \"John Smith\" \"Acme Corp\"")
            sys.exit(1)

        name = sys.argv[1]
        company = sys.argv[2]

        print(f"Searching for: {name} at {company}")
        print("-" * 50)

        result = find_linkedin_sync(name, company)

        print(f"LinkedIn URL: {result.linkedin_url or 'Not found'}")
        print(f"Owner Name:   {result.owner_name or 'Not found'}")
        print(f"Owner Title:  {result.owner_title or 'Not found'}")
        print(f"Source:       {result.source or 'None'}")
        print(f"Confidence:   {result.confidence:.2f}")

        if result.linkedin_url:
            sys.exit(0)
        else:
            sys.exit(1)

    main()
