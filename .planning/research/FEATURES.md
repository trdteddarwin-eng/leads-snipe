# Features Research: Stealth Lead Enrichment

## Email Discovery Methods

### Table Stakes (Must Have for 80%+)

**1. Async SMTP Verification**
- Complexity: Medium
- Success Rate: 60-70% (many servers don't respond accurately)
- How: Connect to MX server, RCPT TO check
- Dependencies: aiodns for MX lookup, aiosmtplib for SMTP

**2. Email Pattern Guessing + Verification**
- Complexity: Low
- Success Rate: 40-60% (depends on company size)
- How: Generate patterns, async verify each, keep first valid
- Common patterns:
  - `firstname@` (30% of businesses)
  - `firstname.lastname@` (25%)
  - `firstlast@` (15%)
  - `first.l@` (10%)
  - `owner@`, `info@` (generic fallback)

**3. Contact Page Scraping**
- Complexity: Medium
- Success Rate: 30-50% (many don't list emails)
- How: Find /contact, /about, /team pages, extract emails
- Dependencies: Sitemap parsing or crawling

**4. DNS MX Validation**
- Complexity: Low
- Success Rate: 99% (just validates domain has email)
- How: Check MX records exist
- Purpose: Filter out domains without email servers

### Differentiators (Competitive Advantage)

**5. Sitemap-First Discovery**
- Complexity: Medium
- Success Rate: +10-15% over blind crawling
- How: Parse sitemap.xml, find contact/team URLs directly
- Advantage: Faster, more targeted than full crawl

**6. SSL Certificate Org Extraction**
- Complexity: Low
- Success Rate: 20-30% have org in cert
- How: Inspect SSL cert subject for organization name
- Use: Confirm business name, find decision maker context

**7. Search Snippet LinkedIn Discovery**
- Complexity: Medium
- Success Rate: 40-60% (name must be unique enough)
- How: Search "site:linkedin.com {name} {company}", parse snippet
- Advantage: No LinkedIn rate limits, no account needed

**8. Catch-All Detection**
- Complexity: Medium
- Success Rate: N/A (validation, not discovery)
- How: Test random email, if accepts = catch-all domain
- Purpose: Avoid false positives on catch-all servers

**9. Gravatar Verification**
- Complexity: Low
- Success Rate: 15-20% have gravatars
- How: Check gravatar.com for email hash
- Purpose: Additional confidence signal

### Anti-Features (Do NOT Build)

**LinkedIn Direct Scraping**
- Why Not: Rate limits, bot detection, ToS violation, account bans
- Alternative: Search engine snippets

**Paid API as Primary**
- Why Not: Defeats $0 goal
- Alternative: Paid as fallback only

**Browser Automation for Search**
- Why Not: Slow, resource-heavy, detectable
- Alternative: Direct HTTP with duckduckgo-search library

**Email Guessing Without Verification**
- Why Not: Destroys sender reputation
- Alternative: Always verify before storing

## Discovery Pipeline Order

Optimal order for maximum success with minimum cost:

1. **DNS MX Check** — Filter out invalid domains (free, instant)
2. **Sitemap Sniper** — Find contact pages directly (free, fast)
3. **Contact Page Scrape** — Extract listed emails (free)
4. **SSL Org Extraction** — Get business context (free)
5. **Pattern Guessing** — Generate candidates (free)
6. **Async SMTP Verify** — Validate all candidates (free)
7. **LinkedIn Snippet** — Find decision maker name (free)
8. **Gravatar Check** — Confidence signal (free)
9. **Paid API Fallback** — Anymailfinder/Apollo if all else fails

## Expected Success Rates

| Method | Success Rate | Cost |
|--------|--------------|------|
| Current (Anymailfinder primary) | 24% | $0.05/lead |
| Stealth Hybrid (free first) | 70-85% | $0.00* |
| With paid fallback | 85-90% | $0.01/lead |

*Assuming typical small business lead mix

---
*Research: 2026-01-18*
