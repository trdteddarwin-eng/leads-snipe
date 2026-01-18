# Architecture

**Analysis Date:** 2026-01-17

## Pattern Overview

**Overall:** 3-Layer Directive-Orchestration-Execution + Client-Server Decoupled Frontend

**Key Characteristics:**
- LLM orchestration layer (AI agent) sits between directives (SOPs) and execution (Python scripts)
- Deterministic Python execution scripts eliminate compounding LLM errors
- Next.js frontend communicates with FastAPI backend via REST API
- SQLite for local persistence, cloud services for deliverables
- Event-driven webhooks via Modal for automation

## Layers

**Layer 1: Directive (What to do)**
- Purpose: Standard Operating Procedures in Markdown
- Location: `directives/` (archived in `_OLD_VERSIONS/`)
- Contains: Natural language instructions - goals, inputs, tools, outputs, edge cases
- Depends on: Nothing (source of truth)
- Used by: LLM orchestration layer

**Layer 2: Orchestration (Decision making)**
- Purpose: LLM agent performs intelligent routing between intent and execution
- Location: Agent context (Claude/Gemini reading `CLAUDE.md`)
- Contains: Decision logic, error handling, directive updates
- Depends on: Directives, Execution scripts
- Used by: User interactions

**Layer 3: Execution (Doing the work)**
- Purpose: Deterministic Python scripts for API calls, data processing
- Location: `execution/`
- Contains: Lead generation, email verification, LinkedIn discovery
- Depends on: Environment variables, external APIs
- Used by: Orchestration layer, FastAPI server

**Layer 4: Frontend (User Interface)**
- Purpose: React/Next.js web application for hunt management
- Location: `leadsnipe-app/src/`
- Contains: Pages, components, API client, types
- Depends on: FastAPI backend at `http://127.0.0.1:8000`
- Used by: End users

## Data Flow

**Lead Generation Flow:**

```
1. User submits hunt → Frontend (leadsnipe-app/src/app/hunt/new/page.tsx)
                    ↓
2. POST /api/hunt  → api.ts creates hunt request
                    ↓
3. FastAPI server  → leadsnipe_api.py creates SQLite record
                    ↓
4. Background thread → UnifiedPipeline orchestrates 4 stages:
   │
   ├─ Stage 1: EngineZero (engine_zero.py)
   │            └── SerpAPI Google Maps + 50 parallel scrapers
   │
   ├─ Stage 2: verify_email (verify_email.py)
   │            └── 3-layer verification (Syntax/DNS/SMTP)
   │
   ├─ Stage 3: LinkedInFinder (linkedin_finder_unified.py)
   │            └── Multi-strategy LinkedIn discovery
   │
   └─ Stage 4: IcebreakerEngine (icebreaker_engine.py)
                └── AI personalization hooks
                    ↓
5. Progress updates → SQLite + SSE streaming
                    ↓
6. Results view    → /hunt/[id]/results
```

**State Management:**
- Backend: SQLite database with `hunts` and `hunt_logs` tables
- Frontend: React state via `useState` hooks (no global state library)
- Data mapping: `api.ts` transforms backend responses to frontend types

## Key Abstractions

**Lead**
- Purpose: Represents a business lead with contact information
- Python: Dataclass in `engine_zero.py`, Pydantic model in `leadsnipe_api.py`
- TypeScript: Interface in `types.ts`
- Pattern: Dataclass → API → TypeScript interface with mapping layer

**Hunt**
- Purpose: Represents a lead generation job/campaign
- State machine: `queued → scraping → finding_owners → getting_emails → generating_outreach → completed/failed`
- Persistence: SQLite `hunts` table + in-memory `hunts` dict

**Pipeline**
- Purpose: Orchestrates multi-stage lead enrichment
- Location: `unified_pipeline.py` (UnifiedPipeline class)
- Pattern: Stage-based processing with progress callbacks

**RateLimiter**
- Purpose: Prevents API bans with adaptive delays
- Location: `rate_limiter.py`
- Pattern: Singleton with per-domain tracking, backoff on failures

## Entry Points

**FastAPI Server:**
- Location: `execution/leadsnipe_api.py`
- Run: `python3 execution/leadsnipe_api.py` or `uvicorn`
- Endpoints: REST API, hunt management, SSE streaming, Gmail OAuth

**Next.js App:**
- Location: `leadsnipe-app/src/app/page.tsx` (dashboard)
- Run: `npm run dev` from `leadsnipe-app/`
- Routes: Dashboard, hunts, analytics, settings

**CLI Scripts:**
- Location: Each `execution/*.py` is runnable standalone
- Example: `python3 execution/engine_zero.py --industry "Dentist" --location "Union, NJ"`

## Error Handling

**Strategy:** Self-annealing - fix, update tool, test, update directive

**Patterns:**
- `onError: continue` - Pipeline continues on individual lead failures
- Try/except with logging in execution scripts
- FastAPI HTTPException for API errors
- Frontend try/catch with console.error
- Rate limiter backoff on 429/503 responses

## Cross-Cutting Concerns

**Logging:**
- Backend: Print statements with timestamps, stored in `hunt_logs` SQLite table
- Frontend: Console logging

**Validation:**
- Backend: Pydantic models
- Frontend: TypeScript types
- Email: Regex + DNS + SMTP verification

**Authentication:**
- Gmail OAuth: `token.json`
- Firebase: `user_id` field (optional, not enforced)
- No auth on local API endpoints

**Configuration:**
- Environment: `.env` loaded via `python-dotenv`
- Frontend: Hardcoded `API_BASE_URL = 'http://127.0.0.1:8000'`

---

*Architecture analysis: 2026-01-17*
