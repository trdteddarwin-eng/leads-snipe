# Phase 2 Plan: Sitemap Sniper

**Phase:** 2 of 7
**Goal:** Discover and scrape contact/team pages from XML sitemaps
**Output:** `execution/sitemap_sniper.py`

## Requirements Coverage

| Requirement | Task | Status |
|-------------|------|--------|
| SITEMAP-01: Sitemap URL discovery | Task 2.1 | Complete |
| SITEMAP-02: Recursive sitemap parsing | Task 2.2 | Complete |
| SITEMAP-03: Contact page identification | Task 2.3 | Complete |
| SITEMAP-04: Email extraction from pages | Task 2.4 | Complete |
| SITEMAP-05: Staff name extraction | Task 2.5 | Complete |

## Implementation Plan

### Wave 1: Discovery & Parsing

#### Task 2.1: Sitemap Discovery
**File:** `execution/sitemap_sniper.py`
**Requirement:** SITEMAP-01

Create `SitemapDiscovery` class:

```python
class SitemapDiscovery:
    async def discover(self, domain: str) -> list[str]
```

**Implementation:**
1. Check robots.txt for `Sitemap:` directives
2. Try common paths: `/sitemap.xml`, `/sitemap_index.xml`, `/wp-sitemap.xml`
3. Check homepage for `<link rel="sitemap">` tag
4. Handle compressed `.gz` sitemaps
5. Return list of discovered sitemap URLs

**Acceptance:**
- [ ] Finds sitemap from robots.txt when present
- [ ] Falls back to common paths when no robots.txt
- [ ] Handles compressed sitemaps
- [ ] Returns empty list on failure (no exceptions)

---

#### Task 2.2: Recursive Sitemap Parsing
**File:** `execution/sitemap_sniper.py`
**Requirement:** SITEMAP-02

Add `SitemapParser` class:

```python
class SitemapParser:
    async def parse(self, sitemap_url: str, max_depth: int = 3) -> list[str]
```

**Implementation:**
1. Fetch sitemap XML with httpx
2. Parse with lxml, handle namespace
3. Detect sitemap index (`<sitemapindex>`) vs regular (`<urlset>`)
4. Recursively parse referenced sitemaps (depth limit: 3)
5. Collect all `<loc>` URLs
6. Handle malformed XML gracefully

**Acceptance:**
- [ ] Parses simple sitemaps correctly
- [ ] Recursively handles sitemap indexes
- [ ] Respects max depth limit
- [ ] Returns partial results on errors

---

### Wave 2: Page Classification & Extraction

#### Task 2.3: Contact Page Identification
**File:** `execution/sitemap_sniper.py`
**Requirement:** SITEMAP-03

Add URL classification:

```python
def classify_urls(urls: list[str]) -> dict[str, list[str]]
```

**Implementation:**
1. Define regex patterns for contact pages (`/contact`, `/reach-us`, etc.)
2. Define regex patterns for team pages (`/team`, `/about`, `/leadership`)
3. Classify each URL by path matching
4. Return dict with `contact`, `team`, `other` categories
5. Prioritize more specific matches

**Acceptance:**
- [ ] Correctly identifies `/contact*` as contact pages
- [ ] Correctly identifies `/team*`, `/about*` as team pages
- [ ] Handles edge cases (trailing slashes, query params)

---

#### Task 2.4: Email Extraction
**File:** `execution/sitemap_sniper.py`
**Requirement:** SITEMAP-04

Add email extraction:

```python
async def extract_emails(url: str) -> list[str]
```

**Implementation:**
1. Fetch page HTML with httpx
2. Decode common email obfuscation (`[at]`, `(dot)`, etc.)
3. Extract via regex pattern
4. Extract from `mailto:` links
5. Filter false positives (image files, example.com, etc.)
6. Deduplicate results

**Acceptance:**
- [ ] Extracts plain text emails
- [ ] Extracts from mailto: links
- [ ] Handles obfuscated emails
- [ ] Filters common false positives

---

#### Task 2.5: Staff Name Extraction
**File:** `execution/sitemap_sniper.py`
**Requirement:** SITEMAP-05

Add staff extraction:

```python
async def extract_staff(url: str) -> list[dict]
```

**Implementation:**
1. Fetch page HTML
2. Look for team/staff card patterns in HTML
3. Extract names from headings (h2-h4, strong)
4. Extract titles from title/role/position classes
5. Parse JSON-LD Schema.org `Person` data
6. Return list of `{name, title, email?}` dicts

**Acceptance:**
- [ ] Extracts names from common card layouts
- [ ] Extracts job titles when present
- [ ] Parses structured data (JSON-LD)
- [ ] Returns empty list when no staff found

---

### Wave 3: Integration

#### Task 2.6: Public API & CLI
**File:** `execution/sitemap_sniper.py`

Create unified API:

```python
@dataclass
class SitemapResult:
    domain: str
    sitemap_url: Optional[str]
    contact_pages: list[str]
    team_pages: list[str]
    emails: list[str]
    staff: list[dict]

async def snipe_sitemap(domain: str) -> SitemapResult
def snipe_sitemap_sync(domain: str) -> SitemapResult
```

**Implementation:**
1. Discover sitemap
2. Parse all URLs
3. Classify into contact/team pages
4. Scrape contact pages for emails
5. Scrape team pages for staff names
6. Return aggregated results
7. Add CLI interface for testing

**Acceptance:**
- [ ] Single function call returns all data
- [ ] Sync wrapper for non-async callers
- [ ] CLI works: `python sitemap_sniper.py example.com`

---

#### Task 2.7: Unit Tests
**File:** `execution/test_sitemap_sniper.py`

**Test Cases:**
1. `test_discover_from_robots` - Finds sitemap in robots.txt
2. `test_discover_fallback` - Uses common paths when no robots.txt
3. `test_parse_simple_sitemap` - Parses urlset correctly
4. `test_parse_sitemap_index` - Recursively parses index
5. `test_classify_contact` - Identifies contact pages
6. `test_classify_team` - Identifies team pages
7. `test_extract_emails` - Extracts various email formats
8. `test_extract_mailto` - Extracts from mailto links
9. `test_extract_staff` - Extracts staff from cards
10. `test_extract_jsonld` - Parses Schema.org Person

**Implementation:**
- Mock HTTP responses for unit tests
- Use pytest-asyncio for async tests

---

## Execution Order

```
Wave 1 (Sequential):
  Task 2.1 → Task 2.2

Wave 2 (Parallel, after Wave 1):
  Task 2.3 | Task 2.4 | Task 2.5

Wave 3 (Sequential, after Wave 2):
  Task 2.6 → Task 2.7
```

## Success Criteria Verification

| Criterion | How to Verify |
|-----------|---------------|
| Finds 70%+ sitemaps | Test against domains with known sitemaps |
| Identifies contact pages | URL classification accuracy test |
| Extracts emails | Test against pages with known emails |
| Extracts staff names | Test against team pages |

## Dependencies

```
httpx>=0.27.0 (existing)
lxml>=5.0.0 (add)
beautifulsoup4>=4.12.0 (add)
```

## Risks & Mitigations

| Risk | Mitigation | Task |
|------|------------|------|
| No sitemap exists | Fall back to `/contact` path directly | 2.1 |
| Rate limiting | 1-2s delay between requests | 2.4, 2.5 |
| Malformed XML | Try-except with partial results | 2.2 |
| JS-rendered pages | Skip, focus on static HTML | 2.4, 2.5 |

---
*Plan created: 2026-01-18*
