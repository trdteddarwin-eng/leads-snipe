# Stack Research: Stealth Lead Enrichment

## Async Email Verification

### aiosmtplib (Recommended)
- **Version:** 3.0.1+
- **Purpose:** Async SMTP client for email verification
- **Why:** Only mature async SMTP library for Python, well-maintained
- **Confidence:** High

```python
import aiosmtplib
async def check_smtp(email, domain):
    try:
        smtp = aiosmtplib.SMTP(hostname=mx_host, timeout=10)
        await smtp.connect()
        await smtp.helo()
        await smtp.mail("verify@yourdomain.com")
        code, _ = await smtp.rcpt(email)
        return code == 250
    except:
        return None
```

### aiodns (Recommended)
- **Version:** 3.2.0+
- **Purpose:** Async DNS resolver for MX lookups
- **Why:** Built on c-ares, fastest async DNS for Python
- **Confidence:** High

```python
import aiodns
resolver = aiodns.DNSResolver()
mx_records = await resolver.query(domain, 'MX')
```

### Alternative: dnspython with asyncio
- **Version:** 2.6.0+
- dnspython now has native asyncio support via `dns.asyncresolver`
- Slightly slower than aiodns but more features

## Sitemap Parsing

### ultimate-sitemap-parser (Recommended)
- **Version:** 0.5+
- **Purpose:** Parse XML sitemaps recursively
- **Why:** Handles sitemap indexes, gzip, robots.txt discovery
- **Confidence:** Medium (may need httpx for async fetching)

### Alternative: Manual with lxml
- Use `lxml.etree` for XML parsing
- Fetch with `httpx.AsyncClient`
- More control, less abstraction

```python
import httpx
from lxml import etree

async def parse_sitemap(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        tree = etree.fromstring(resp.content)
        return [loc.text for loc in tree.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
```

## HTTP Client

### httpx (Recommended)
- **Version:** 0.27.0+
- **Purpose:** Async HTTP client
- **Why:** Already in requirements.txt, supports HTTP/2, connection pooling
- **Confidence:** High

### aiohttp
- **Version:** 3.9.0+
- Alternative if httpx issues arise
- Slightly more memory efficient for high concurrency

## Search Engine Scraping

### duckduckgo-search (Recommended)
- **Version:** 6.0.0+
- **Purpose:** DuckDuckGo results without API key
- **Why:** No rate limits, no API key needed
- **Confidence:** Medium (may break with DDG changes)

```python
from duckduckgo_search import DDGS
results = DDGS().text(f"site:linkedin.com {name} {company}", max_results=5)
```

### Alternative: SerpAPI (Paid fallback)
- Already in stack, use for fallback only

## SSL/WHOIS

### ssl (stdlib)
- Built-in Python SSL for certificate inspection
- Extract organization from cert subject

### python-whois
- **Version:** 0.9.0+
- WHOIS lookups (often privacy-protected, low success rate)
- **Confidence:** Low (registrant data usually hidden)

## Email Pattern Generation

### No library needed
- Implement pattern generation directly:
  - `{first}@domain.com`
  - `{first}.{last}@domain.com`
  - `{f}{last}@domain.com`
  - `{first}{l}@domain.com`
  - `owner@domain.com`
  - `info@domain.com`
  - `contact@domain.com`

## Gravatar

### libgravatar or manual
- MD5 hash of lowercase email
- Check `https://gravatar.com/avatar/{hash}?d=404`
- 404 = no gravatar = less confidence

## What NOT to Use

- **smtplib (sync)** — Blocks event loop, defeats async purpose
- **dnspython without async** — Same blocking issue
- **requests** — Use httpx for async
- **LinkedIn API** — Requires OAuth, rate limited, ToS issues
- **Hunter.io/Clearbit** — Paid APIs, defeats $0 goal

---
*Research: 2026-01-18*
