# Phase 2 Verification: Sitemap Sniper

**Status:** passed
**Verified:** 2026-01-18

## Goal

Discover and scrape contact/team pages from XML sitemaps

## Must-Haves Checklist

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Sitemap URL discovery | ✓ | `SitemapDiscovery` with 3 methods |
| Recursive sitemap parsing | ✓ | `SitemapParser` with depth limit |
| Contact page identification | ✓ | `URLClassifier` with regex patterns |
| Email extraction from pages | ✓ | `EmailExtractor` with obfuscation |
| Staff name extraction | ✓ | `StaffExtractor` with JSON-LD + HTML |

## Code Verification

### 1. Sitemap Discovery (SITEMAP-01)

```python
# Line 59-64 - Three discovery methods
async def discover(self, domain: str) -> List[str]:
    # Method 1: Check robots.txt
    robots_sitemaps = await self._from_robots(client, base_url)
    # Method 2: Try common paths if robots.txt didn't work
    common_sitemaps = await self._from_common_paths(client, base_url)
    # Method 3: Check homepage for link tag
    link_sitemaps = await self._from_html_link(client, base_url)
```

**Verified:** Three-tier discovery with fallbacks.

### 2. Recursive Sitemap Parsing (SITEMAP-02)

```python
# Line 130-135 - Recursive parsing
async def parse(self, sitemap_url: str, depth: int = 0) -> List[str]:
    if depth >= self.max_depth:
        return []
    # Check if this is a sitemap index
    sitemap_refs = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=self.SITEMAP_NS)
    if sitemap_refs:
        for ref in sitemap_refs:
            child_urls = await self.parse(ref.strip(), depth + 1)
```

**Verified:** Handles sitemapindex with depth limit (3 levels).

### 3. Contact Page Identification (SITEMAP-03)

```python
# Line 200-212 - URL patterns
CONTACT_PATTERNS = [r"/contact(?:-us)?/?$", r"/reach-us/?$", r"/get-in-touch/?$", ...]
TEAM_PATTERNS = [r"/team/?$", r"/our-team/?$", r"/about/?$", r"/leadership/?$", ...]

def classify(self, urls: List[str]) -> Dict[str, List[str]]:
    # Returns {"contact": [...], "team": [...], "other": [...]}
```

**Verified:** Regex-based classification with multiple patterns.

### 4. Email Extraction (SITEMAP-04)

```python
# Line 269-280 - Multi-method extraction
async def extract(self, url: str) -> List[str]:
    html = self._decode_obfuscation(html)  # [at] → @
    text_emails = self.EMAIL_PATTERN.findall(html)  # Regex
    mailto_emails = self._extract_mailto(html)  # mailto: links
    filtered = self._filter_emails(all_emails)  # Remove false positives
```

**Verified:** Regex + mailto + obfuscation decoding + filtering.

### 5. Staff Name Extraction (SITEMAP-05)

```python
# Line 340-350 - Two extraction methods
async def extract(self, url: str) -> List[StaffMember]:
    # Method 1: Schema.org JSON-LD
    jsonld_staff = self._extract_jsonld(html)
    # Method 2: HTML card patterns
    card_staff = self._extract_from_cards(html)
```

**Verified:** JSON-LD structured data + HTML card parsing.

## Test Coverage

| Test | Covers |
|------|--------|
| test_discover_from_robots | SITEMAP-01 |
| test_discover_fallback_paths | SITEMAP-01 |
| test_parse_simple_sitemap | SITEMAP-02 |
| test_parse_sitemap_index | SITEMAP-02 |
| test_classify_contact_pages | SITEMAP-03 |
| test_classify_team_pages | SITEMAP-03 |
| test_extract_plain_emails | SITEMAP-04 |
| test_extract_mailto_emails | SITEMAP-04 |
| test_extract_obfuscated_emails | SITEMAP-04 |
| test_extract_from_cards | SITEMAP-05 |
| test_extract_jsonld | SITEMAP-05 |

## Score

**5/5 must-haves verified**

## Gaps Found

None.

## Human Verification

Not required - all criteria are code-verifiable.

---
*Verification completed: 2026-01-18*
