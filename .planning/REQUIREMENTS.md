# Requirements: LeadSnipe Stealth Hybrid Engine

**Defined:** 2026-01-18
**Core Value:** Find valid decision-maker emails for 80%+ of leads using free methods

## v1 Requirements

### Async Foundation ✓
- [x] **ASYNC-01**: System verifies emails asynchronously using aiosmtplib
- [x] **ASYNC-02**: System resolves MX records asynchronously using aiodns
- [x] **ASYNC-03**: System can verify 50+ emails in parallel without blocking
- [x] **ASYNC-04**: System detects catch-all domains to avoid false positives
- [x] **ASYNC-05**: System implements retry logic for greylisting (30-60s delay)

### Sitemap Sniper ✓
- [x] **SITEMAP-01**: System discovers sitemap URL from robots.txt or common paths
- [x] **SITEMAP-02**: System parses sitemap XML recursively (handles sitemap indexes)
- [x] **SITEMAP-03**: System identifies contact/about/team page URLs from sitemap
- [x] **SITEMAP-04**: System scrapes identified pages for email addresses
- [x] **SITEMAP-05**: System extracts staff names from team pages

### Metadata Recon
- [ ] **META-01**: System extracts organization name from SSL certificates
- [ ] **META-02**: System uses org name as fallback for business identification

### LinkedIn Stealth
- [ ] **LINKEDIN-01**: System searches DuckDuckGo for "site:linkedin.com {name} {company}"
- [ ] **LINKEDIN-02**: System parses LinkedIn URL from search result
- [ ] **LINKEDIN-03**: System extracts name and job title from search snippet
- [ ] **LINKEDIN-04**: System falls back to Bing if DuckDuckGo fails

### Pattern Guerrilla
- [ ] **PATTERN-01**: System generates 8-10 email pattern variations per lead
- [ ] **PATTERN-02**: System orders patterns by probability (firstname@ most common)
- [ ] **PATTERN-03**: System verifies all patterns in parallel using Async Verifier
- [ ] **PATTERN-04**: System stops on first verified email to save resources
- [ ] **PATTERN-05**: System normalizes common nicknames (Bob→Robert)

### Pipeline Integration
- [ ] **PIPELINE-01**: System tries all free methods before paid API fallback
- [ ] **PIPELINE-02**: System integrates Gravatar check for confidence scoring
- [ ] **PIPELINE-03**: System tracks success/failure counts per method
- [ ] **PIPELINE-04**: System returns partial results with failure reasons
- [ ] **PIPELINE-05**: System replaces existing verify_email + LinkedInFinder stages

### Testing
- [ ] **TEST-01**: System achieves 80%+ email discovery on 25-lead test hunt
- [ ] **TEST-02**: System completes test hunt with $0 API costs (free methods only)
- [ ] **TEST-03**: System verifies all discovered emails are deliverable

## v2 Requirements

### Performance Optimization
- **PERF-01**: System uses IP rotation for SMTP verification
- **PERF-02**: System implements connection pooling for SMTP
- **PERF-03**: System caches MX lookups per domain

### Additional Discovery
- **DISC-01**: System checks WHOIS for registrant email
- **DISC-02**: System scrapes social media profiles for emails
- **DISC-03**: System uses machine learning for pattern probability

## Out of Scope

| Feature | Reason |
|---------|--------|
| LinkedIn direct API | Requires OAuth, rate limits, ToS issues |
| LinkedIn scraping | Bot detection, account bans |
| Browser automation | Too slow, resource-heavy for scale |
| Paid API as primary | Defeats $0 goal |
| Mobile app | Web-first for this milestone |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ASYNC-01 | Phase 1 | Complete |
| ASYNC-02 | Phase 1 | Complete |
| ASYNC-03 | Phase 1 | Complete |
| ASYNC-04 | Phase 1 | Complete |
| ASYNC-05 | Phase 1 | Complete |
| SITEMAP-01 | Phase 2 | Complete |
| SITEMAP-02 | Phase 2 | Complete |
| SITEMAP-03 | Phase 2 | Complete |
| SITEMAP-04 | Phase 2 | Complete |
| SITEMAP-05 | Phase 2 | Complete |
| META-01 | Phase 3 | Pending |
| META-02 | Phase 3 | Pending |
| LINKEDIN-01 | Phase 4 | Pending |
| LINKEDIN-02 | Phase 4 | Pending |
| LINKEDIN-03 | Phase 4 | Pending |
| LINKEDIN-04 | Phase 4 | Pending |
| PATTERN-01 | Phase 5 | Pending |
| PATTERN-02 | Phase 5 | Pending |
| PATTERN-03 | Phase 5 | Pending |
| PATTERN-04 | Phase 5 | Pending |
| PATTERN-05 | Phase 5 | Pending |
| PIPELINE-01 | Phase 6 | Pending |
| PIPELINE-02 | Phase 6 | Pending |
| PIPELINE-03 | Phase 6 | Pending |
| PIPELINE-04 | Phase 6 | Pending |
| PIPELINE-05 | Phase 6 | Pending |
| TEST-01 | Phase 7 | Pending |
| TEST-02 | Phase 7 | Pending |
| TEST-03 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0 ✓

---
*Requirements defined: 2026-01-18*
