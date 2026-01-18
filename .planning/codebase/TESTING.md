# Testing

**Analysis Date:** 2026-01-17

## Current State

**Test Framework:** None configured
**Test Files:** None found
**Coverage:** 0%

## Test Infrastructure

**Python:**
- No `pytest`, `unittest`, or test framework in `requirements.txt`
- No `tests/` directory
- No `conftest.py`
- No test files matching `*_test.py` or `test_*.py` patterns

**TypeScript/React:**
- No `jest`, `vitest`, or testing-library in `package.json`
- No `__tests__/` directory
- No test files matching `*.test.ts`, `*.test.tsx`, or `*.spec.*` patterns

**E2E:**
- `playwright` in requirements.txt but used for scraping, not testing
- No Cypress or Playwright test configurations

## Manual Testing Patterns

**Backend scripts:**
```python
# Scripts include __main__ blocks for manual testing
if __name__ == "__main__":
    # Example usage with hardcoded values
    leads = engine.discover_leads(industry="Dentist", location="Union, NJ")
```

**API testing:**
- Manual curl/Postman requests to `http://127.0.0.1:8000`
- No documented API test collection

## Critical Gaps

### High Priority (Before Production)

**1. Pipeline Integration Tests**
- Files: `execution/unified_pipeline.py`
- Risk: 4-stage pipeline with external API calls - failures cascade
- Recommended: Mock external APIs, test stage transitions

**2. API Contract Tests**
- Files: `execution/leadsnipe_api.py`, `leadsnipe-app/src/lib/api.ts`
- Risk: Frontend/backend type mismatches cause runtime errors
- Recommended: Generate OpenAPI spec, validate against TypeScript types

**3. Email Verification Tests**
- Files: `execution/verify_email.py`
- Risk: Email validation is core to product value
- Recommended: Unit tests for each verification layer

### Medium Priority

**4. Location Parser Tests**
- Files: `execution/leadsnipe_api.py` lines 298-354
- Risk: Complex regex parsing with many edge cases
- Recommended: Property-based testing with hypothesis

**5. Hunt State Machine Tests**
- Files: `execution/leadsnipe_api.py` HuntStage enum
- Risk: Invalid state transitions corrupt data
- Recommended: State machine validation tests

**6. Rate Limiter Tests**
- Files: `execution/rate_limiter.py`
- Risk: Too aggressive = bans, too loose = floods
- Recommended: Unit tests with time mocking

### Lower Priority

**7. React Component Tests**
- Files: `leadsnipe-app/src/components/`
- Risk: UI regressions
- Recommended: Snapshot or interaction tests

**8. Data Transformation Tests**
- Files: `leadsnipe-app/src/lib/api.ts` mapping functions
- Risk: Data loss or corruption in transformation
- Recommended: Unit tests for each mapper function

## Recommended Test Setup

### Python (pytest)

Add to `requirements.txt`:
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.0.0
responses>=0.25.0  # Mock HTTP
```

Directory structure:
```
tests/
├── conftest.py           # Fixtures
├── unit/
│   ├── test_verify_email.py
│   ├── test_rate_limiter.py
│   └── test_location_parser.py
├── integration/
│   └── test_pipeline.py
└── api/
    └── test_endpoints.py
```

### TypeScript (Vitest)

Add to `leadsnipe-app/package.json`:
```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/user-event": "^14.0.0",
    "msw": "^2.0.0"
  }
}
```

Directory structure:
```
leadsnipe-app/
├── src/
│   ├── __tests__/
│   │   ├── api.test.ts
│   │   └── types.test.ts
│   └── components/
│       └── __tests__/
│           └── LeadCard.test.tsx
```

## Mocking Strategy

**External APIs to mock:**
- SerpAPI (Google Maps results)
- Apify (Web scraping)
- Anymailfinder (Email discovery)
- Apollo (Decision maker lookup)
- OpenRouter/Claude (LLM responses)
- DuckDuckGo (LinkedIn search)

**Database:**
- Use in-memory SQLite for tests
- Reset between test runs

**Time:**
- Mock `datetime.now()` for rate limiter tests
- Mock `time.sleep()` for faster test runs

## CI/CD Integration

Currently not configured. Recommended:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest --cov=execution tests/

  typescript-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - working-directory: leadsnipe-app
        run: npm ci && npm test
```

---

*Testing analysis: 2026-01-17*
