# Technology Stack

**Analysis Date:** 2026-01-17

## Languages

**Primary:**
- Python 3.x - Backend execution scripts, API server, lead pipeline (`execution/*.py`)
- TypeScript 5.x - Frontend web application (`leadsnipe-app/src/**/*.{ts,tsx}`)

**Secondary:**
- JavaScript - Configuration files (`next.config.js`, `tailwind.config.js`)

## Runtime

**Environment:**
- Node.js - Frontend (Next.js) runtime
- Python 3.x - Backend scripts and FastAPI server
- Platform: macOS (Darwin) development environment

**Package Managers:**
- npm - Frontend dependencies (`package-lock.json`)
- pip - Python dependencies (`requirements.txt`)

## Frameworks

**Core:**
- Next.js 15.0.3 (root) / 16.1.1 (leadsnipe-app) - React meta-framework
- FastAPI - Python API server (`execution/leadsnipe_api.py`)
- React 18.3.1 (root) / 19.2.3 (leadsnipe-app) - UI library

**Testing:**
- None detected - No test frameworks configured

**Build/Dev:**
- TypeScript 5.x - Type checking
- PostCSS 8.x - CSS processing
- Tailwind CSS 3.4.x / 4.x - Utility-first CSS
- ESLint - Linting (Next.js config)

## Key Dependencies

**Frontend (root `package.json`):**
- `@anthropic-ai/sdk` ^0.32.1 - Claude AI integration
- `next` 15.0.3 - Server-side rendering
- `react` / `react-dom` 18.3.1 - UI rendering
- `framer-motion` ^12.24.0 - Animations
- `zod` ^3.23.8 - Schema validation
- `lucide-react` ^0.454.0 - Icons

**Frontend (`leadsnipe-app/package.json`):**
- `next` 16.1.1 - Latest Next.js
- `react` / `react-dom` 19.2.3 - React 19
- `motion` ^12.24.12 - Animations
- `lucide-react` ^0.562.0 - Icons
- `date-fns` ^4.1.0 - Date utilities
- `uuid` ^13.0.0 - UUID generation

**Backend (`requirements.txt`):**
- `anthropic` >=0.40.0 - Claude AI SDK
- `openai` - OpenAI API
- `google-genai` >=1.0.0 - Gemini AI SDK
- `httpx` >=0.28.0 - Async HTTP client
- `requests` >=2.32.0 - HTTP client
- `beautifulsoup4` >=4.12.0 - HTML parsing
- `apify-client` >=1.8.0 - Web scraping API
- `playwright` >=1.49.0 - Browser automation

**Google Services:**
- `google-auth` >=2.36.0 - Authentication
- `google-auth-oauthlib` >=1.2.0 - OAuth2 flow
- `google-api-python-client` >=2.160.0 - Google APIs
- `gspread` >=6.1.0 - Google Sheets

**Data Processing:**
- `pandas` >=2.2.0 - Data manipulation
- `numpy` >=1.26.0 - Numerical computing
- `Pillow` >=11.0.0 - Image processing
- `mediapipe` >=0.10.0 - Computer vision
- `opencv-python` >=4.9.0 - Image/video processing

**Infrastructure:**
- `modal` >=0.73.0 - Serverless Python (webhooks)
- `python-dotenv` >=1.0.0 - Environment management
- `pinecone-client` - Vector database (RAG)

**UI Components:**
- `@radix-ui/react-slot` ^1.1.0 - Primitive components
- `class-variance-authority` ^0.7.0 - Component variants
- `clsx` ^2.1.1 - Class name utility
- `tailwind-merge` ^2.5.4 - Tailwind class merging

## Configuration

**Environment:**
- `.env` - API keys (APIFY, SERPAPI, OPENROUTER, ANTHROPIC, APOLLO, ANYMAILFINDER)
- `.env.local` - Local overrides
- Environment vars loaded via `python-dotenv` and Next.js

**Build:**
- `tsconfig.json` - TypeScript config (ESNext target, bundler module resolution)
- `tailwind.config.js` - Tailwind with custom theme (HSL colors, animations)
- `next.config.js` / `next.config.ts` - Next.js configuration
- `postcss.config.js` / `postcss.config.mjs` - PostCSS with Tailwind

## Database

**Primary:**
- SQLite - Hunt persistence (`execution/leadsnipe_api.py`)
- Location: `.tmp/leadsnipe.db`
- Tables: `hunts`, `hunt_logs`

**Secondary:**
- JSON files in `.tmp/` - Intermediate lead data
- Google Sheets - External deliverables

## Platform Requirements

**Development:**
- Node.js (modern required for Next.js 15+)
- Python 3.x
- macOS/Linux recommended

**Production:**
- Local Python FastAPI server: `http://127.0.0.1:8000`
- Next.js frontend: development server
- Modal webhooks: `https://nick-90891--claude-orchestrator-*.modal.run`

---

*Stack analysis: 2026-01-17*
