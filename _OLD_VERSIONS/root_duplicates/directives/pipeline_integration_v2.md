# Master Directive: LeadSnipe Enrichment Pipeline Integration

This directive defines the final logic and integration steps for the LeadSnipe Lead Enrichment Pipeline. Use this to implement or refine the orchestration in `leadsnipe_api.py` and ensure the frontend reflects accurate data.

## 1. The 4-Stage Orchestration Logic

The pipeline must execute in this exact sequence to ensure maximum efficiency and minimum cost.

### Stage 1: Raw Scrape (The Foundation)
- **Tool**: `n8n_gmaps_scraper.py` (via N8N Webhook)
- **Input**: Niche + Location
- **Output**: `_raw.json`
- **Goal**: Gather as many raw data points as possible (Name, Website, Scraper Email).

### Stage 2: The Cleaning Buffer & Snoop (Free Enrichment)
This stage performs two critical tasks before moving to paid APIs.
1. **Tool**: `find_owner_linkedin.py` (Snoop)
   - **Input**: `_raw.json`
   - **Goal**: Scrape the business website for owner names and LinkedIn URLs. Save to `_owners.json`.
2. **Tool**: `verify_email.py` (The Cleaning Filter)
   - **Input**: `_owners.json`
   - **Goal**: Run with `--no-smtp`. 
   - **Action**: Check if any email provided by the scraper is a "Technical Hash" (e.g., Wixpress, Sentry, AWS). 
   - **Logic**: If an email fails verification (syntax, MX, or technical junk patterns), **DELETE** it from the lead record. This forces the next stage to find a real email.

### Stage 3: High-Quality Enrichment (Anymailfinder)
- **Tool**: `anymailfinder_email.py`
- **Input**: `_owners.json`
- **Logic (Skip-Credit Optimization)**:
  - **IF** lead has a verified, deliverable email from Stage 2: **SKIP** (Save $0.02).
  - **IF** lead has no email (or it was deleted in Stage 2): Use Anymailfinder to lookup via LinkedIn or Name+Domain.
- **Output**: `_enriched.json`

### Stage 4: Personalization (AI & Gmail)
- **Tool**: `generate_outreach_emails.py`
- **Goal**: Analyze websites for triggers and create Gmail drafts.
- **Output**: `email_drafts.json`

---

## 2. Critical Implementation Details

### A. Technical Junk Filters (In `verify_email.py`)
Ensure these patterns are active to filter out "Scraper Noise":
- `r'[a-f0-9]{20,}'` (Technical hashes/Next.js/Wix)
- Keywords: `wixpress`, `sentry`, `aws`, `amazon`, `notification`, `mailer-daemon`.
- Extensions: `.png`, `.jpg`, `.webp` inside the email string.

### B. Data Mapping for UI
When merging the final results into the leads store, use this logic:
- `id`: Use Google `place_id` where available.
- `has_direct_contact`: `true` if lead has an `email` OR `anymailfinder_email` OR `linkedin_url`.
- `email_verified`: `true` if (`anymailfinder_email` exists) OR (`email` exists AND `email_verification.deliverable == true`).

### C. Pipeline Resilience
Orchestration in Python should use `subprocess.run` with error capturing:
- Check `result.returncode`.
- If a script fails (e.g., Snooper hits a Google Bot Wall), **DO NOT FAIL THE WHOLE PIPELINE**. 
- Log the error and move to the next stage with the data currently available.

## 3. Environment Dependencies
- `ANYMAILFINDER_API_KEY`: Required for Stage 3.
- `OPENROUTER_API_KEY`: Required for Stage 4.
- `token.json`: Required for Gmail Draft creation.

---

**Hand-off Note**: If the user asks to "Run a hunt," ensure you are calling the `leadsnipe_api.py` endpoint rather than running individual scripts manually, to maintain state synchronization.
