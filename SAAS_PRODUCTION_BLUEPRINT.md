# LeadSnipe SaaS Production Blueprint 💎

This blueprint provides the exact architectural and feature path to transform the LeadSnipe prototype into a commercial SaaS web application.

## 1. Core Technology Stack (The Scaling Foundation)
To handle multiple users and high-volume scraping, we must transition to a production-grade stack:

*   **Framework:** **Next.js 14+ (App Router)** - Standard for modern SaaS. Handles SEO, Server Components, and API routes in one place.
*   **Database:** **Supabase (PostgreSQL)** - Provides real-time data, high-performance querying, and easy user-data isolation.
*   **Auth:** **Clerk** or **Supabase Auth** - Handles SSO (Google/LinkedIn), session management, and user profiles out of the box.
*   **Task Queue:** **BullMQ (with Redis)** - CRITICAL. Scraping takes time. We can't let the browser "wait" for the API. BullMQ will handle hunts in the background and notify the user when done.
*   **Storage:** **AWS S3** or **Supabase Storage** - For storing raw scrape JSONs and exported CSVs.

---

## 2. The "Web App" UI/UX Transition
We are moving from a **Mobile Phone Frame** to a **Wide-Canvas Desktop Experience**.

### ⚡ Key UI Components to Build:
1.  **Sidebar Navigation:** Dashboard, My Hunts, Lead Database, Settings, Billing.
2.  **The "Hunt Command Center":** A wide-area dashboard where users can orchestrate multiple hunts at once.
3.  **Lead Data-Grid:** A powerful table with:
    *   Inline editing.
    *   Status filtering (Cold, Warm, Contacted).
    *   Bulk actions (Select all -> Export, Select all -> AI Generate).
4.  **Real-Time Console Drawer:** A slide-out panel that shows the 1s and 0s of what the AI is doing (restoring that "hacker" feel from the mobile logs).

---

## 3. The Backend "Formula" (Preserving the Secret Sauce)
Your current "Formula" works: **Scrape -> Find Owner -> Get Email -> Generate Outreach**. We will scale it:

*   **Distributed Scraper:** Wrap your Python scripts in a Docker container. When a user starts a hunt, we spin up/trigger a worker.
*   **AI Enrichment Engine:** A dedicated microservice that handles OpenRouter/OpenAI calls for finding owners and personalized writing.
*   **Email Verification Proxy:** A rotation system to ensure email verification doesn't get rate-limited.

---

## 4. SaaS Infrastructure (The "Money" Layers)
These are the non-negotiable features for a paid product:

### A. Stripe Monetization
*   **Free Tier:** 10 leads/month (Teaser).
*   **Starter ($49/mo):** 500 leads, AI owner finding.
*   **Pro ($149/mo):** 2000 leads, LinkedIn Snoop, Unlimited outreach drafts.
*   **Agency ($499/mo):** API access, White-label exports, Team seats.

### B. Usage Metering
*   Implement a "Credit" system. Every successful lead found consumes 1 credit.
*   Real-time usage bar in the UI.

### C. Multi-Tenancy (Security)
*   **Row-Level Security (RLS):** Ensure User A can *never* see User B's leads.
*   **API Keys:** Allow users to connect LeadSnipe to their own CRMs (Zapier/Make integration).

---

## 5. Development Roadmap (Phased Approach)

### Phase 1: The Next.js Shell (Week 1-2)
*   Setup Next.js, Tailwind, and Supabase.
*   Migrate the "Premium Minimal" HTML/CSS components into React components.
*   Build the Desktop Sidebar and Layout.

### Phase 2: The Queue System (Week 3)
*   Setup Redis and BullMQ.
*   Build the bridge between Next.js and your Python Python Scrapers (`leadsnipe_api.py` refactor).
*   Implement real-time updates via WebSockets (Socket.io).

### Phase 3: The Data Vault (Week 4)
*   Build the "Lead Database" view.
*   Implement filtering, sorting, and CSV exports.

### Phase 4: Billing & Launch (Week 5)
*   Stripe checkout integration.
*   Closed Beta launch to 10-20 users.

---

## 🚀 Immediate Built-In Features User Wants:
1.  **Chrome Extension:** (Phase 2 byproduct) To scrape leads directly while browsing.
2.  **Gmail/SMTP Integration:** Let users send the generated outreach directly from the app.
3.  **CRM Sync:** "One-click send to Hubspot/GoHighLevel".

**Ready to start the transformation? I can begin by generating the Next.js scaffold or refactoring the current backend into a production-style API.**
