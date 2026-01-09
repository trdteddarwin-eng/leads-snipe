# LeadSnipe SaaS Transformation Plan 🚀

This document outlines the roadmap to transition **LeadSnipe** from a local mobile-style prototype into a fully scalable Software-as-a-Service (SaaS) platform.

## 1. Vision & Architecture Upgrade
We will move from a "phone-in-browser" layout to a standard **Desktop-First SaaS Dashboard** while preserving the current "Apple-Minimalist" aesthetic.

### Current vs. Future Stack
| Component | Current (Prototype) | SaaS (Production) |
| :--- | :--- | :--- |
| **Frontend** | Vanilla HTML/JS (Mobile Frame) | **Next.js** (Desktop Responsive) |
| **Styling** | Custom CSS | **Tailwind CSS + Headless UI** |
| **Backend** | FastAPI (Direct Threads) | **FastAPI + Celery/Redis** (Task Queues) |
| **Database** | SQLite | **PostgreSQL (Supabase)** |
| **Auth** | Firebase Client-side | **Firebase/Clerk** (Server-side session management) |
| **Payments** | None | **Stripe (Subscriptions)** |

---

## 2. Phase 1: The SaaS Shell (UI/UX)
**Goal:** Create the desktop dashboard structure.
- [ ] **Next.js Migration:** Componentize the existing `dashboard.html` logic.
- [ ] **Sidebar Layout:** Implement a persistent sidebar (Hunts, Leads, Campaigns, Settings).
- [ ] **Responsive Content:** Replace the `.phone-frame` with a fluid container that works on any screen size.
- [ ] **Modern Tables:** Upgrade the "Recent Campaigns" into a full-featured datagrid with sorting and filtering.

## 3. Phase 2: Scalable Execution Engine
**Goal:** Handle hundreds of concurrent hunt requests without crashing the server.
- [ ] **Task Queue (Redis):** Instead of `threading.Thread`, move scraper execution to **Celery**. This allows the API to remain responsive while workers handle compute-heavy tasks.
- [ ] **Database Migration:** Move all hunt persistence to **PostgreSQL**.
- [ ] **Websocket Update:** Replace/Reinforce SSE with WebSockets for more robust real-time log streaming.

## 4. Phase 3: Monetization & Limits
**Goal:** Turn LeadSnipe into a business.
- [ ] **Stripe Integration:** Add "Pricing" tiers (Basic, Pro, Agency).
- [ ] **Usage Credit System:**
    - Basic: 50 Leads/month.
    - Pro: 1000 Leads/month + AI Owner Finding.
    - Agency: Unlimited + Team access.
- [ ] **Middleware:** Add server-side logic to check user credits before starting a hunt.

## 5. Phase 4: CRM & Export Features
**Goal:** Make the leads actionable.
- [ ] **Lead CRM:** Allow users to move leads between stages (Contacted, Replied, Closed).
- [ ] **Bulk Actions:** Select 500 leads and export to CSV or send to CRM (Hubspot/Salesforce).
- [ ] **AI Outreach 2.0:** More templates and personalized AI video/voice integration hooks.

---

## 6. Immediate Next Steps (The "Quick Win")
To get moving immediately, we will:
1. **Initialize a Next.js project** in a new directory or refactor the current one.
2. **Standardize the API:** Move `leadsnipe_api.py` to a proper environment with a `.env` file and PostgreSQL connection.
3. **Desktop Layout:** Build the first "SaaS Style" navigation bar and greeting area.

---

**Would you like me to start by initializing the Next.js foundation or should we first migrate the backend to support multiple users properly?**
