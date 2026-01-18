# LeadSnipe: Stealth Hybrid Lead Engine

## What This Is

A lead generation platform that discovers business leads from Google Maps, finds decision-maker emails, and generates personalized outreach. This milestone adds the **Stealth Hybrid Engine** — a free, async, high-speed lead enrichment system that achieves 80%+ email discovery rates at $0 by using sitemap scraping, search snippet extraction, email pattern guessing, and async SMTP verification instead of paid APIs.

## Core Value

**Find valid decision-maker emails for 80%+ of leads using free methods, falling back to paid APIs only when necessary.**

The current system achieves only ~24% email discovery while costing money per lead. The Stealth Hybrid Engine flips this: free methods first, paid fallback second, async everything.

## Requirements

### Validated

*Existing capabilities from current codebase:*

- ✓ User can create hunts with industry + location — existing
- ✓ System discovers leads from Google Maps via SerpAPI — existing
- ✓ System scrapes lead websites in parallel — existing
- ✓ System verifies emails via syntax/DNS/SMTP checks — existing (sync)
- ✓ System finds LinkedIn profiles via DuckDuckGo search — existing (fragile)
- ✓ System finds decision-maker emails via Anymailfinder/Apollo — existing (paid)
- ✓ System generates AI icebreakers for personalization — existing
- ✓ User can view hunt progress in real-time via SSE — existing
- ✓ User can export leads and send emails via Gmail — existing

### Active

*Stealth Hybrid Engine — 7-phase build:*

- [ ] **ASYNC-01**: System performs email verification asynchronously using aiosmtplib/aiodns
- [ ] **ASYNC-02**: System can verify 50+ emails in parallel without blocking
- [ ] **SITEMAP-01**: System extracts contact/about/team page URLs from XML sitemaps
- [ ] **SITEMAP-02**: System scrapes extracted pages for email addresses and staff names
- [ ] **META-01**: System extracts organization name from SSL certificates
- [ ] **META-02**: System uses org name to identify decision maker context
- [ ] **LINKEDIN-01**: System extracts LinkedIn profile URLs from DuckDuckGo/Bing snippets without hitting LinkedIn
- [ ] **LINKEDIN-02**: System parses name/title from search snippet text
- [ ] **PATTERN-01**: System generates email pattern variations (firstname@, john.doe@, jdoe@, owner@, info@)
- [ ] **PATTERN-02**: System async-verifies all pattern guesses in parallel
- [ ] **PATTERN-03**: System keeps first valid email per lead
- [ ] **PIPELINE-01**: System tries free methods first, falls back to paid APIs only if all free methods fail
- [ ] **PIPELINE-02**: System integrates Gravatar checks for email validation confidence
- [ ] **TEST-01**: System achieves 80%+ email discovery on 25-lead verification hunt

### Out of Scope

- Mobile app — web-first, mobile later
- Multi-tenant SaaS auth — local-only for now
- Replacing Google Maps discovery — SerpAPI stays, we're optimizing enrichment
- Real-time collaborative features — single-user workflow

## Context

**Current pain points:**
- 24% email discovery rate (too low)
- Paid API costs per lead (Anymailfinder, Apollo, SerpAPI)
- Synchronous email verification (slow, blocking)
- LinkedIn discovery is fragile and rate-limited

**Existing architecture:**
- FastAPI backend (`execution/leadsnipe_api.py` — 2,300+ lines, needs refactoring)
- 4-stage pipeline: EngineZero → verify_email → LinkedInFinder → IcebreakerEngine
- Next.js frontend with hunt management UI
- SQLite for persistence, SSE for real-time updates

**Key files to modify:**
- `execution/verify_email.py` — convert to async
- `execution/linkedin_finder_unified.py` — add search snippet extraction
- `execution/unified_pipeline.py` — integrate stealth methods with fallback
- New: `execution/sitemap_sniper.py`
- New: `execution/metadata_recon.py`
- New: `execution/pattern_guerrilla.py`

## Constraints

- **Cost**: All new discovery methods must be free (no paid API calls)
- **Async**: All verification must be non-blocking using asyncio
- **Fallback**: Must gracefully fall back to existing paid methods if free methods fail
- **Compatibility**: Must integrate with existing pipeline without breaking current functionality

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid fallback vs replace | Keep paid APIs as safety net, not primary | — Pending |
| aiosmtplib for async SMTP | Standard async SMTP library, well-maintained | — Pending |
| DuckDuckGo/Bing snippets for LinkedIn | Avoids LinkedIn rate limits and ToS issues | — Pending |
| Sitemap-first for email discovery | Contact pages often have owner emails directly | — Pending |

---
*Last updated: 2026-01-18 after initialization*
