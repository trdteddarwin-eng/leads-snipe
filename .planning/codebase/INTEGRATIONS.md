# External Integrations

**Analysis Date:** 2026-01-17

## APIs

### SerpAPI (Google Maps)
- **Purpose:** Lead discovery from Google Maps search results
- **Usage:** `execution/engine_zero.py` - Primary lead sourcing
- **Auth:** API key via `SERPAPI_API_KEY` env var
- **Rate limits:** Commercial API, paid per request
- **Fallback:** None configured

### Apify
- **Purpose:** Web scraping at scale
- **Usage:** `execution/engine_zero.py` - Parallel website scraping
- **Auth:** API key via `APIFY_API_TOKEN` env var
- **Rate limits:** Based on Apify plan
- **Fallback:** Direct scraping with rate limiting

### Anymailfinder
- **Purpose:** Email discovery for decision makers
- **Usage:** `execution/unified_pipeline.py` - Stage 2 email finding
- **Auth:** API key via `ANYMAILFINDER_API_KEY` env var
- **Rate limits:** Based on plan
- **Fallback:** LinkedIn-based email inference

### Apollo.io
- **Purpose:** Decision maker discovery and enrichment
- **Usage:** `execution/unified_pipeline.py` - Owner/CEO lookup
- **Auth:** API key via `APOLLO_API_KEY` env var
- **Rate limits:** Based on plan
- **Fallback:** Website scraping for owner names

### OpenRouter
- **Purpose:** LLM routing for AI operations
- **Usage:** `execution/leadsnipe_api.py` - AI insights and personalization
- **Auth:** API key via `OPENROUTER_API_KEY` env var
- **Rate limits:** Token-based, semaphore limits to 5 concurrent calls
- **Fallback:** None configured

### Anthropic Claude
- **Purpose:** AI text generation and analysis
- **Usage:** Root package, various AI operations
- **Auth:** API key via `ANTHROPIC_API_KEY` env var
- **Rate limits:** Token-based
- **Fallback:** OpenRouter routing

## Databases

### SQLite (Primary)
- **Purpose:** Hunt persistence, logs, lead storage
- **Connection:** File-based at `.tmp/leadsnipe.db`
- **Tables:** `hunts`, `hunt_logs`
- **Migrations:** Schema created inline in `init_database()`
- **Pooling:** None (contextmanager-based connections)

### Pinecone (Vector DB)
- **Purpose:** RAG and semantic search (planned)
- **Connection:** Client via `pinecone-client` package
- **Usage:** Not actively used in current codebase
- **Auth:** API key (not configured in .env)

## Authentication Providers

### Gmail OAuth
- **Purpose:** Email sending from user's Gmail account
- **Config:** OAuth credentials in `credentials.json`
- **Token storage:** `token.json` (plain text)
- **Scopes:** `gmail.send`, `gmail.readonly`
- **Flow:** `/api/gmail/connect` -> Google OAuth -> `/api/gmail/callback`
- **Location:** `execution/leadsnipe_api.py` lines 1150-1220

### Firebase (Planned)
- **Purpose:** User authentication
- **Config:** `lib/firebase.js` (currently in deleted state)
- **Usage:** `user_id` field in HuntRequest model, not enforced
- **Status:** Partially implemented, not active

## Webhooks

### Modal (Outbound)
- **Purpose:** Serverless Python execution for automation
- **Endpoints:**
  - `https://nick-90891--claude-orchestrator-list-webhooks.modal.run`
  - `https://nick-90891--claude-orchestrator-directive.modal.run`
  - `https://nick-90891--claude-orchestrator-test-email.modal.run`
- **Config:** `execution/webhooks.json` (archived in `_OLD_VERSIONS/`)
- **Triggers:** HTTP POST from external systems
- **Status:** Webhook infrastructure exists but scripts archived

### SSE (Server-Sent Events)
- **Purpose:** Real-time log streaming to frontend
- **Endpoint:** `/api/hunt/{id}/logs`
- **Implementation:** FastAPI StreamingResponse
- **Client:** Frontend polling/SSE connection

## Message Queues

None configured. Background tasks use Python threading.

## File Storage

### Local `.tmp/` Directory
- **Purpose:** Intermediate files, database, temp exports
- **Contents:**
  - `leadsnipe.db` - SQLite database
  - `{hunt_id}/` - Hunt-specific data
  - JSON files for lead data
- **Cleanup:** Manual, not automated

### Google Sheets (Deliverables)
- **Purpose:** Export leads to shareable spreadsheet
- **Auth:** OAuth via `gspread` and Google APIs
- **Usage:** Planned but not integrated in current flow

### Google Slides (Deliverables)
- **Purpose:** Presentation generation (per CLAUDE.md)
- **Auth:** OAuth via Google APIs
- **Usage:** Planned but not integrated in current flow

## Third-Party Services

### DuckDuckGo Search
- **Purpose:** LinkedIn profile discovery
- **Usage:** `execution/linkedin_finder_unified.py`
- **Auth:** None (public API)
- **Rate limits:** Aggressive rate limiting required

### LinkedIn (Scraping)
- **Purpose:** Decision maker profile discovery
- **Usage:** `execution/linkedin_finder_unified.py`
- **Auth:** None (public page scraping)
- **Limitations:** Heavy bot detection, needs rotation

## Integration Patterns

**Error Handling:**
- Try/except with continue for non-critical failures
- Return default dict on errors
- Log and continue philosophy

**Rate Limiting:**
- Centralized in `execution/rate_limiter.py`
- Per-domain tracking with adaptive delays
- User-agent rotation for scraping

**Data Transformation:**
- Frontend `api.ts` maps backend responses to frontend types
- Pydantic models validate backend data
- TypeScript interfaces define frontend contracts

---

*Integration analysis: 2026-01-17*
