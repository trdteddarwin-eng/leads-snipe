# Architecture Research: Stealth Lead Enrichment

## Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Stealth Hybrid Engine                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Sitemap    │  │   Metadata   │  │   LinkedIn   │       │
│  │   Sniper     │  │    Recon     │  │   Stealth    │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └────────────┬────┴────────────────┘                │
│                      ▼                                       │
│              ┌──────────────┐                                │
│              │   Pattern    │                                │
│              │  Guerrilla   │                                │
│              └──────┬───────┘                                │
│                     ▼                                        │
│              ┌──────────────┐                                │
│              │    Async     │                                │
│              │  Verifier    │                                │
│              └──────┬───────┘                                │
│                     ▼                                        │
│              ┌──────────────┐                                │
│              │   Fallback   │◄── Anymailfinder/Apollo        │
│              │   Gateway    │                                │
│              └──────────────┘                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Async Verifier (`async_verifier.py`)
- **Purpose:** Core async email verification engine
- **Inputs:** List of email candidates
- **Outputs:** List of verified emails with confidence scores
- **Dependencies:** aiosmtplib, aiodns
- **Key Methods:**
  - `verify_batch(emails: List[str]) -> List[VerificationResult]`
  - `check_mx(domain: str) -> List[str]`
  - `check_smtp(email: str, mx_host: str) -> bool`
  - `detect_catchall(domain: str) -> bool`

### 2. Sitemap Sniper (`sitemap_sniper.py`)
- **Purpose:** Extract contact/team page URLs from sitemaps
- **Inputs:** Domain URL
- **Outputs:** List of contact page URLs, extracted emails
- **Dependencies:** httpx, lxml
- **Key Methods:**
  - `discover_sitemap(domain: str) -> str`
  - `parse_sitemap(url: str) -> List[str]`
  - `filter_contact_pages(urls: List[str]) -> List[str]`
  - `scrape_emails(urls: List[str]) -> List[str]`

### 3. Metadata Recon (`metadata_recon.py`)
- **Purpose:** Extract org info from SSL certs
- **Inputs:** Domain URL
- **Outputs:** Organization name, registration info
- **Dependencies:** ssl (stdlib)
- **Key Methods:**
  - `get_ssl_org(domain: str) -> Optional[str]`
  - `get_cert_info(domain: str) -> dict`

### 4. LinkedIn Stealth (`linkedin_stealth.py`)
- **Purpose:** Find LinkedIn profiles via search snippets
- **Inputs:** Name, company name
- **Outputs:** LinkedIn URL, title from snippet
- **Dependencies:** duckduckgo-search, httpx
- **Key Methods:**
  - `search_linkedin(name: str, company: str) -> Optional[LinkedInResult]`
  - `parse_snippet(snippet: str) -> dict`

### 5. Pattern Guerrilla (`pattern_guerrilla.py`)
- **Purpose:** Generate and verify email pattern guesses
- **Inputs:** First name, last name, domain
- **Outputs:** Valid email address (first match)
- **Dependencies:** Async Verifier
- **Key Methods:**
  - `generate_patterns(first: str, last: str, domain: str) -> List[str]`
  - `find_valid_email(patterns: List[str]) -> Optional[str]`

### 6. Fallback Gateway (`fallback_gateway.py`)
- **Purpose:** Route to paid APIs when free methods fail
- **Inputs:** Lead data, stealth results
- **Outputs:** Final enriched lead
- **Dependencies:** Existing Anymailfinder/Apollo integrations
- **Key Methods:**
  - `should_fallback(stealth_result: dict) -> bool`
  - `enrich_with_paid(lead: Lead) -> Lead`

## Data Flow

```
Lead Input (name, domain, website)
        │
        ▼
┌───────────────────────┐
│ 1. Sitemap Sniper     │──► Contact page URLs + direct emails
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 2. Metadata Recon     │──► Org name from SSL cert
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 3. LinkedIn Stealth   │──► Decision maker name + title
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 4. Pattern Guerrilla  │──► Email candidates from name patterns
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 5. Async Verifier     │──► Verified email (or None)
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 6. Fallback Gateway   │──► Final email (paid API if needed)
└───────────┬───────────┘
            │
            ▼
    Enriched Lead Output
```

## Integration with Existing Pipeline

### Current Pipeline (unified_pipeline.py)
```
Stage 1: EngineZero (Google Maps) → leads
Stage 2: verify_email (sync) → verified emails
Stage 3: LinkedInFinder → LinkedIn profiles
Stage 4: IcebreakerEngine → personalization
```

### New Pipeline Integration
```
Stage 1: EngineZero (Google Maps) → leads [UNCHANGED]
Stage 2: StealthHybridEngine → emails + LinkedIn [NEW - replaces 2+3]
  └─ Sitemap Sniper
  └─ Metadata Recon
  └─ LinkedIn Stealth
  └─ Pattern Guerrilla
  └─ Async Verifier
  └─ Fallback Gateway
Stage 3: IcebreakerEngine → personalization [UNCHANGED]
```

### Integration Points

1. **Lead Input:** Receives Lead dataclass from EngineZero
2. **Lead Output:** Returns Lead with email, email_verified, owner_name, linkedin_url
3. **Progress Callbacks:** Uses existing `add_log()` and progress tracking
4. **Async Integration:** Run stealth engine in asyncio event loop within thread

```python
# In unified_pipeline.py
def run_stealth_enrichment(leads: List[Lead]) -> List[Lead]:
    return asyncio.run(stealth_engine.enrich_batch(leads))
```

## Build Order

Based on dependencies:

1. **Phase 1: Async Verifier** — Foundation, everything depends on this
2. **Phase 2: Sitemap Sniper** — Independent, uses httpx
3. **Phase 3: Metadata Recon** — Independent, uses ssl stdlib
4. **Phase 4: LinkedIn Stealth** — Independent, uses duckduckgo-search
5. **Phase 5: Pattern Guerrilla** — Depends on Async Verifier
6. **Phase 6: Pipeline Integration** — Depends on all above
7. **Phase 7: Testing** — End-to-end validation

---
*Research: 2026-01-18*
