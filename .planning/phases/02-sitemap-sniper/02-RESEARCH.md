# Phase 2 Research: Sitemap Sniper

## Objective

Discover and scrape contact/team pages from XML sitemaps to extract emails and staff names.

## Sitemap Discovery Strategies

### 1. robots.txt Method (Most Reliable)

```python
async def get_sitemap_from_robots(domain: str) -> list[str]:
    """Parse robots.txt for Sitemap: directives."""
    url = f"https://{domain}/robots.txt"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        sitemaps = []
        for line in response.text.split("\n"):
            if line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())
        return sitemaps
```

### 2. Common Path Fallback

Try these paths in order:
1. `/sitemap.xml`
2. `/sitemap_index.xml`
3. `/sitemap/sitemap.xml`
4. `/sitemaps/sitemap.xml`
5. `/wp-sitemap.xml` (WordPress)
6. `/sitemap.xml.gz` (compressed)

### 3. HTML Link Discovery

Some sites include sitemap in `<link>` tags:
```html
<link rel="sitemap" type="application/xml" href="/sitemap.xml">
```

## Sitemap XML Parsing

### Structure Types

**Simple sitemap:**
```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2025-01-15</lastmod>
  </url>
</urlset>
```

**Sitemap index (references other sitemaps):**
```xml
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>https://example.com/sitemap-pages.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://example.com/sitemap-posts.xml</loc>
  </sitemap>
</sitemapindex>
```

### Recursive Parsing Pattern

```python
from lxml import etree

async def parse_sitemap(url: str, depth: int = 0, max_depth: int = 3) -> list[str]:
    """Parse sitemap recursively, handling both urlset and sitemapindex."""
    if depth >= max_depth:
        return []

    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=15)
        root = etree.fromstring(response.content)

    # Handle namespace
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = []

    # Check if sitemap index
    sitemap_refs = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=ns)
    if sitemap_refs:
        for ref in sitemap_refs:
            urls.extend(await parse_sitemap(ref, depth + 1, max_depth))
    else:
        # Regular sitemap
        urls = root.xpath("//sm:url/sm:loc/text()", namespaces=ns)

    return urls
```

## Contact Page Identification

### URL Pattern Matching

High-confidence patterns:
- `/contact`
- `/contact-us`
- `/about/contact`
- `/reach-us`
- `/get-in-touch`

Medium-confidence patterns:
- `/about`
- `/about-us`
- `/team`
- `/our-team`
- `/leadership`
- `/staff`
- `/people`
- `/company`

```python
CONTACT_PATTERNS = [
    r"/contact(?:-us)?/?$",
    r"/reach-us/?$",
    r"/get-in-touch/?$",
]

TEAM_PATTERNS = [
    r"/team/?$",
    r"/our-team/?$",
    r"/leadership/?$",
    r"/staff/?$",
    r"/people/?$",
    r"/about/?$",
    r"/about-us/?$",
]

def classify_url(url: str) -> str:
    """Classify URL as contact, team, or other."""
    path = urlparse(url).path.lower()
    for pattern in CONTACT_PATTERNS:
        if re.search(pattern, path):
            return "contact"
    for pattern in TEAM_PATTERNS:
        if re.search(pattern, path):
            return "team"
    return "other"
```

## Email Extraction

### Regex Pattern

```python
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE
)

def extract_emails(html: str) -> list[str]:
    """Extract email addresses from HTML content."""
    # Decode common obfuscation
    html = html.replace(" [at] ", "@").replace("[at]", "@")
    html = html.replace(" [dot] ", ".").replace("[dot]", ".")
    html = html.replace(" (at) ", "@").replace("(at)", "@")

    emails = EMAIL_PATTERN.findall(html)

    # Filter out common false positives
    filtered = [
        e for e in emails
        if not e.endswith(('.png', '.jpg', '.gif', '.css', '.js'))
        and '@example.com' not in e
        and '@sentry' not in e.lower()
    ]

    return list(set(filtered))
```

### mailto: Link Extraction

```python
from bs4 import BeautifulSoup

def extract_mailto_emails(html: str) -> list[str]:
    """Extract emails from mailto: links."""
    soup = BeautifulSoup(html, "html.parser")
    emails = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0]
            emails.append(email)
    return emails
```

## Staff Name Extraction

### Team Page Patterns

```python
def extract_staff_names(html: str) -> list[dict]:
    """Extract staff names and titles from team pages."""
    soup = BeautifulSoup(html, "html.parser")
    staff = []

    # Common patterns:
    # 1. Card layouts with name in heading
    for card in soup.find_all(class_=re.compile(r"team|staff|member|person")):
        name = None
        title = None

        # Name usually in h2-h4 or strong
        name_elem = card.find(["h2", "h3", "h4", "strong"])
        if name_elem:
            name = name_elem.get_text(strip=True)

        # Title in p or span with class containing "title", "role", "position"
        title_elem = card.find(class_=re.compile(r"title|role|position|job"))
        if title_elem:
            title = title_elem.get_text(strip=True)

        if name:
            staff.append({"name": name, "title": title})

    return staff
```

### Schema.org Structured Data

```python
import json

def extract_schema_org_people(html: str) -> list[dict]:
    """Extract Person data from JSON-LD structured data."""
    soup = BeautifulSoup(html, "html.parser")
    people = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Person":
                        people.append({
                            "name": item.get("name"),
                            "title": item.get("jobTitle"),
                            "email": item.get("email")
                        })
            elif data.get("@type") == "Person":
                people.append({
                    "name": data.get("name"),
                    "title": data.get("jobTitle"),
                    "email": data.get("email")
                })
        except json.JSONDecodeError:
            continue

    return people
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   SitemapSniper                          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   Discover   │    │    Parse     │    │  Scrape   │ │
│  │   Sitemap    │───▶│   XML/Index  │───▶│   Pages   │ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
│          │                   │                  │       │
│          ▼                   ▼                  ▼       │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   robots.txt │    │  Recursive   │    │  Extract  │ │
│  │   + fallback │    │   parsing    │    │  Emails   │ │
│  └──────────────┘    └──────────────┘    │  + Names  │ │
│                                          └───────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Dependencies

Already in stack:
- `httpx` — async HTTP client
- `lxml` — fast XML parsing (add if missing)
- `beautifulsoup4` — HTML parsing (add if missing)

## Risk Mitigations

| Risk | Mitigation |
|------|------------|
| No sitemap exists | Fallback to common contact page paths |
| Rate limiting | 1-2s delay between requests to same domain |
| Malformed XML | Try-except with fallback to string parsing |
| Compressed sitemaps | Handle .gz with gzip module |
| Dynamic pages | Stick to static content, avoid JS-heavy |

## Success Metrics

| Metric | Target |
|--------|--------|
| Sitemap discovery | 70% of domains with sitemaps |
| Contact page identification | 80% accuracy |
| Email extraction | Extract from 50% of contact pages |
| Staff name extraction | Extract from 40% of team pages |

---
*Research completed: 2026-01-18*
