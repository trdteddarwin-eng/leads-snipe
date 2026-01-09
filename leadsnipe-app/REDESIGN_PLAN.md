# LeadSnipe Dashboard Redesign Plan
## Dark Mode → Light "Sales Overview" Style

---

## 🎯 OBJECTIVE
Transform the current dark-themed dashboard into a light, clean "Sales Overview" style matching the reference image, while **preserving all existing logic, state, and data connections**.

---

## 📋 STRICT PRESERVATION RULES

### ✅ MUST PRESERVE (DO NOT TOUCH):
- All `useState` hooks: `hunts`, `loading`, `stats`
- All `useEffect` hooks and data fetching logic
- All API endpoints: `/api/hunts`, `/api/hunt/${huntId}`
- All variable names: `totalLeads`, `thisWeek`, `avgSuccess`, `recentHunts`
- All functions: `fetchData()`, `handleDeleteHunt()`
- All data display: Show REAL data, not mock data
- All existing components: `StatsCard`, `HuntTable`, etc.

### 🎨 WILL CHANGE (VISUAL ONLY):
- Background colors: Dark → Light
- Card styling: Dark cards → White cards
- Text colors: White text → Dark text
- Borders and shadows
- Layout structure to add sidebar
- Overall color scheme

---

## 🎨 DESIGN TRANSFORMATION BREAKDOWN

### 1. **Color Palette Change**

**Current (Dark Mode):**
```css
--color-void: #030308          /* Main background */
--color-surface: #12121f       /* Cards */
--color-text-primary: #f0f0f5  /* White text */
--color-text-secondary: #a0a0b5 /* Gray text */
```

**New (Light Mode):**
```css
--color-bg-base: #F3F4F6       /* Light gray background (like reference) */
--color-bg-white: #FFFFFF      /* Pure white for cards */
--color-text-primary: #1F2937  /* Dark gray for main text */
--color-text-secondary: #6B7280 /* Medium gray for secondary text */
--color-text-muted: #9CA3AF    /* Light gray for muted text */
```

**Brand Colors (KEEP SAME):**
```css
--color-brand-blue: #3B82F6    /* Primary blue from reference */
--color-accent-blue: #DBEAFE  /* Light blue background for active states */
--color-success-green: #10B981 /* Green for positive percentages */
```

---

### 2. **Layout Structure Changes**

#### **Current Layout:**
```
┌──────────────────────────────────────┐
│ Header (top, dark)                   │
├──────────────────────────────────────┤
│                                      │
│  Hero Section (gradient effects)     │
│  - Large headline                    │
│  - CTA buttons                       │
│                                      │
│  Stats Section (3 cards)             │
│  - Total Leads                       │
│  - This Week                         │
│  - Avg Success                       │
│                                      │
│  Recent Hunts Table                  │
│                                      │
└──────────────────────────────────────┘
```

#### **New Layout (Reference Style):**
```
┌────────┬─────────────────────────────────┐
│        │ Search Bar + Dark Mode Toggle   │
│ SIDE   ├─────────────────────────────────┤
│ BAR    │ Sales Overview                  │
│        │ Welcome back, Sarah.            │
│ Logo   │                                 │
│ Nav    │ ┌────┐ ┌────┐ ┌────┐ ┌────┐   │
│ Items  │ │Stat│ │Stat│ │Stat│ │Stat│   │
│        │ │Card│ │Card│ │Card│ │Card│   │
│ Upgrade│ └────┘ └────┘ └────┘ └────┘   │
│ Card   │                                 │
│        │ Recent Hunts Table              │
│        │ (inside white card container)   │
└────────┴─────────────────────────────────┘
```

---

### 3. **Component-by-Component Changes**

#### **A. Root Layout (`layout.tsx`)**

**Changes:**
1. Remove dark mode class: `className="dark"` → `className="light"`
2. Change background: `bg-[var(--color-void)]` → `bg-[var(--color-bg-base)]`
3. Remove scanline overlay (dark theme effect)
4. Remove grid background overlay
5. Remove gradient blur effects
6. Keep fonts unchanged
7. **ADD**: Sidebar component to layout

**Preserved:**
- All font definitions
- All metadata
- Header component (will restyle separately)

---

#### **B. Dashboard Page (`page.tsx`)**

**Section 1: Remove Hero Section**
- **Delete**: Lines 73-142 (entire hero section with "Generate High-Quality B2B Leads")
- **Why**: Reference style has clean header with greeting, no hero

**Section 2: Add Page Header**
- **Add**: New greeting header section
  ```tsx
  <div className="mb-6">
    <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
      Sales Overview
    </h1>
    <p className="text-sm text-[var(--color-text-secondary)]">
      Welcome back, Sarah. Here's what's happening today.
    </p>
  </div>
  ```

**Section 3: Stats Cards Row**
- **Keep**: All 3 stats cards (totalLeads, thisWeek, avgSuccess)
- **Add**: 4th dummy card for visual balance (like reference)
- **Change**: Card styling to match reference
  - White background: `bg-white`
  - Soft shadow: `shadow-sm`
  - Rounded corners: `rounded-2xl`
  - Icon style: Circular colored background
  - Green percentage badges: `bg-green-100 text-green-600`

**Current Stats:**
```tsx
<StatsCard title="Total Leads Generated" value={stats.totalLeads} />
<StatsCard title="This Week" value={stats.thisWeek} />
<StatsCard title="Avg Success Rate" value={`${stats.avgSuccess}%`} />
```

**Keep Same Data, Restyle Cards:**
- Map `totalLeads` → "Total Leads" card (users icon)
- Map `thisWeek` → "Qualified" card (target icon)
- Map `avgSuccess` → "Avg. Score" card (trending icon)
- Add 4th card: "Conversion" with dummy 24% (sparkles icon)

**Section 4: Recent Hunts Table**
- **Keep**: All `hunts` data, `handleDeleteHunt` function
- **Change**: Wrap in large white card (like "Acquisition Flow" in reference)
- **Change**: Table styling to light mode
  - White background
  - Light gray borders
  - Generous padding
  - Remove dark grid lines

**Preserved Logic:**
```tsx
const [hunts, setHunts] = useState<Hunt[]>([]);
useEffect(() => {
  async function fetchData() {
    const response = await fetch('/api/hunts');
    // ... (ALL LOGIC UNCHANGED)
  }
}, []);
```

---

#### **C. Sidebar Component (NEW)**

**Location**: `/src/components/Sidebar.tsx`

**Structure:**
```tsx
┌─────────────────────┐
│ 🎯 LeadSnipe        │ ← Logo + title
│   B2B INTELLIGENCE  │
├─────────────────────┤
│ 📊 Overview (ACTIVE)│ ← Nav items
│ 👥 Leads            │
│ 📈 Analytics        │
│ ⚙️  Settings        │
├─────────────────────┤
│ ╔═════════════════╗ │
│ ║ UPGRADE PLAN    ║ │ ← Blue card
│ ║ Snipe Premium   ║ │
│ ║ [Get 2x Credits]║ │
│ ╚═════════════════╝ │
└─────────────────────┘
```

**Styling:**
- Background: White (`bg-white`)
- Width: Fixed 240px
- Height: Full viewport
- Active state: Light blue background (`bg-blue-50`)
- Active text: Blue (`text-blue-600`)
- Inactive text: Gray (`text-gray-600`)

**Links (Match Reference Exactly):**
1. Overview (active) → `/` (current page)
2. Leads → `/hunt/new` (existing route)
3. Analytics → `/analytics` (dummy for now)
4. Settings → `/settings` (dummy for now)

---

#### **D. Header Component (`Header.tsx`)**

**Changes:**
1. Move to right side of layout (next to sidebar)
2. Add search bar (left side)
3. Add dark mode toggle (right side)
4. Remove purple gradient background → white background
5. Remove "New Hunt" button from header (it's in sidebar now)

**New Structure:**
```
┌──────────────────────────────────────────────┐
│ [🔍 Search leads, companies...]  🌙 🔔 👤   │
└──────────────────────────────────────────────┘
```

---

### 4. **Component Styling Changes**

#### **StatsCard Component**

**Current Style (Dark):**
```tsx
<div className="bg-[var(--color-surface)] border border-[var(--color-border)] p-6 rounded-xl">
  <Icon className="text-purple-500" />
  <div className="text-4xl font-bold text-white">{value}</div>
  <div className="text-sm text-gray-400">{title}</div>
</div>
```

**New Style (Light):**
```tsx
<div className="bg-white p-6 rounded-2xl shadow-sm">
  <div className="flex items-center justify-between mb-4">
    <div className="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center">
      <Icon className="w-6 h-6 text-blue-600" />
    </div>
    {trend && (
      <span className="text-xs font-medium bg-green-100 text-green-600 px-2 py-1 rounded-full">
        +{trend}%
      </span>
    )}
  </div>
  <div className="text-3xl font-bold text-gray-900">{value}</div>
  <div className="text-sm text-gray-600 mt-1">{title}</div>
</div>
```

---

#### **HuntTable Component**

**Current Style (Dark):**
```tsx
<div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden">
  <table className="w-full text-white">
    {/* Dark table rows */}
  </table>
</div>
```

**New Style (Light):**
```tsx
<div className="bg-white rounded-2xl shadow-sm p-6">
  <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Hunts</h3>
  <table className="w-full">
    <thead className="border-b border-gray-200">
      <tr className="text-left text-xs font-medium text-gray-500 uppercase">
        {/* Headers */}
      </tr>
    </thead>
    <tbody className="divide-y divide-gray-100">
      <tr className="hover:bg-gray-50 transition-colors">
        {/* Light rows */}
      </tr>
    </tbody>
  </table>
</div>
```

---

### 5. **CSS Variables Update** (`globals.css`)

**Add Light Mode Variables:**
```css
@theme inline {
  /* Light Mode Colors */
  --color-bg-base: #F3F4F6;
  --color-bg-white: #FFFFFF;
  --color-text-primary: #1F2937;
  --color-text-secondary: #6B7280;
  --color-text-muted: #9CA3AF;

  /* Borders & Dividers */
  --color-border-light: #E5E7EB;
  --color-border: #D1D5DB;

  /* Brand Colors (unchanged) */
  --color-brand-blue: #3B82F6;
  --color-accent-blue-light: #DBEAFE;
  --color-accent-blue-dark: #1E40AF;

  /* Status Colors */
  --color-success-bg: #D1FAE5;
  --color-success-text: #065F46;
  --color-success-border: #10B981;
}
```

**Remove Dark Mode Effects:**
- Delete `.scanlines` styles
- Delete `.grid-bg` pattern
- Keep `.gradient-text` (still useful)

---

## 📊 BEFORE & AFTER DATA MAPPING

| Current Variable | Reference Element | New Display |
|-----------------|-------------------|-------------|
| `stats.totalLeads` | "Total Leads" card | Users icon, show actual number |
| `stats.thisWeek` | "Qualified" card | Target icon, show actual number |
| `stats.avgSuccess` | "Avg. Score" card | Trending icon, show percentage |
| (new) | "Conversion" card | Sparkles icon, dummy 24% |
| `hunts` array | Recent Hunts table | Show in white card container |

---

## 🚫 WHAT WE'RE NOT DOING

1. ❌ Adding acquisition flow chart (reference has it, we keep our table)
2. ❌ Adding top industries chart (not in our data model)
3. ❌ Changing API structure
4. ❌ Renaming variables
5. ❌ Adding mock/static data
6. ❌ Changing the hunt creation flow
7. ❌ Modifying backend Python scripts

---

## ✅ FILES THAT WILL BE MODIFIED

1. **`src/app/globals.css`** - Add light mode colors, remove dark effects
2. **`src/app/layout.tsx`** - Add sidebar, change root bg color
3. **`src/app/page.tsx`** - Remove hero, add greeting, restyle stats/table
4. **`src/components/Sidebar.tsx`** - NEW FILE - Create sidebar
5. **`src/components/Header.tsx`** - Simplify, add search bar
6. **`src/components/StatsCard.tsx`** - Restyle to match reference cards
7. **`src/components/HuntTable.tsx`** - Restyle to light mode table

---

## 🎯 SUCCESS CRITERIA

After implementation, the app will:

✅ Have light gray background (#F3F4F6) instead of black
✅ Have white cards with soft shadows
✅ Have left sidebar with logo, nav, and upgrade card
✅ Show "Sales Overview" greeting at top
✅ Display 4 stat cards in a row (using REAL data for 3 of them)
✅ Show Recent Hunts table in white card container
✅ Use dark text on light backgrounds
✅ Have blue accent colors matching reference
✅ **Still fetch real data from `/api/hunts`**
✅ **Still show actual hunt data in table**
✅ **Still allow deleting hunts**
✅ **All functionality preserved 100%**

---

## 📝 IMPLEMENTATION ORDER

1. Update `globals.css` with light mode colors
2. Create `Sidebar.tsx` component
3. Update `layout.tsx` to add sidebar and change background
4. Simplify `Header.tsx` (add search, remove hero elements)
5. Update `page.tsx` (remove hero, add greeting, restyle)
6. Update `StatsCard.tsx` styling
7. Update `HuntTable.tsx` styling
8. Test that all data still loads correctly

---

## 🔍 VERIFICATION CHECKLIST

Before marking complete:

- [ ] Can still create new hunt via "New Hunt" button
- [ ] Dashboard still fetches hunts from API
- [ ] Stats still calculate from real data
- [ ] Can still delete hunts
- [ ] All links work
- [ ] Visual design matches reference (light, clean, sidebar)
- [ ] No console errors
- [ ] Responsive on mobile (sidebar collapses)

---

**READY TO PROCEED?** Confirm this plan, then I'll implement all changes.
