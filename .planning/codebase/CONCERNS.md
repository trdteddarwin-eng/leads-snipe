# Codebase Concerns

**Analysis Date:** 2026-01-17

## Tech Debt

### Giant Monolithic API File
- **Issue:** `execution/leadsnipe_api.py` is 2,300+ lines combining API routes, business logic, database operations, web scraping, LLM integration, and email sending
- **Impact:** Difficult to maintain, test, or debug. Single changes can break unrelated functionality
- **Fix:** Decompose into modules:
  - `api/routes.py` - FastAPI endpoints
  - `services/hunt_service.py` - Hunt orchestration
  - `services/insight_engine.py` - AI insights
  - `db/repository.py` - Database operations

### Duplicated Code in _OLD_VERSIONS
- **Issue:** 50+ archived scripts creating confusion about active code
- **Impact:** Developers may reference wrong files. Bloats repository
- **Fix:** Remove `_OLD_VERSIONS/` or archive to separate branch

### Bare Except Clauses
- **Issue:** Multiple `except:` without specific exception types
- **Files:** `leadsnipe_api.py`, `verify_email.py`
- **Impact:** Silently swallows errors including KeyboardInterrupt
- **Fix:** Use specific exceptions (`except Exception as e:`)

### Hardcoded Configuration
- **Issue:** Rate limits, worker counts, API URL hardcoded
- **Files:**
  - `leadsnipe_api.py` (LLM semaphore)
  - `engine_zero.py` (user agents)
  - `api.ts` (`API_BASE_URL = 'http://127.0.0.1:8000'`)
- **Impact:** Cannot configure for different environments
- **Fix:** Move to environment variables or config file

## Known Bugs

### Frontend Displays Mocked Data
- **Symptoms:** Dashboard shows hardcoded "4,250 Credits" and "98.4% Avg Accuracy"
- **Files:** `leadsnipe-app/src/app/page.tsx` lines 116-142
- **Fix:** Fetch actual stats from backend `/api/stats` endpoint

### Live Discovery Feed is Static
- **Symptoms:** "Live Discovery Feed" shows 3 hardcoded items
- **Files:** `leadsnipe-app/src/app/page.tsx` lines 101-110
- **Fix:** Connect to SSE endpoint or create global activity feed

### Email Send API Mismatch
- **Symptoms:** Frontend sends `to_email` but backend expects `to`
- **Files:** `api.ts` line 218 vs `leadsnipe_api.py` line 2115
- **Fix:** Align parameter names between frontend and backend

## Security Considerations

### CRITICAL: Exposed API Keys in .env
- **Risk:** `.env` contains real API keys (APIFY, SERPAPI, OPENROUTER, APOLLO)
- **Mitigation:** `.gitignore` includes `.env` but file may have been committed
- **Action:**
  1. Rotate ALL API keys immediately
  2. Use `git filter-branch` or BFG to remove from history
  3. Use proper secrets management

### CORS Allows All Origins
- **Risk:** API accepts requests from any domain via `allow_origins=["*"]`
- **Files:** `leadsnipe_api.py` lines 1805-1811
- **Action:** Restrict to known frontend origins in production

### No Authentication on API
- **Risk:** All API endpoints publicly accessible without auth
- **Mitigation:** Local-only binding (127.0.0.1)
- **Action:** Add JWT or session-based auth before production

### Gmail OAuth Token in Plain File
- **Risk:** `token.json` contains OAuth refresh token in plain text
- **Mitigation:** `.gitignore` excludes `token.json`
- **Action:** Encrypt at rest or use credential storage

## Performance Bottlenecks

### Synchronous Database Access in Async Context
- **Problem:** SQLite operations block FastAPI event loop
- **Files:** `leadsnipe_api.py` - `get_db()` in async routes
- **Fix:** Use `aiosqlite` or run DB ops in thread pool

### Unbounded Memory Growth
- **Problem:** `hunts` and `leads_store` dicts grow indefinitely
- **Files:** `leadsnipe_api.py` lines 273-275
- **Fix:** Implement LRU cache or load from DB on demand

### Serial LLM Calls
- **Problem:** LLM semaphore limits concurrency but still blocks
- **Files:** `leadsnipe_api.py` lines 891-893
- **Fix:** Use `aiohttp` with async LLM calls

## Fragile Areas

### Location Parser
- **Files:** `leadsnipe_api.py` lines 298-354
- **Risk:** Complex regex with many edge cases ("North NJ" vs "Newark, NJ")
- **Safe modification:** Add unit tests first, consider geocoding API

### Hunt Status State Machine
- **Files:** `leadsnipe_api.py` HuntStage enum
- **Risk:** Status transitions happen in multiple places, no validation
- **Safe modification:** Create explicit state machine with valid transitions

### Frontend-Backend Type Drift
- **Files:** `types.ts` vs Pydantic models
- **Risk:** Types defined separately, no shared schema
- **Safe modification:** Generate TypeScript from OpenAPI spec

## Scaling Limits

### SQLite Database
- **Limit:** Single file, single-writer, ~1000 concurrent reads
- **Path:** Migrate to PostgreSQL for multi-user support

### In-Memory Hunt Storage
- **Limit:** ~100-1000 hunts depending on leads per hunt
- **Path:** Move to Redis or load from DB on demand

### Single Server Architecture
- **Limit:** Cannot scale horizontally
- **Path:** Stateless API, external job queue, shared database

## Missing Critical Features

### No User Authentication
- **Problem:** `user_id` field exists but no auth implementation
- **Blocks:** Multi-tenant deployment

### No Rate Limiting on API
- **Problem:** External clients can hammer endpoints
- **Blocks:** Production deployment without DDoS protection

### No Monitoring/Observability
- **Problem:** No logging aggregation, metrics, or tracing
- **Blocks:** Production debugging

## Test Coverage Gaps

### Zero Automated Tests
- **Files:** Entire codebase
- **Risk:** Any refactoring can silently break functionality
- **Priority:** Critical

### Priority Test Areas
1. Location parser (high bug surface)
2. Email verification layers
3. API endpoint contracts
4. Pipeline integration flow

---

*Concerns audit: 2026-01-17*
