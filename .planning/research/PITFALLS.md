# Pitfalls Research: Stealth Lead Enrichment

## Async/Sync Integration

### Pitfall: Event Loop Conflicts
- **Warning Signs:** "Event loop is already running" errors, hangs
- **Cause:** Mixing asyncio.run() with existing event loops (FastAPI)
- **Prevention:** Use `asyncio.run()` only from sync context, or use `loop.run_until_complete()` in existing loop
- **Phase:** 1 (Async Foundation)

### Pitfall: Blocking Calls in Async Code
- **Warning Signs:** Slow performance despite async, one slow lead blocks all
- **Cause:** Using sync libraries (requests, smtplib) inside async functions
- **Prevention:** Audit all imports, use only async libraries (httpx, aiosmtplib)
- **Phase:** 1 (Async Foundation)

## Email Verification

### Pitfall: IP Blacklisting
- **Warning Signs:** Increasing timeouts, 550 errors, "blocked" messages
- **Cause:** Too many SMTP checks from same IP
- **Prevention:**
  - Rate limit SMTP checks (max 10/minute per IP)
  - Use connection pooling
  - Rotate IPs if available
  - Use valid HELO hostname
- **Phase:** 1 (Async Foundation)

### Pitfall: Catch-All False Positives
- **Warning Signs:** 100% verification rate for some domains
- **Cause:** Catch-all servers accept any email address
- **Prevention:**
  - Test with random gibberish email first
  - If random passes, mark domain as catch-all
  - Lower confidence score for catch-all domains
- **Phase:** 6 (Pipeline Integration)

### Pitfall: Greylisting Delays
- **Warning Signs:** First check fails, retry succeeds
- **Cause:** Greylisting temporarily rejects unknown senders
- **Prevention:** Implement retry with 30-60 second delay
- **Phase:** 1 (Async Foundation)

### Pitfall: SMTP Timeout Cascades
- **Warning Signs:** Entire batch stalls on one slow domain
- **Cause:** Single timeout blocks concurrent operations
- **Prevention:**
  - Set aggressive timeouts (10s connect, 30s total)
  - Use asyncio.wait_for() with per-operation timeouts
  - Don't await sequentially
- **Phase:** 1 (Async Foundation)

## Sitemap Scraping

### Pitfall: Missing Sitemaps
- **Warning Signs:** 404 on /sitemap.xml
- **Cause:** Not all sites have sitemaps, or use non-standard locations
- **Prevention:**
  - Check robots.txt for sitemap URL
  - Try common paths: /sitemap.xml, /sitemap_index.xml, /sitemap/
  - Fall back to contact page heuristics if no sitemap
- **Phase:** 2 (Sitemap Sniper)

### Pitfall: Sitemap Index Recursion
- **Warning Signs:** Incomplete URL list, missing pages
- **Cause:** Sitemap indexes reference other sitemaps
- **Prevention:** Recursively parse sitemap indexes (limit depth to 3)
- **Phase:** 2 (Sitemap Sniper)

### Pitfall: Rate Limiting by Target Sites
- **Warning Signs:** 429 errors, blocked IPs
- **Cause:** Scraping too fast
- **Prevention:** Respectful delays (1-2s between requests per domain)
- **Phase:** 2 (Sitemap Sniper)

## Search Engine Scraping

### Pitfall: DuckDuckGo Changes
- **Warning Signs:** Empty results, parsing errors
- **Cause:** DDG updates their HTML/API
- **Prevention:**
  - Use duckduckgo-search library (maintained)
  - Have Bing fallback ready
  - Monitor for library updates
- **Phase:** 4 (LinkedIn Stealth)

### Pitfall: Bot Detection
- **Warning Signs:** CAPTCHAs, empty results, blocks
- **Cause:** Detectable request patterns
- **Prevention:**
  - Rotate user agents
  - Add random delays (2-5s)
  - Don't hammer same query repeatedly
- **Phase:** 4 (LinkedIn Stealth)

### Pitfall: LinkedIn Snippet Parsing
- **Warning Signs:** Missing names/titles, wrong person matched
- **Cause:** Snippet format varies, multiple people with same name
- **Prevention:**
  - Validate company name appears in result
  - Parse multiple results, score by relevance
  - Accept uncertainty (may get wrong person)
- **Phase:** 4 (LinkedIn Stealth)

## Email Pattern Guessing

### Pitfall: Pattern Explosion
- **Warning Signs:** Slow verification, too many API calls
- **Cause:** Testing too many pattern variations
- **Prevention:**
  - Limit to 8-10 most common patterns
  - Stop on first verified email
  - Order patterns by probability
- **Phase:** 5 (Pattern Guerrilla)

### Pitfall: Name Normalization
- **Warning Signs:** Missed emails due to name variations
- **Cause:** "John" vs "Jonathan", "Bob" vs "Robert"
- **Prevention:**
  - Normalize common nicknames
  - Try both formal and informal names
- **Phase:** 5 (Pattern Guerrilla)

## Pipeline Integration

### Pitfall: Lost Errors
- **Warning Signs:** Silent failures, missing data without explanation
- **Cause:** Broad try/except swallowing errors
- **Prevention:**
  - Log all exceptions with context
  - Track success/failure counts per method
  - Return partial results with failure reasons
- **Phase:** 6 (Pipeline Integration)

### Pitfall: Fallback Trigger Logic
- **Warning Signs:** Paying for leads that free methods could find
- **Cause:** Triggering paid fallback too early
- **Prevention:**
  - Only fallback after ALL free methods fail
  - Set minimum confidence threshold before accepting free result
  - Track metrics to tune fallback threshold
- **Phase:** 6 (Pipeline Integration)

## Testing

### Pitfall: Test Data Bias
- **Warning Signs:** Great test results, poor production results
- **Cause:** Testing on easy domains (big companies with good email hygiene)
- **Prevention:**
  - Test on real lead mix (small businesses, varied industries)
  - Include known-difficult domains
  - Track success by domain type
- **Phase:** 7 (Testing)

### Pitfall: Flaky Async Tests
- **Warning Signs:** Tests pass/fail randomly
- **Cause:** Race conditions, timing dependencies
- **Prevention:**
  - Mock external services in unit tests
  - Use deterministic test data
  - Separate unit tests from integration tests
- **Phase:** 7 (Testing)

---
*Research: 2026-01-18*
