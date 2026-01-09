# LeadSnipe Frontend Build - Complete Prompt for Claude

I need you to build a modern, professional frontend web application for LeadSnipe - a B2B lead generation platform. This will be a Next.js app with a clean, intuitive UI that connects to our Python backend pipeline.

---

## 🎯 Application Overview

**LeadSnipe** is a lead generation platform that finds service-based businesses, enriches them with decision maker emails and LinkedIn profiles, and exports them for outreach campaigns.

**Tech Stack:**
- Frontend: Next.js 14 (App Router), React, TypeScript, Tailwind CSS
- Backend: Python scripts (already built)
- Styling: Modern gradient UI, purple/blue theme

---

## 🔄 How the Lead Generation Pipeline Works

### Pipeline Architecture (3 Stages)

**STAGE 1: Google Maps Scraping**
- Script: `execution/optimized/pipeline_optimized.py` (calls `execution/n8n_gmaps_scraper_ai.py`)
- Input: Industry (e.g., "HVAC contractor"), Location (e.g., "New Jersey"), Target count (e.g., 10)
- Process:
  1. Uses AI (Llama 3.3 70B via OpenRouter) to generate nearby cities OR uses hardcoded cities for small hunts (<25 leads)
  2. Sends queries to N8N webhook: "HVAC contractor in Newark, NJ"
  3. N8N scrapes Google Maps for business listings
  4. Returns: business name, address, phone, website, email, ratings
- Time: ~30-40s for 10 leads
- Output: JSON array of raw business data

**STAGE 2: Decision Maker Email Finding (ASYNC)**
- Script: `execution/optimized/anymailfinder_decision_maker_async.py`
- Input: Array of businesses from Stage 1
- Process:
  1. Extracts domain from website URL
  2. Calls Anymailfinder API in parallel (10 concurrent requests)
  3. Finds CEO/owner email, name, job title, LinkedIn URL
  4. 15s timeout per request (optimized from 180s)
  5. Falls back to business email if CEO not found
- Time: ~15s for 10 leads (parallel processing)
- Cost: $0.04 per valid email found
- Output: Same array + `decision_maker` object added to each lead

**STAGE 3: LinkedIn Profile Discovery (ASYNC)**
- Script: `execution/optimized/find_linkedin_smart_async.py`
- Input: Array of businesses from Stage 2
- Process:
  1. Checks Anymailfinder response first (free)
  2. Parses website HTML for LinkedIn links (free)
  3. Uses DuckDuckGo search with 2 parallel strategies (free):
     - Strategy 1: "Full name + Job title + Company"
     - Strategy 2: "Full name + Company + Location"
  4. 0.5s delay between searches (rate limiting)
  5. Processes 5 leads concurrently
- Time: ~2-5s for 10 leads
- Cost: FREE (DuckDuckGo)
- Output: Same array + `linkedin_url` and `linkedin_source` added to decision_maker

**FINAL OUTPUT:**
```json
[
  {
    "name": "ABC HVAC Services",
    "address": "123 Main St, Newark, NJ 07102",
    "phone": "(973) 555-1234",
    "website": "abchvac.com",
    "email": "info@abchvac.com",
    "rating": 4.8,
    "user_ratings_total": 127,
    "decision_maker": {
      "email": "john@abchvac.com",
      "full_name": "John Smith",
      "job_title": "CEO",
      "linkedin_url": "https://linkedin.com/in/johnsmith",
      "status": "valid"
    }
  }
]
```

### Performance Metrics
- **Old pipeline:** 3-5 minutes for 10 leads
- **Optimized pipeline:** 50-60 seconds for 10 leads (3.5x faster)
- **With Redis caching:** 8-10 seconds for 10 leads (18-22x faster)

### Cost Structure
- Google Maps scraping: FREE (N8N webhook)
- AI city generation: FREE (Llama 3.3 70B via OpenRouter)
- Email finding: $0.04 per valid CEO email (Anymailfinder API)
- LinkedIn finding: FREE (DuckDuckGo search)
- **Average cost:** $0.40-$0.80 per 100 leads

---

## 🎨 Design Requirements

### Color Scheme & Branding
- Primary: Purple/Blue gradient (`from-purple-600 to-blue-600`)
- Accent: Cyan/Blue gradient (`from-cyan-500 to-blue-500`)
- Background: Dark mode with `bg-gray-950`, `bg-gray-900`
- Text: White/gray scale (`text-white`, `text-gray-400`)
- Cards: `bg-gray-900` with subtle borders `border-gray-800`
- Modern glass-morphism effects on key components

### Design Style
- Clean, minimal, professional
- Neumorphism/glass effects for cards
- Smooth animations and transitions
- Responsive (mobile-first)
- High contrast for readability

---

## 📱 Page Structure & UI Components

### Page 1: Dashboard (Landing Page)

**Route:** `/`

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Header: "LeadSnipe" logo + "Dashboard" + "New Hunt" button
├─────────────────────────────────────────────────┤
│                                                  │
│  Hero Section:                                   │
│  ┌─────────────────────────────────────────┐   │
│  │  🎯 Generate High-Quality B2B Leads      │   │
│  │                                           │   │
│  │  Find decision makers, emails, and       │   │
│  │  LinkedIn profiles in seconds            │   │
│  │                                           │   │
│  │  [Start New Hunt →]                      │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  Stats Cards (3 columns):                       │
│  ┌────────┐  ┌────────┐  ┌────────┐           │
│  │  Total  │  │ This   │  │ Avg    │           │
│  │  Leads  │  │ Week   │  │ Success│           │
│  │  1,247  │  │  156   │  │  73%   │           │
│  └────────┘  └────────┘  └────────┘           │
│                                                  │
│  Recent Hunts Table:                            │
│  ┌──────────────────────────────────────────┐  │
│  │ Date    Industry   Location  Leads  ⚙️   │  │
│  │─────────────────────────────────────────│  │
│  │ Jan 7   HVAC       NJ        10     ⋮   │  │
│  │ Jan 7   Tech       NY        10     ⋮   │  │
│  │ Jan 6   Dental     CA        25     ⋮   │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Components:**
1. **Header**
   - Logo: "LeadSnipe" with target icon
   - Nav: "Dashboard" | "New Hunt" button (purple gradient, prominent)

2. **Hero Section**
   - Large heading with gradient text
   - Subtitle describing the service
   - CTA button with gradient background and shadow

3. **Stats Cards**
   - 3 cards in a row (responsive to column on mobile)
   - Each card: icon, number (large), label
   - Gradient borders or backgrounds
   - Hover effect: lift + glow

4. **Recent Hunts Table**
   - Sortable columns: Date, Industry, Location, Lead Count
   - Action menu (⋮) per row: View, Download JSON, Delete
   - Empty state if no hunts yet
   - Click row to view hunt details

---

### Page 2: New Hunt (Lead Generation Form)

**Route:** `/hunt/new`

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Header: "← Back" + "New Lead Hunt"              │
├─────────────────────────────────────────────────┤
│                                                  │
│  Form Card (centered, max-w-2xl):               │
│  ┌─────────────────────────────────────────┐   │
│  │  🎯 Create New Lead Hunt                 │   │
│  │                                           │   │
│  │  Industry *                               │   │
│  │  [Text input with suggestions]            │   │
│  │  e.g., "HVAC contractor", "Dentist"       │   │
│  │                                           │   │
│  │  Location *                               │   │
│  │  [Text input with suggestions]            │   │
│  │  e.g., "New Jersey", "Phoenix area"       │   │
│  │                                           │   │
│  │  Number of Leads *                        │   │
│  │  [Slider: 10 - 100] Current: 25          │   │
│  │                                           │   │
│  │  Decision Maker Category                  │   │
│  │  [Dropdown: CEO, CFO, CTO, etc.]         │   │
│  │  Default: CEO                             │   │
│  │                                           │   │
│  │  ┌─────────────────────────────────┐    │   │
│  │  │ 📊 Estimated Cost: $1.00         │    │   │
│  │  │ ⏱️  Estimated Time: ~2 minutes   │    │   │
│  │  └─────────────────────────────────┘    │   │
│  │                                           │   │
│  │  [Cancel]  [Generate Leads →]            │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Components:**
1. **Form Fields**
   - Industry: Text input with autocomplete (HVAC, Plumber, Dentist, etc.)
   - Location: Text input with autocomplete (state names, city names)
   - Lead count: Slider with number display (10-100)
   - Category: Dropdown (CEO, CFO, CTO, CMO, etc.)

2. **Estimation Panel**
   - Calculates cost: `leads * 0.04 * 0.5` (50% success rate estimate)
   - Calculates time: `leads * 5` seconds
   - Updates in real-time as slider moves

3. **Buttons**
   - Cancel: Secondary style, returns to dashboard
   - Generate Leads: Primary gradient button, disables on submit

---

### Page 3: Hunt Progress (Real-time Status)

**Route:** `/hunt/[id]/progress`

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Header: "Lead Hunt in Progress"                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │  🎯 Generating 25 HVAC leads in NJ       │   │
│  │                                           │   │
│  │  Progress: ███████████░░░░░ 68%          │   │
│  │                                           │   │
│  │  Stage 1: Google Maps Scraping           │   │
│  │  ✅ Complete (28.3s)                      │   │
│  │  → Found 25 businesses                    │   │
│  │                                           │   │
│  │  Stage 2: Finding Decision Makers        │   │
│  │  🔄 In Progress... (17/25 processed)      │   │
│  │  → 9 CEOs found, 8 using business email  │   │
│  │                                           │   │
│  │  Stage 3: LinkedIn Discovery              │   │
│  │  ⏳ Pending                               │   │
│  │                                           │   │
│  │  ⏱️  Elapsed: 45s / ~2m estimated         │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  Live Activity Feed:                            │
│  ┌─────────────────────────────────────────┐   │
│  │ [15:45:23] ✅ Found CEO: John Smith      │   │
│  │ [15:45:22] 🔍 Searching: ABC Corp...     │   │
│  │ [15:45:20] ✅ Scraped: 123 Main St       │   │
│  │ [15:45:18] 🔄 Stage 2 started            │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Components:**
1. **Progress Card**
   - Hunt details (industry, location, count)
   - Overall progress bar with percentage
   - 3 stage indicators: ✅ Complete, 🔄 In Progress, ⏳ Pending
   - Stage details: time taken, results found
   - Elapsed time vs estimated time

2. **Live Activity Feed**
   - Scrollable log of real-time events
   - Auto-scrolls to bottom
   - Color-coded by event type (success=green, info=blue, error=red)

3. **Completion State**
   - When done, show success message
   - Button: "View Results →" (navigates to results page)

---

### Page 4: Hunt Results (Lead List & Export)

**Route:** `/hunt/[id]/results`

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Header: "← Hunts" + "HVAC in NJ - 25 Leads"    │
│  Actions: [Download JSON] [Download CSV] [⋮]     │
├─────────────────────────────────────────────────┤
│                                                  │
│  Summary Stats (4 cards):                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ Total │ │ CEOs │ │LinkedIn│ │ Cost │          │
│  │  25   │ │  18  │ │   15   │ │$0.72 │          │
│  └──────┘ └──────┘ └──────┘ └──────┘          │
│                                                  │
│  Filters:                                        │
│  [Has CEO Email ✓] [Has LinkedIn ✓] [Search...] │
│                                                  │
│  Lead Cards (List View):                        │
│  ┌─────────────────────────────────────────┐   │
│  │ 🏢 ABC HVAC Services                     │   │
│  │ 📍 123 Main St, Newark, NJ               │   │
│  │ ⭐ 4.8 (127 reviews)                      │   │
│  │                                           │   │
│  │ 👤 John Smith - CEO                       │   │
│  │ 📧 john@abchvac.com                       │   │
│  │ 💼 linkedin.com/in/johnsmith              │   │
│  │ 📱 (973) 555-1234                         │   │
│  │ 🌐 abchvac.com                            │   │
│  │                                           │   │
│  │ [Copy Email] [View LinkedIn] [Select]    │   │
│  └─────────────────────────────────────────┘   │
│  ... (24 more cards)                            │
│                                                  │
│  Bulk Actions:                                   │
│  [Select All] [Export Selected (0)]             │
└─────────────────────────────────────────────────┘
```

**Components:**
1. **Header Actions**
   - Download JSON: Full data export
   - Download CSV: Spreadsheet format
   - More menu: Delete hunt, Re-run, Share

2. **Summary Stats**
   - Total leads found
   - Leads with CEO email
   - Leads with LinkedIn
   - Total cost incurred

3. **Filters**
   - Toggle: Has CEO Email
   - Toggle: Has LinkedIn
   - Search bar: Filter by name/location

4. **Lead Cards**
   - Business info: name, address, rating
   - Decision maker: name, title, email, LinkedIn
   - Contact: phone, website
   - Actions: Copy email, Visit LinkedIn, Select for export

5. **Bulk Actions**
   - Multi-select with checkboxes
   - Export selected leads

---

## 🔌 Backend Integration

### API Endpoints (You'll Create These)

**1. POST `/api/hunt/create`**
```json
Request:
{
  "industry": "HVAC contractor",
  "location": "New Jersey",
  "target": 25,
  "category": "ceo"
}

Response:
{
  "hunt_id": "hunt_20260107_153045_a1b2c3",
  "status": "running",
  "created_at": "2026-01-07T15:30:45Z"
}
```

Implementation:
- Spawns Python pipeline: `python3 execution/optimized/pipeline_optimized.py --industry "..." --location "..." --target 25`
- Runs in background
- Returns hunt ID immediately
- Streams progress updates via WebSocket or Server-Sent Events

**2. GET `/api/hunt/[id]/status`**
```json
Response:
{
  "hunt_id": "hunt_20260107_153045_a1b2c3",
  "status": "running", // "running", "completed", "failed"
  "progress": {
    "stage": 2,
    "stage_name": "Finding Decision Makers",
    "percentage": 68,
    "processed": 17,
    "total": 25,
    "elapsed_time": 45,
    "estimated_total": 120
  },
  "stats": {
    "total_leads": 25,
    "ceos_found": 9,
    "linkedin_found": 0
  }
}
```

**3. GET `/api/hunt/[id]/results`**
```json
Response:
{
  "hunt_id": "hunt_20260107_153045_a1b2c3",
  "industry": "HVAC contractor",
  "location": "New Jersey",
  "created_at": "2026-01-07T15:30:45Z",
  "completed_at": "2026-01-07T15:32:30Z",
  "performance": {
    "total_time": 105,
    "stage1_time": 33,
    "stage2_time": 62,
    "stage3_time": 10
  },
  "stats": {
    "total": 25,
    "with_email": 25,
    "with_ceo_email": 18,
    "with_linkedin": 15,
    "cost": 0.72
  },
  "leads": [
    {
      "name": "ABC HVAC Services",
      "address": "123 Main St, Newark, NJ 07102",
      "phone": "(973) 555-1234",
      "website": "abchvac.com",
      "email": "info@abchvac.com",
      "rating": 4.8,
      "user_ratings_total": 127,
      "decision_maker": {
        "email": "john@abchvac.com",
        "full_name": "John Smith",
        "job_title": "CEO",
        "linkedin_url": "https://linkedin.com/in/johnsmith",
        "status": "valid"
      }
    }
  ]
}
```

**4. GET `/api/hunts`**
```json
Response:
{
  "hunts": [
    {
      "hunt_id": "hunt_20260107_153045_a1b2c3",
      "industry": "HVAC contractor",
      "location": "New Jersey",
      "target": 25,
      "status": "completed",
      "created_at": "2026-01-07T15:30:45Z",
      "total_leads": 25,
      "cost": 0.72
    }
  ]
}
```

**5. DELETE `/api/hunt/[id]`**
- Deletes hunt and associated files

**6. GET `/api/hunt/[id]/export`**
- Query params: `?format=json|csv`
- Returns file download

---

## 🎬 User Flow

1. User lands on Dashboard
2. Clicks "Start New Hunt" or "New Hunt" button
3. Fills out form (industry, location, count, category)
4. Clicks "Generate Leads"
5. Redirected to Progress page
6. Watches real-time progress (3 stages)
7. When complete, clicks "View Results"
8. Reviews leads in card view
9. Filters/searches leads
10. Downloads JSON or CSV
11. Returns to Dashboard to see hunt in history

---

## 🛠️ Technical Implementation Notes

### Backend Python Integration

**Option 1: Spawn Python Process (Simplest)**
```typescript
// In your API route
import { spawn } from 'child_process';

export async function POST(req: Request) {
  const { industry, location, target, category } = await req.json();

  const python = spawn('python3', [
    'execution/optimized/pipeline_optimized.py',
    '--industry', industry,
    '--location', location,
    '--target', target.toString(),
    '--output', `.tmp/hunt_${huntId}.json`
  ]);

  python.stdout.on('data', (data) => {
    // Parse progress and send via WebSocket
  });

  python.on('close', (code) => {
    // Mark hunt as completed
  });
}
```

**Option 2: Use Next.js API Routes + Background Jobs**
- Use `better-sqlite3` to store hunt metadata
- Use WebSockets or Server-Sent Events for real-time updates
- Parse Python stdout for progress updates

### Real-time Progress Updates

Use **Server-Sent Events (SSE)** for simplicity:

```typescript
// app/api/hunt/[id]/stream/route.ts
export async function GET(req: Request) {
  const stream = new ReadableStream({
    start(controller) {
      // Stream Python stdout as SSE events
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache'
    }
  });
}
```

### Data Persistence

**Option 1: File System (Current)**
- Store hunt results in `.tmp/hunt_[id].json`
- Store hunt metadata in `.tmp/hunts_metadata.json`

**Option 2: SQLite (Better)**
- Create `leadsnipe.db` with tables:
  - `hunts`: hunt_id, industry, location, target, status, created_at, completed_at
  - `leads`: lead_id, hunt_id, name, address, phone, email, decision_maker (JSON)

---

## 🎨 UI/UX Details

### Animations
- Page transitions: Fade in
- Card hover: Lift (translateY -2px) + shadow
- Button hover: Scale 1.02 + brightness increase
- Progress bar: Smooth width animation
- Loading states: Skeleton loaders, not spinners

### Typography
- Headings: `font-bold` with gradient text
- Body: `text-gray-300` for readability
- Labels: `text-gray-400 text-sm`

### Spacing
- Consistent padding: p-6 for cards, p-8 for sections
- Gap between elements: gap-4 or gap-6
- Max width: max-w-7xl for dashboard, max-w-2xl for forms

### Responsive Design
- Mobile: Single column, full-width cards
- Tablet: 2 columns for stats, responsive table
- Desktop: 3-4 columns, full table layout

### Icons
Use **Lucide React** icons:
- Target for LeadSnipe logo
- TrendingUp for stats
- Search for filters
- Download for exports
- Mail, Phone, Globe, Linkedin for contact info

---

## 📦 File Structure

```
leadsnipe-frontend/
├── app/
│   ├── page.tsx                    # Dashboard
│   ├── hunt/
│   │   ├── new/
│   │   │   └── page.tsx            # New Hunt Form
│   │   └── [id]/
│   │       ├── progress/
│   │       │   └── page.tsx        # Progress View
│   │       └── results/
│   │           └── page.tsx        # Results View
│   ├── api/
│   │   └── hunt/
│   │       ├── create/
│   │       │   └── route.ts        # POST create hunt
│   │       ├── [id]/
│   │       │   ├── status/
│   │       │   │   └── route.ts    # GET status
│   │       │   ├── results/
│   │       │   │   └── route.ts    # GET results
│   │       │   ├── stream/
│   │       │   │   └── route.ts    # SSE stream
│   │       │   └── route.ts        # DELETE hunt
│   │       └── route.ts            # GET all hunts
│   ├── layout.tsx                  # Root layout
│   └── globals.css                 # Tailwind styles
├── components/
│   ├── ui/                         # shadcn/ui components
│   ├── HuntCard.tsx
│   ├── LeadCard.tsx
│   ├── ProgressTracker.tsx
│   └── StatsCard.tsx
├── lib/
│   ├── python-runner.ts            # Python process manager
│   ├── db.ts                       # Database helpers
│   └── utils.ts
└── public/
    └── logo.svg
```

---

## 🚀 Getting Started Code

**Installation:**
```bash
npx create-next-app@latest leadsnipe-frontend --typescript --tailwind --app
cd leadsnipe-frontend
npm install lucide-react date-fns
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input slider select
```

**Key Dependencies:**
- `next`: 14.x
- `react`: 18.x
- `typescript`: 5.x
- `tailwindcss`: 3.x
- `lucide-react`: Icons
- `date-fns`: Date formatting
- `shadcn/ui`: UI components

---

## ✅ Deliverables

Build a complete Next.js application with:

1. ✅ 4 pages (Dashboard, New Hunt, Progress, Results)
2. ✅ 6 API routes (create, status, results, stream, delete, list)
3. ✅ Python backend integration via child_process
4. ✅ Real-time progress updates via SSE
5. ✅ Modern purple/blue gradient UI
6. ✅ Responsive design (mobile, tablet, desktop)
7. ✅ Export functionality (JSON, CSV)
8. ✅ Animations and smooth transitions
9. ✅ Error handling and loading states
10. ✅ Clean, maintainable TypeScript code

---

## 🎯 Success Criteria

The app should:
- ✅ Launch a hunt in <3 clicks
- ✅ Show real-time progress (stages, percentage, live feed)
- ✅ Display results in clean, scannable cards
- ✅ Allow filtering and exporting leads
- ✅ Work flawlessly on mobile and desktop
- ✅ Have smooth, professional animations
- ✅ Match the modern gradient aesthetic
- ✅ Be production-ready and deployable

---

Start by building the Dashboard page, then the New Hunt form, then wire up the Python backend integration. Focus on making it beautiful, fast, and intuitive. Use the latest Next.js 14 App Router patterns and modern React best practices.

Let me know if you need any clarification on how the pipeline works or any design details!
