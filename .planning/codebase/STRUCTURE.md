# Directory Structure

**Analysis Date:** 2026-01-17

## Root Layout

```
.
├── .claude/                    # Claude Code configuration (GSD workflows)
├── .git/                       # Git repository
├── .next/                      # Next.js build output (root package)
├── .planning/                  # GSD planning artifacts
│   └── codebase/              # Codebase analysis documents
├── .tmp/                       # Temporary files, SQLite DB, intermediate data
├── _OLD_VERSIONS/             # Archived code (scripts, directives, duplicates)
├── execution/                  # Python backend scripts
├── leadsnipe-app/             # Next.js frontend application
├── node_modules/              # Root npm dependencies
│
├── .claudeignore              # Claude Code ignore patterns
├── .env                       # Environment variables (API keys)
├── .env.local                 # Local environment overrides
├── .gitignore                 # Git ignore patterns
├── AGENTS.md                  # Agent instructions (mirrors CLAUDE.md)
├── CHANGELOG_SMART_SCRAPER.md # Historical changelog
├── CLAUDE.md                  # AI agent instructions
├── FRONTEND_BUILD_PROMPT.md   # Frontend design prompts
├── GEMINI.md                  # Gemini agent instructions
├── OPTIMIZATION_SUMMARY.md    # Performance optimization notes
├── package.json               # Root npm package (legacy UI components)
├── package-lock.json          # Root npm lockfile
├── requirements.txt           # Python dependencies
├── SAAS_PRODUCTION_BLUEPRINT.md # Production planning doc
├── SaaS_IMPL_PLAN.md          # Implementation plan
├── tailwind.config.js         # Root Tailwind config
├── token.json                 # Gmail OAuth token
└── tsconfig.json              # Root TypeScript config
```

## Key Directories

### `execution/` - Backend Python Scripts

```
execution/
├── engine_zero.py             # Lead discovery engine (SerpAPI + parallel scraping)
├── icebreaker_engine.py       # AI-powered personalization hooks
├── leadsnipe_api.py           # FastAPI server (2,300+ lines - main backend)
├── linkedin_finder_unified.py # Multi-strategy LinkedIn discovery
├── rate_limiter.py            # Adaptive rate limiting with user-agent rotation
├── unified_pipeline.py        # 4-stage lead enrichment orchestrator
├── verify_email.py            # 3-layer email verification (syntax/DNS/SMTP)
└── optimized/                 # Experimental optimizations (not active)
```

**Entry points:**
- `leadsnipe_api.py` - Main FastAPI server
- Each script runnable standalone for testing

### `leadsnipe-app/` - Frontend Next.js Application

```
leadsnipe-app/
├── src/
│   ├── app/                   # Next.js App Router pages
│   │   ├── api/              # API route handlers (proxy to backend)
│   │   │   ├── hunt/         # Hunt-related endpoints
│   │   │   └── hunts/        # Hunts list endpoint
│   │   ├── analytics/        # Analytics dashboard page
│   │   ├── campaigns/        # Campaigns page (stub)
│   │   ├── hunt/             # Hunt detail pages
│   │   ├── leads/            # Leads management pages
│   │   ├── settings/         # Settings page
│   │   ├── globals.css       # Global styles with CSS variables
│   │   ├── layout.tsx        # Root layout with Sidebar
│   │   └── page.tsx          # Dashboard home page
│   │
│   ├── components/           # Reusable UI components
│   │   ├── Header.tsx        # Top navigation header
│   │   ├── Sidebar.tsx       # Left navigation sidebar
│   │   ├── LeadCard.tsx      # Lead display card
│   │   ├── BulkOutreachModal.tsx # Bulk email modal
│   │   └── index.ts          # Component exports
│   │
│   └── lib/                  # Shared utilities
│       ├── api.ts            # Backend API client with type mapping
│       ├── types.ts          # TypeScript type definitions
│       └── utils.ts          # Utility functions (cn, formatDate)
│
├── .next/                    # Next.js build output
├── node_modules/             # Frontend npm dependencies
├── package.json              # Frontend package config
├── tailwind.config.ts        # Tailwind CSS config
└── tsconfig.json             # TypeScript config
```

### `_OLD_VERSIONS/` - Archived Code

```
_OLD_VERSIONS/
├── old_directives/           # Archived SOP markdown files
├── old_scripts/              # 50+ archived Python scripts
│   ├── gmaps_lead_pipeline.py
│   ├── anymailfinder_decision_maker.py
│   ├── instantly_autoreply.py
│   └── ... (many more)
└── root_duplicates/          # Files moved from root
    ├── directives/           # Original directives folder
    └── leadsnipe-web/        # Previous web app version
```

### `.tmp/` - Temporary Files

```
.tmp/
├── leadsnipe.db              # SQLite database
├── {hunt_id}/                # Per-hunt data directories
│   ├── leads.json
│   └── exports/
└── *.json                    # Various intermediate files
```

## Naming Conventions

**Files:**
- Python: `snake_case.py` (e.g., `engine_zero.py`, `verify_email.py`)
- TypeScript/React: `PascalCase.tsx` for components (e.g., `LeadCard.tsx`)
- TypeScript utilities: `camelCase.ts` (e.g., `api.ts`, `types.ts`)

**Directories:**
- Lowercase with hyphens for multi-word (e.g., `leadsnipe-app`)
- Lowercase single words (e.g., `execution`, `components`, `lib`)

**Special patterns:**
- `[id]` - Next.js dynamic route segments
- `route.ts` - Next.js API route handlers
- `page.tsx` - Next.js page components
- `layout.tsx` - Next.js layout components

## Import Patterns

**Python:**
```python
# Relative imports within execution/
from engine_zero import EngineZero, EngineConfig
from unified_pipeline import UnifiedPipeline
```

**TypeScript:**
```typescript
// Path aliases via tsconfig
import { api } from '@/lib/api';
import type { Hunt, Lead } from '@/lib/types';
import { LeadCard } from '@/components/LeadCard';
```

## File Size Analysis

**Largest files (concern flags):**
- `execution/leadsnipe_api.py` - 84,909 bytes (2,300+ lines) - **needs decomposition**
- `execution/engine_zero.py` - 26,888 bytes
- `execution/unified_pipeline.py` - 23,661 bytes
- `execution/linkedin_finder_unified.py` - 19,339 bytes

---

*Structure analysis: 2026-01-17*
