# Roadmap: LeadSnipe Stealth Hybrid Engine

**Created:** 2026-01-18
**Milestone:** v2.0 — Stealth Hybrid Lead Engine
**Phases:** 7
**Requirements:** 28 mapped

## Overview

| # | Phase | Goal | Requirements | Status |
|---|-------|------|--------------|--------|
| 1 | Async Foundation | Replace sync verification with async | ASYNC-01 to ASYNC-05 | ✓ Complete |
| 2 | Sitemap Sniper | Extract emails from contact pages | SITEMAP-01 to SITEMAP-05 | ✓ Complete |
| 3 | Metadata Recon | Get org info from SSL certs | META-01 to META-02 | ○ Pending |
| 4 | LinkedIn Stealth | Find profiles via search snippets | LINKEDIN-01 to LINKEDIN-04 | ○ Pending |
| 5 | Pattern Guerrilla | Guess and verify email patterns | PATTERN-01 to PATTERN-05 | ○ Pending |
| 6 | Pipeline Integration | Connect components with fallback | PIPELINE-01 to PIPELINE-05 | ○ Pending |
| 7 | Testing | Validate 80%+ discovery on 25 leads | TEST-01 to TEST-03 | ○ Pending |

---

## Phase 1: Async Foundation

**Goal:** Replace synchronous email verification with async system using aiosmtplib/aiodns

**Requirements:**
- ASYNC-01: Async email verification with aiosmtplib
- ASYNC-02: Async MX resolution with aiodns
- ASYNC-03: Parallel verification (50+ concurrent)
- ASYNC-04: Catch-all domain detection
- ASYNC-05: Greylist retry logic

**Success Criteria:**
1. User can verify 50 emails in parallel completing in <30 seconds
2. System correctly identifies catch-all domains (test with known catch-all)
3. System retries greylisted emails after delay and succeeds
4. No blocking calls in verification pipeline (async throughout)

**Output:** `execution/async_verifier.py`

**Dependencies:** None (foundation)

**Completed:** 2026-01-18

---

## Phase 2: Sitemap Sniper

**Goal:** Discover and scrape contact/team pages from XML sitemaps

**Requirements:**
- SITEMAP-01: Sitemap URL discovery
- SITEMAP-02: Recursive sitemap parsing
- SITEMAP-03: Contact page identification
- SITEMAP-04: Email extraction from pages
- SITEMAP-05: Staff name extraction

**Success Criteria:**
1. System finds sitemap for 70%+ of domains with sitemaps
2. System identifies contact/about/team pages correctly
3. System extracts valid email addresses from contact pages
4. System extracts staff names from team pages

**Output:** `execution/sitemap_sniper.py`

**Dependencies:** httpx (existing)

**Completed:** 2026-01-18

---

## Phase 3: Metadata Recon

**Goal:** Extract organization info from SSL certificates

**Requirements:**
- META-01: SSL cert org extraction
- META-02: Org name as business identifier

**Success Criteria:**
1. System extracts organization from SSL certs where available
2. System gracefully handles certs without org info
3. Extracted org name matches actual business name

**Output:** `execution/metadata_recon.py`

**Dependencies:** ssl (stdlib)

---

## Phase 4: LinkedIn Stealth

**Goal:** Find LinkedIn profiles via search engine snippets without hitting LinkedIn

**Requirements:**
- LINKEDIN-01: DuckDuckGo LinkedIn search
- LINKEDIN-02: LinkedIn URL extraction
- LINKEDIN-03: Name/title extraction from snippet
- LINKEDIN-04: Bing fallback

**Success Criteria:**
1. System finds LinkedIn profiles for 50%+ of searchable names
2. System never makes direct requests to linkedin.com
3. System extracts name and title from search snippets
4. System falls back to Bing when DDG fails

**Output:** `execution/linkedin_stealth.py`

**Dependencies:** duckduckgo-search (new)

---

## Phase 5: Pattern Guerrilla

**Goal:** Generate email pattern guesses and verify in parallel

**Requirements:**
- PATTERN-01: Generate 8-10 patterns per lead
- PATTERN-02: Order patterns by probability
- PATTERN-03: Parallel async verification
- PATTERN-04: Stop on first valid
- PATTERN-05: Nickname normalization

**Success Criteria:**
1. System generates correct pattern variations for names
2. System finds valid email via pattern guessing for 30%+ of leads
3. System stops verification on first valid email (no wasted checks)
4. System handles nicknames (Bob → Robert, etc.)

**Output:** `execution/pattern_guerrilla.py`

**Dependencies:** Phase 1 (Async Verifier)

---

## Phase 6: Pipeline Integration

**Goal:** Connect all stealth components with hybrid fallback to paid APIs

**Requirements:**
- PIPELINE-01: Free methods first, paid fallback
- PIPELINE-02: Gravatar confidence check
- PIPELINE-03: Method success tracking
- PIPELINE-04: Partial results with failure reasons
- PIPELINE-05: Replace existing email/LinkedIn stages

**Success Criteria:**
1. System exhausts ALL free methods before calling paid APIs
2. System tracks which method found each email
3. System integrates with existing UnifiedPipeline
4. System reports why leads failed (which methods tried)

**Output:** Modified `execution/unified_pipeline.py`, new `execution/stealth_engine.py`

**Dependencies:** Phases 1-5

---

## Phase 7: Testing

**Goal:** Validate 80%+ email discovery on real 25-lead hunt at $0 cost

**Requirements:**
- TEST-01: 80%+ discovery rate
- TEST-02: $0 API costs (free methods only)
- TEST-03: All emails verified deliverable

**Success Criteria:**
1. 25-lead test hunt achieves 80%+ email discovery (20+ emails found)
2. Zero paid API calls during test (SerpAPI for Maps is OK, email APIs = fail)
3. All discovered emails pass verification (no false positives)
4. Test covers varied industries (not just easy domains)

**Output:** Test results documented, metrics tracked

**Dependencies:** Phase 6

---

## Milestone Completion

When all phases complete:
- [ ] 80%+ email discovery rate achieved
- [ ] $0 cost for email enrichment
- [ ] Async pipeline faster than sync
- [ ] Existing functionality preserved
- [ ] Production-ready code merged

---
*Roadmap created: 2026-01-18*
