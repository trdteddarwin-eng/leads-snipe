# Phase 4 Plan: LinkedIn Stealth

**Phase:** 4 of 7
**Goal:** Find LinkedIn profiles via search engine snippets without hitting LinkedIn directly
**Output:** `execution/linkedin_stealth.py`

## Requirements Coverage

| Requirement | Task | Status |
|-------------|------|--------|
| LINKEDIN-01: DuckDuckGo LinkedIn search | Task 4.1 | Pending |
| LINKEDIN-02: LinkedIn URL extraction | Task 4.1 | Pending |
| LINKEDIN-03: Name/title extraction from snippet | Task 4.2 | Pending |
| LINKEDIN-04: Bing fallback | Task 4.3 | Pending |

## Implementation Plan

### Wave 1: Core Search & Extraction

#### Task 4.1: DuckDuckGo LinkedIn Search
**File:** `execution/linkedin_stealth.py`
**Requirements:** LINKEDIN-01, LINKEDIN-02

Create async DuckDuckGo search with LinkedIn URL extraction:

```python
from duckduckgo_search import DDGS
import re
from dataclasses import dataclass
from typing import Optional
import asyncio

# LinkedIn profile URL pattern (handles country codes, mobile)
LINKEDIN_PROFILE_PATTERN = re.compile(
    r'https?://(?:[a-z]{2}\.)?(?:www\.)?(?:m\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?',
    re.IGNORECASE
)

# Invalid usernames to filter (avoid false positives)
INVALID_USERNAMES = {'share', 'company', 'jobs', 'feed', 'in', 'posts', 'pulse', 'login'}

@dataclass
class LinkedInResult:
    linkedin_url: Optional[str] = None
    owner_name: Optional[str] = None
    owner_title: Optional[str] = None
    source: Optional[str] = None  # 'duckduckgo' or 'bing'
    confidence: str = "low"  # snippet-extracted = low

async def search_duckduckgo(name: str, company: str) -> Optional[dict]:
    """Search DDG for LinkedIn profile."""
```

**Implementation:**
1. Build site-restricted query: `site:linkedin.com/in "{name}" "{company}"`
2. Use DDGS().text() with backend="html", max_results=5
3. Filter results to only linkedin.com/in/ URLs
4. Validate username against INVALID_USERNAMES
5. Return first valid result with href, title, body
6. Handle rate limits (202 errors) with exponential backoff
7. Use 2-3 second delays between requests (per research)
8. Run in executor for async compatibility (DDGS is sync)

**Acceptance:**
- [ ] Searches DDG with site-restricted query
- [ ] Extracts LinkedIn profile URLs from results
- [ ] Filters out /company/, /jobs/, /share/ URLs
- [ ] Handles 202 rate limit gracefully
- [ ] Returns None on failure (no exceptions)

---

#### Task 4.2: Snippet Name/Title Extraction
**File:** `execution/linkedin_stealth.py`
**Requirement:** LINKEDIN-03

Add snippet parsing for name and job title:

```python
def parse_linkedin_snippet(title: str, body: str) -> dict:
    """
    Extract name and title from LinkedIn search snippet.

    Title formats vary:
    - "John Smith - CEO - Company Inc | LinkedIn"
    - "John Smith | LinkedIn"
    - "John Smith - Software Engineer at Company"

    Returns: {"name": str|None, "title": str|None}
    """
```

**Implementation:**
1. Remove LinkedIn suffix (| LinkedIn, - LinkedIn)
2. Split by common delimiters (-, |)
3. First part = name (validate: 2+ words, reasonable length)
4. Second part = title (if present)
5. Mark confidence as "low" for all snippet-extracted data
6. Handle edge cases: Dr./Jr./III suffixes, commas in titles
7. Return None for fields that can't be reliably parsed

**Acceptance:**
- [ ] Extracts name from "Name - Title | LinkedIn" format
- [ ] Extracts title when present
- [ ] Handles varied delimiter formats
- [ ] Returns None when format is unparseable
- [ ] Never throws on malformed input

---

#### Task 4.3: Bing Fallback Search
**File:** `execution/linkedin_stealth.py`
**Requirement:** LINKEDIN-04

Add Bing HTML scraping as fallback:

```python
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

async def search_bing(name: str, company: str) -> Optional[dict]:
    """Fallback Bing search when DDG fails."""
```

**Implementation:**
1. Build query: `site:linkedin.com/in "{name}" "{company}"`
2. URL: `https://www.bing.com/search?q={query}&count=10`
3. Use realistic headers from rate_limiter.py pattern:
   - User-Agent rotation
   - Accept, Accept-Language headers
   - Referer: "https://www.bing.com/"
4. Parse HTML with BeautifulSoup
5. Extract results from `li.b_algo` > `h2 a` elements
6. Filter to linkedin.com/in/ URLs only
7. Use 3-5 second delays (Bing more aggressive)
8. Handle 403/CAPTCHA gracefully

**Acceptance:**
- [ ] Searches Bing with site-restricted query
- [ ] Uses realistic headers to avoid blocks
- [ ] Extracts LinkedIn URLs from search results
- [ ] Returns None on 403/CAPTCHA (no retry)
- [ ] Integrates with existing rate_limiter.py

---

### Wave 2: Integration & Testing

#### Task 4.4: Public API & Multi-Strategy Orchestration
**File:** `execution/linkedin_stealth.py`

Create unified API that tries DDG then Bing:

```python
async def find_linkedin(
    name: str,
    company: str,
    location: str = ""
) -> LinkedInResult:
    """
    Find LinkedIn profile via stealth search.

    Strategy:
    1. DuckDuckGo search (primary)
    2. Bing search (fallback if DDG fails/rate-limited)

    Never makes direct requests to linkedin.com.
    """

async def find_linkedin_batch(
    leads: list[dict],
    max_concurrent: int = 5,
    progress_callback: Optional[Callable] = None
) -> list[dict]:
    """Batch process with controlled concurrency."""

def find_linkedin_sync(name: str, company: str) -> LinkedInResult:
    """Sync wrapper for non-async callers."""
```

**Implementation:**
1. Try DDG first, return immediately on success
2. On DDG failure/rate-limit, try Bing
3. Combine URL + snippet parsing for full result
4. Batch processing with semaphore (max 5 concurrent - conservative)
5. Progress callback for UI integration
6. Sync wrapper using asyncio.run()
7. CLI interface: `python linkedin_stealth.py "John Smith" "Acme Corp"`

**Acceptance:**
- [ ] Single function returns LinkedInResult
- [ ] Falls back to Bing when DDG fails
- [ ] Batch processing respects concurrency limit
- [ ] CLI works for testing
- [ ] Never hits linkedin.com directly

---

#### Task 4.5: Unit Tests
**File:** `execution/test_linkedin_stealth.py`

**Test Cases:**
1. `test_search_duckduckgo_success` - Finds profile via DDG
2. `test_search_duckduckgo_rate_limit` - Handles 202 gracefully
3. `test_search_bing_fallback` - Bing works when DDG fails
4. `test_extract_linkedin_url` - Extracts valid profile URLs
5. `test_filter_invalid_urls` - Filters /company/, /jobs/ URLs
6. `test_parse_snippet_standard` - Parses "Name - Title | LinkedIn"
7. `test_parse_snippet_minimal` - Parses "Name | LinkedIn"
8. `test_parse_snippet_edge_cases` - Handles Dr., Jr., commas
9. `test_find_linkedin_multi_strategy` - DDG -> Bing fallback
10. `test_batch_concurrency` - Respects concurrent limit
11. `test_no_direct_linkedin_requests` - Verify no linkedin.com calls

**Implementation:**
- Mock DDGS for DDG tests
- Mock httpx for Bing tests
- Use pytest-asyncio for async tests
- Integration test with real (but rate-limited) requests optional

---

## Execution Order

```
Wave 1 (Sequential):
  Task 4.1 -> Task 4.2 -> Task 4.3

Wave 2 (Sequential, after Wave 1):
  Task 4.4 -> Task 4.5
```

## Success Criteria Verification

| Criterion | How to Verify |
|-----------|---------------|
| Finds 50%+ LinkedIn profiles | Test against 20 known searchable names |
| Never hits linkedin.com | Mock/monitor outgoing requests |
| Extracts name/title from snippets | Test against known snippet formats |
| Falls back to Bing | Force DDG failure, verify Bing triggers |

## Dependencies

```
duckduckgo-search>=8.1.1 (new)
httpx>=0.27.0 (existing)
beautifulsoup4>=4.12.0 (existing)
```

**Install:**
```bash
pip install duckduckgo-search
```

## Existing Code to Leverage

Reference patterns from `execution/linkedin_finder_unified.py`:
- `LINKEDIN_PROFILE_PATTERN` regex (line 32-35)
- `INVALID_USERNAMES` filtering logic (line 146)
- `_search_duckduckgo()` method pattern (line 179-230)
- Name extraction from title (line 218-223)

Key differences from existing code:
1. New module uses async (existing is sync with threads)
2. New module uses duckduckgo-search library (existing uses raw HTTP)
3. New module adds Bing fallback (existing uses Google)
4. New module focuses solely on LinkedIn (no HTML extraction strategy)

## Risks & Mitigations

| Risk | Mitigation | Task |
|------|------------|------|
| DDG rate limits | 2-3s delays, exponential backoff, Bing fallback | 4.1, 4.3 |
| Bing bot detection | Realistic headers, longer delays | 4.3 |
| Inconsistent snippet formats | Mark as low confidence, validate downstream | 4.2 |
| Library API changes | Pin duckduckgo-search version | 4.1 |

## Notes

This phase creates a NEW module (`linkedin_stealth.py`) rather than modifying the existing `linkedin_finder_unified.py` because:

1. **Different architecture:** New module is fully async, existing is sync with threads
2. **Different strategy focus:** New module is stealth-only (search engines), existing includes HTML extraction
3. **Eventual replacement:** Phase 6 will integrate linkedin_stealth.py and deprecate parts of linkedin_finder_unified.py

The snippet parsing confidence is intentionally LOW per research findings - title formats vary too much to trust extracted names/titles without cross-validation.

---
*Plan created: 2026-01-20*
