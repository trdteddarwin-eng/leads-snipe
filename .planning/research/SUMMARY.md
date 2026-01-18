# Research Summary: Stealth Hybrid Lead Engine

## Key Findings

### Stack Recommendations
- **Async SMTP:** aiosmtplib 3.0.1+ (only mature option)
- **Async DNS:** aiodns 3.2.0+ (fastest, c-ares based)
- **HTTP Client:** httpx 0.27.0+ (already in stack)
- **Search:** duckduckgo-search 6.0.0+ (no API key needed)
- **Sitemap:** lxml + httpx (manual parsing for control)

### Table Stakes for 80%+ Discovery
1. Async SMTP verification with catch-all detection
2. Email pattern guessing (8-10 patterns, ordered by probability)
3. Contact page scraping via sitemap discovery
4. DNS MX validation as first filter

### Differentiators
- Sitemap-first discovery (+10-15% vs blind crawl)
- Search snippet LinkedIn extraction (no LinkedIn rate limits)
- SSL cert org extraction (business context)
- Gravatar confidence signal

### Expected Success Rates
| Method | Rate | Cost |
|--------|------|------|
| Current (paid primary) | 24% | $0.05/lead |
| Stealth Hybrid | 70-85% | $0.00 |
| With paid fallback | 85-90% | ~$0.01/lead |

### Critical Pitfalls to Avoid
1. **IP Blacklisting** — Rate limit SMTP to 10/min, use valid HELO
2. **Catch-All False Positives** — Test random email first
3. **Event Loop Conflicts** — Use asyncio.run() from sync context only
4. **Fallback Too Early** — Exhaust ALL free methods first

### Build Order
1. Async Foundation (aiodns/aiosmtplib)
2. Sitemap Sniper
3. Metadata Recon
4. LinkedIn Stealth
5. Pattern Guerrilla
6. Pipeline Integration
7. Testing (25-lead verification)

## Files
- `STACK.md` — Library recommendations
- `FEATURES.md` — Discovery methods analysis
- `ARCHITECTURE.md` — Component design
- `PITFALLS.md` — Failure modes and prevention

---
*Research completed: 2026-01-18*
