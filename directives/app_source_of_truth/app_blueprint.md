# 🎯 LeadSnipe: The Decision Maker Outreach App

## 📝 Core Mission
To provide a specialized, high-converting outreach platform that bypasses "gatekeepers" by identifying the **Decision Maker** (Owner, CEO, Founder) of local businesses and providing a direct line to them via **AI-Personalized Outreach**.

---

## 🏗️ System Architecture (The "Decision Maker" Engine)

LeadSnipe operates on a robust API-first architecture connecting a sleek monochrome frontend to a deterministic Python pipeline.

### 1. Frontend (UI/UX)
*   **Design Language:** Apple-inspired, minimalist, monochrome (Black & White).
*   **Navigation:** Linear wizard flow (Target -> Location -> Refine -> Launch).
*   **State Management:** `localStorage` for cross-page data persistence.

### 2. API Layer (`execution/leadsnipe_api.py`)
*   **Framework:** FastAPI.
*   **Core Endpoints:**
    *   `POST /api/hunt`: Initiates a background hunt process.
    *   `GET /api/hunt/{id}/status`: Polls real-time progress of the active hunt.
    *   `GET /api/leads`: Retrieves the final enriched lead list.
*   **Orchestration:** Spawns a background thread to execute the sequential Python pipeline.

### 3. Backend Pipeline (The "Hunt")
Executed sequentially via subprocess:
1.  **Phase 1: Scrape** (`n8n_gmaps_scraper.py`) -> Google Maps raw lead capture.
2.  **Phase 2: Snoop** (`find_owner_linkedin.py`) -> Identifies Owner Name & LinkedIn.
3.  **Phase 3: Unlock** (`anymailfinder_email.py`) -> Extracts verified direct emails.
4.  **Phase 4: Hook** (`generate_outreach_emails.py`) -> AI script generation & Gmail draft creation.

---

## 🛠️ Key Functions & Workflow

### 1. Lead Discovery (The Hunt)
*   **Function:** Users input a `Niche` and `Location`.
*   **Outcome:** Raw business lead capture.

### 2. Decision Maker Identification (The Snoop)
*   **Function:** Website deep-crawling and LinkedIn X-Ray searching.
*   **Outcome:** Full identity of the business owner.

### 3. Contact Enrichment (The Unlock)
*   **Function:** Anymailfinder integration for direct email verification.
*   **Outcome:** Skip-tracing the "Gatekeeper" to reach the owner directly.

### 4. AI Outreach (The Hook)
*   **Function:** OpenRouter AI review analysis and script writing.
*   **Outcome:** Personalized Gmail Drafts or SMS scripts.

---

## 📱 App UI Structure (Monochrome Pages)

| Screen | File | Primary Action |
| :--- | :--- | :--- |
| **Home Screen** | `leadsnipe_homescreen_minimal.html` | Branding intro & "Start the Hunt" entry. |
| **Step 1: Niche** | `leadsnipe_wizard_step1.html` | Selecting business category. |
| **Step 2: Location** | `leadsnipe_wizard_step2.html` | Defining geographic search area. |
| **Step 3: Refine** | `leadsnipe_wizard_step3.html` | Toggle Enrichment (Owner Snoop + Email Unlock). |
| **Step 4: Review** | `leadsnipe_wizard_step4.html` | Final summary & API Launch trigger. |
| **Radar Screen** | `leadsnipe_processing.html` | Real-time API status polling animation. |
| **Results List** | `leadsnipe_results_list.html` | Browsing real discovered Decision Makers. |
| **Lead Detail** | `leadsnipe_lead_detail.html` | AI Script view & Gmail draft generation. |

---

## ⚙️ Environment & Requirements
*   **API Tokens:** Requires `.env` with `APIFY_API_TOKEN`, `OPENROUTER_API_KEY`, `ANYMAILFINDER_API_KEY`.
*   **Server:** `python3 execution/leadsnipe_api.py` (Localhost Port 8000).
*   **UI Server:** `python3 -m http.server 8080` (inside `.tmp/` folder).

---

## 🛑 Principles for Future Development
1. **Minimalism:** No colors unless absolutely vital. Keep it Apple-clean.
2. **Direct to DM:** Every feature must serve the goal of reaching the Decision Maker.
3. **Speed:** The path from "Search" to "Send" should be frictionless.
