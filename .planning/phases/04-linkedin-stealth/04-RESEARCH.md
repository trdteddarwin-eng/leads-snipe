# Phase 4: LinkedIn Stealth - Research

**Researched:** 2026-01-20
**Domain:** Search engine scraping for LinkedIn profile discovery
**Confidence:** HIGH

## Summary

This phase implements LinkedIn profile discovery via search engine snippets, avoiding direct LinkedIn requests. The approach uses DuckDuckGo's HTML endpoint (primary) with Bing HTML scraping (fallback) to find LinkedIn profiles and extract name/title from search snippets.

The existing codebase already has a working implementation in `linkedin_finder_unified.py` that demonstrates the core pattern. This phase builds on that foundation with improvements: async support, better name/title extraction, and Bing fallback as specified in requirements.

**Primary recommendation:** Use the `duckduckgo-search` library (or newer `ddgs` package) with HTML backend, site-restricted queries (`site:linkedin.com/in`), and regex-based URL/snippet parsing. Implement Bing HTML scraping as fallback.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| duckduckgo-search | 8.1.1+ | DuckDuckGo search API | Official Python wrapper, handles HTML/lite endpoints, no API key |
| httpx | 0.24+ | Async HTTP client | Already used in sitemap_sniper.py, async-native |
| beautifulsoup4 | 4.12+ | HTML parsing | For Bing fallback parsing, already in codebase |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re | stdlib | Regex matching | LinkedIn URL extraction, name parsing |
| asyncio | stdlib | Async orchestration | Batch processing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| duckduckgo-search | Raw HTTP to html.duckduckgo.com | More control but more maintenance |
| httpx | aiohttp | httpx already in codebase, better async API |
| Bing scraping | SerpAPI | Cost ($50+/mo) vs free but less reliable |

**Installation:**
```bash
pip install duckduckgo-search httpx beautifulsoup4
```

## Architecture Patterns

### Recommended Project Structure
```
execution/
    linkedin_stealth.py     # Main module (this phase output)
    rate_limiter.py         # Existing - reuse for DDG/Bing
    linkedin_finder_unified.py  # Existing - reference implementation
```

### Pattern 1: Multi-Strategy Search with Fallback
**What:** Try DuckDuckGo first, fall back to Bing on failure
**When to use:** Every search operation
**Example:**
```python
# Pattern from existing linkedin_finder_unified.py
async def find_linkedin(business_name: str, owner_name: str = None) -> Optional[str]:
    """
    Multi-strategy LinkedIn discovery.

    Order:
    1. DuckDuckGo HTML endpoint (primary)
    2. Bing HTML scraping (fallback)
    """
    # Try DuckDuckGo first
    result = await search_duckduckgo(business_name, owner_name)
    if result:
        return result

    # Fallback to Bing
    return await search_bing(business_name, owner_name)
```

### Pattern 2: Site-Restricted Query Construction
**What:** Build queries that target LinkedIn profiles specifically
**When to use:** All LinkedIn searches
**Example:**
```python
# Query patterns from existing find_linkedin_smart.py
def build_query(business_name: str, owner_name: str = None, location: str = "") -> str:
    """
    Build site-restricted search query.

    Patterns:
    1. With name: site:linkedin.com/in "John Smith" "Company Name"
    2. Without name: site:linkedin.com/in "Company Name" owner founder CEO
    """
    base = 'site:linkedin.com/in'

    if owner_name:
        return f'{base} "{owner_name}" "{business_name}"'
    else:
        return f'{base} "{business_name}" owner OR founder OR CEO {location}'
```

### Pattern 3: Snippet Parsing for Name/Title
**What:** Extract name and job title from search result title
**When to use:** After getting search results
**Example:**
```python
# LinkedIn titles typically format as: "Name - Title - Company | LinkedIn"
import re

def parse_linkedin_snippet(title: str, body: str) -> dict:
    """
    Extract name and title from LinkedIn search snippet.

    Title formats vary:
    - "John Smith - CEO - Company Inc | LinkedIn"
    - "John Smith | LinkedIn"
    - "John Smith - Software Engineer at Company"
    """
    result = {"name": None, "title": None}

    # Remove LinkedIn suffix
    title = re.sub(r'\s*\|\s*LinkedIn\s*$', '', title)
    title = re.sub(r'\s*-\s*LinkedIn\s*$', '', title)

    # Split by common delimiters
    parts = re.split(r'\s*[-|]\s*', title)

    if len(parts) >= 1:
        # First part is usually the name
        result["name"] = parts[0].strip()

    if len(parts) >= 2:
        # Second part is often the title
        result["title"] = parts[1].strip()

    return result
```

### Anti-Patterns to Avoid
- **Direct LinkedIn requests:** Never hit linkedin.com directly - violates ToS and gets IP banned
- **Fixed delays:** Use adaptive rate limiting, not static sleep
- **Single search strategy:** Always have fallback (DDG fails sometimes)
- **Trusting snippet parsing completely:** Use LOW confidence for snippet-extracted names

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DuckDuckGo search | Custom HTTP scraper | duckduckgo-search library | Handles rate limits, backends, parsing |
| Rate limiting | Simple sleep() | rate_limiter.py (exists) | Adaptive delays, per-domain tracking |
| User-Agent rotation | Static headers | rate_limiter.py (exists) | Weighted rotation, realistic headers |
| LinkedIn URL validation | Basic string check | Regex pattern | Edge cases: country codes, mobile URLs |

**Key insight:** The existing `linkedin_finder_unified.py` already has working code for DDG search and URL extraction. Reuse patterns, don't rebuild.

## Common Pitfalls

### Pitfall 1: DuckDuckGo Rate Limiting
**What goes wrong:** 202 Ratelimit errors after ~30-60 requests
**Why it happens:** DDG detects automated traffic patterns
**How to avoid:**
- Use 2-3 second delays between requests (existing rate_limiter.py has 2s base delay for DDG)
- Rotate user agents (already in rate_limiter.py)
- Use proxy rotation for high volume (optional)
**Warning signs:** 202 status codes, empty results

### Pitfall 2: LinkedIn URL False Positives
**What goes wrong:** Matching company pages, job pages, feed URLs
**Why it happens:** All contain "linkedin.com" but aren't profiles
**How to avoid:**
```python
# Filter patterns
INVALID_LINKEDIN_PATHS = {'share', 'company', 'jobs', 'feed', 'in', 'posts', 'pulse'}

def validate_profile_url(url: str) -> bool:
    """Validate URL is a real profile, not company/job/feed page."""
    match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', url)
    if not match:
        return False
    username = match.group(1).lower()
    return username not in INVALID_LINKEDIN_PATHS and len(username) > 2
```
**Warning signs:** URLs ending in `/company/`, `/jobs/`, or usernames like "share"

### Pitfall 3: Inconsistent Snippet Title Format
**What goes wrong:** Name/title extraction fails or extracts wrong data
**Why it happens:** LinkedIn profile titles have no standard format:
- "John Smith - CEO - Company | LinkedIn"
- "John Smith | Company | LinkedIn"
- "Dr. John Smith, MBA - Transforming Healthcare"
**How to avoid:**
- Mark snippet-extracted names as LOW confidence
- Use multiple parsing attempts
- Cross-validate with other data sources
**Warning signs:** Extracted "Transforming Healthcare" as job title

### Pitfall 4: Bing Anti-Bot Detection
**What goes wrong:** CAPTCHAs, empty results, IP blocks
**Why it happens:** Bing has sophisticated bot detection
**How to avoid:**
- Use realistic headers (from rate_limiter.py)
- Add referer: "https://www.bing.com/"
- Longer delays (3-5s between requests)
- Respect robots.txt rate hints
**Warning signs:** 403 responses, CAPTCHA pages

## Code Examples

Verified patterns from existing codebase and documentation:

### DuckDuckGo Search (from duckduckgo-search docs + existing code)
```python
# Source: linkedin_finder_unified.py + duckduckgo-search PyPI
from duckduckgo_search import DDGS
import re

LINKEDIN_PROFILE_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?',
    re.IGNORECASE
)

def search_duckduckgo_linkedin(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo for LinkedIn profiles.

    Returns list of {href, title, body} dicts.
    """
    try:
        results = DDGS().text(
            query,
            max_results=max_results,
            backend="html"  # Use HTML backend for reliability
        )
        return [r for r in results if 'linkedin.com/in/' in r.get('href', '')]
    except Exception as e:
        print(f"DDG error: {e}")
        return []
```

### Bing HTML Scraping Fallback
```python
# Source: WebSearch research + existing patterns
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

async def search_bing_linkedin(query: str, headers: dict) -> list[dict]:
    """
    Fallback Bing search for LinkedIn profiles.

    Scrapes HTML since Bing API requires key.
    """
    search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count=10"

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        response = await client.get(search_url, headers=headers)

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Bing results in <li class="b_algo">
        for item in soup.select('li.b_algo'):
            link = item.select_one('h2 a')
            if link:
                href = link.get('href', '')
                if 'linkedin.com/in/' in href:
                    results.append({
                        'href': href,
                        'title': link.get_text(strip=True),
                        'body': item.get_text(strip=True)
                    })

        return results
```

### LinkedIn URL Pattern Validation
```python
# Source: linkedin_finder_unified.py (existing, verified)
import re

# Full LinkedIn profile URL pattern (handles country codes, mobile)
LINKEDIN_PROFILE_PATTERN = re.compile(
    r'https?://(?:[a-z]{2}\.)?(?:www\.)?(?:m\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?',
    re.IGNORECASE
)

# Invalid usernames to filter
INVALID_USERNAMES = {'share', 'company', 'jobs', 'feed', 'in', 'posts', 'pulse', 'login'}

def extract_linkedin_url(text: str) -> str | None:
    """
    Extract and validate LinkedIn profile URL from text.

    Returns normalized URL or None.
    """
    match = LINKEDIN_PROFILE_PATTERN.search(text)
    if not match:
        return None

    username = match.group(1).lower()
    if username in INVALID_USERNAMES or len(username) < 3:
        return None

    return f"https://linkedin.com/in/{match.group(1)}"
```

### Async Batch Processing Pattern
```python
# Source: async_verifier.py pattern (existing, verified)
import asyncio
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class LinkedInResult:
    """Result of LinkedIn discovery."""
    linkedin_url: Optional[str] = None
    owner_name: Optional[str] = None
    owner_title: Optional[str] = None
    source: Optional[str] = None  # 'duckduckgo' or 'bing'
    confidence: str = "low"  # Snippet-extracted = low

async def find_linkedin_batch(
    leads: list[dict],
    max_concurrent: int = 5,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> list[dict]:
    """
    Find LinkedIn for batch of leads with controlled concurrency.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(lead: dict) -> dict:
        async with semaphore:
            result = await find_linkedin_single(lead)
            lead['linkedin_url'] = result.linkedin_url
            lead['owner_name'] = result.owner_name or lead.get('owner_name')
            lead['linkedin_source'] = result.source
            return lead

    tasks = [process_one(lead) for lead in leads]

    # Track progress
    completed = 0
    results = []
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        completed += 1
        if progress_callback:
            progress_callback(completed, len(leads))

    return results
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| duckduckgo-search | ddgs (new package) | 2025 | Renamed, same author, more backends |
| Requests + BeautifulSoup | duckduckgo-search library | 2024 | Handles parsing internally |
| Single backend | Multi-backend (html, lite, bing) | 2025 | Better reliability |
| Static delays | Adaptive rate limiting | 2024 | Fewer blocks, faster when safe |

**Deprecated/outdated:**
- `ddgr` CLI tool: Still works but Python library is better
- Google Custom Search: Expensive and quota-limited
- Direct LinkedIn scraping: Gets blocked immediately, ToS violation

## Open Questions

Things that couldn't be fully resolved:

1. **Exact DDG rate limit thresholds**
   - What we know: ~30-60 requests before 202 errors reported
   - What's unclear: Exact per-minute/per-hour limits, varies by IP
   - Recommendation: Use 2-3s delays, back off exponentially on 202

2. **Bing reliability at scale**
   - What we know: Works but bot detection is aggressive
   - What's unclear: Long-term sustainability as fallback
   - Recommendation: Implement as fallback, monitor success rate

3. **Name/title extraction accuracy**
   - What we know: Varies widely due to inconsistent formats
   - What's unclear: What percentage extracts correctly
   - Recommendation: Mark as LOW confidence, validate downstream

## Sources

### Primary (HIGH confidence)
- [duckduckgo-search PyPI](https://pypi.org/project/duckduckgo-search/) - Version 8.1.1, API reference
- Existing codebase: `linkedin_finder_unified.py` - Working implementation
- Existing codebase: `find_linkedin_smart_async.py` - Async pattern

### Secondary (MEDIUM confidence)
- [GitHub deedy5/ddgs](https://github.com/deedy5/ddgs) - Newer package, multi-backend
- [LinkedIn URL help](https://www.linkedin.com/help/linkedin/answer/a522735) - URL format
- [WebScraping.AI Bing guide](https://webscraping.ai/faq/bing-scraping/how-can-i-scrape-bing-search-results-without-an-api-key) - Bing scraping patterns
- [GitHub issues](https://github.com/open-webui/open-webui/discussions/6624) - Rate limit reports

### Tertiary (LOW confidence)
- Blog posts on LinkedIn scraping via search engines
- Community reports on DDG rate limits (varies by user)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Library verified on PyPI, existing code works
- Architecture: HIGH - Follows existing codebase patterns exactly
- Pitfalls: MEDIUM - Based on community reports + existing code comments

**Research date:** 2026-01-20
**Valid until:** 30 days (stable domain, libraries actively maintained)
