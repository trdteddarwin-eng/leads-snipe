# LeadSnipe Mobile App - Complete Product Specification

---

## 🎯 App Overview

### What is LeadSnipe?
LeadSnipe is a B2B lead generation mobile app that helps sales professionals, agency owners, and entrepreneurs find decision-makers at local businesses and send personalized cold outreach emails—all from their phone.

### The Problem We Solve
1. **Finding leads is time-consuming** - Manually searching Google Maps, copying contact info
2. **Generic emails don't convert** - info@ and contact@ emails go to front desk, not decision-makers
3. **Personalization is hard** - Writing unique emails for 50+ leads takes hours
4. **No mobile solution** - Existing tools (Apollo, Hunter) are desktop-only and expensive

### How It Works (User Journey)
```
1. User selects a niche (Dentists, Med Spas, Plumbers, etc.)
2. User enters a location (Union, NJ)
3. App scrapes 50 leads from Google Maps
4. App finds owner LinkedIn profiles using Google X-Ray search
5. App gets owner's verified email using Anymailfinder
6. AI generates personalized cold emails based on website analysis
7. Emails are created as Gmail drafts (or sent directly)
8. User reviews and sends with one tap
```

### Value Proposition
> "Find 50 decision-maker emails and send personalized outreach in 5 minutes, not 5 hours."

---

## 🎨 Design System

### Colors
```
Primary Background: #0D0D14 (near black)
Secondary Background: #1A1A2E (dark purple-gray)
Card Background: #252538 (elevated surface)
Primary Accent: #7C3AED (purple)
Secondary Accent: #3B82F6 (blue)
Gradient: linear-gradient(135deg, #7C3AED, #3B82F6)
Success: #10B981 (green)
Warning: #F59E0B (amber)
Error: #EF4444 (red)
Text Primary: #FFFFFF
Text Secondary: #A1A1AA (gray)
Text Muted: #71717A (darker gray)
Border: #27272A
```

### Typography
```
Font Family: Inter (or SF Pro for iOS)
Headings: 
  - H1: 28px, Bold
  - H2: 24px, Semibold
  - H3: 20px, Semibold
  - H4: 18px, Medium
Body: 16px, Regular
Caption: 14px, Regular
Small: 12px, Regular
```

### Spacing
```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
2xl: 48px
```

### Border Radius
```
sm: 8px
md: 12px
lg: 16px
xl: 24px
full: 9999px (pills)
```

---

## 📱 Screen-by-Screen Specification

---

### 1. SPLASH SCREEN

**Purpose:** Show branding while app loads

**Elements:**
- [ ] App logo (LeadSnipe icon - crosshair/target on envelope)
- [ ] App name "LeadSnipe" in gradient text
- [ ] Tagline: "Find decision-makers. Send personalized emails."
- [ ] Loading indicator (subtle pulse animation)

**Duration:** 2-3 seconds, then navigate to Onboarding (first time) or Dashboard (returning user)

---

### 2. ONBOARDING FLOW (First-time users only)

#### Screen 2.1: Welcome
**Elements:**
- [ ] Illustration: Person on phone with email icons floating
- [ ] Headline: "Welcome to LeadSnipe"
- [ ] Subheadline: "The fastest way to find leads and send cold emails"
- [ ] [Get Started] button (primary, full width)
- [ ] "Already have an account? [Sign In]" link

#### Screen 2.2: Value Prop 1
**Elements:**
- [ ] Illustration: Map with pins transforming into contact cards
- [ ] Headline: "Find Local Business Leads"
- [ ] Subheadline: "Search any niche in any city. We scrape Google Maps and find 50+ leads in seconds."
- [ ] Progress dots (1 of 3 filled)
- [ ] [Next] button
- [ ] [Skip] text link

#### Screen 2.3: Value Prop 2
**Elements:**
- [ ] Illustration: LinkedIn logo connecting to email icon
- [ ] Headline: "Get Owner Emails"
- [ ] Subheadline: "We find the LinkedIn profile of the owner and get their verified email—not just info@company.com."
- [ ] Progress dots (2 of 3 filled)
- [ ] [Next] button
- [ ] [Skip] text link

#### Screen 2.4: Value Prop 3
**Elements:**
- [ ] Illustration: AI brain icon generating email
- [ ] Headline: "AI-Powered Personalization"
- [ ] Subheadline: "Our AI analyzes each website and writes unique cold emails that actually get replies."
- [ ] Progress dots (3 of 3 filled)
- [ ] [Let's Go] button (primary)

---

### 3. AUTHENTICATION

#### Screen 3.1: Sign Up
**Elements:**
- [ ] Back arrow (top left)
- [ ] Headline: "Create Account"
- [ ] [Continue with Google] button (icon + text, outlined)
- [ ] [Continue with Apple] button (icon + text, outlined)
- [ ] Divider: "or"
- [ ] Email input field (placeholder: "Email address")
- [ ] Password input field (placeholder: "Password", with show/hide toggle)
- [ ] [Create Account] button (primary, full width)
- [ ] Terms text: "By signing up, you agree to our [Terms] and [Privacy Policy]"
- [ ] "Already have an account? [Sign In]" link

#### Screen 3.2: Sign In
**Elements:**
- [ ] Back arrow (top left)
- [ ] Headline: "Welcome Back"
- [ ] [Continue with Google] button
- [ ] [Continue with Apple] button
- [ ] Divider: "or"
- [ ] Email input field
- [ ] Password input field
- [ ] [Forgot Password?] link (right-aligned)
- [ ] [Sign In] button (primary)
- [ ] "Don't have an account? [Sign Up]" link

#### Screen 3.3: Forgot Password
**Elements:**
- [ ] Back arrow
- [ ] Headline: "Reset Password"
- [ ] Subheadline: "Enter your email and we'll send you a reset link"
- [ ] Email input field
- [ ] [Send Reset Link] button

#### Screen 3.4: Connect Gmail (Post-signup)
**Elements:**
- [ ] Progress indicator: Step 1 of 2
- [ ] Gmail icon (large)
- [ ] Headline: "Connect Your Gmail"
- [ ] Subheadline: "We need access to create email drafts for you. We never read your emails."
- [ ] Permission list:
  - ✓ Create drafts
  - ✓ Send emails on your behalf
  - ✗ We never read your inbox
- [ ] [Connect Gmail] button (primary, with Google icon)
- [ ] [Skip for now] link (muted)

#### Screen 3.5: Add API Key (Post-signup)
**Elements:**
- [ ] Progress indicator: Step 2 of 2
- [ ] Headline: "Almost Done!"
- [ ] Subheadline: "Add your Anymailfinder API key to find owner emails"
- [ ] API Key input field (password style, with paste button)
- [ ] "Don't have one? [Get free API key]" link (opens Anymailfinder signup)
- [ ] [Complete Setup] button
- [ ] [Skip for now] link

---

### 4. MAIN DASHBOARD (Home Tab)

**Purpose:** Overview of user's activity and quick actions

#### Header
- [ ] "LeadSnipe" logo (left)
- [ ] Notification bell icon (right, with red dot if unread)
- [ ] User avatar (right, tappable → Profile)

#### Greeting Section
- [ ] "Good morning, {FirstName}" (dynamic based on time)
- [ ] "Ready to find some leads?" (subtitle)

#### Stats Cards Row (Horizontal scroll)
- [ ] Card 1: "{count} Leads" + trend arrow (e.g., "+12 this week")
- [ ] Card 2: "{count} Sent" + trend
- [ ] Card 3: "{count} Replies" + trend
- [ ] Card 4: "{count} Meetings" + trend

#### Quick Actions Section
- [ ] Section title: "Quick Actions"
- [ ] [+ New Campaign] button (primary, large, gradient background)
- [ ] [View All Leads] button (secondary, outlined)

#### Recent Campaigns Section
- [ ] Section title: "Recent Campaigns" + [See All] link
- [ ] Campaign Card (repeating):
  - Campaign name (e.g., "Dentists - Union NJ")
  - Lead count badge (e.g., "47 leads")
  - Status badge (Draft/Active/Completed)
  - Date created
  - Chevron right icon
  - Tappable → Campaign Detail

#### Credits Section (Bottom card)
- [ ] "Credits Remaining" label
- [ ] "{X} / {Y} credits" with progress bar
- [ ] [Upgrade Plan] button (if low)

#### Bottom Navigation Bar
- [ ] Home icon + "Home" label (active state: purple)
- [ ] Grid icon + "Campaigns" label
- [ ] Users icon + "Leads" label
- [ ] Chart icon + "Analytics" label
- [ ] Gear icon + "Settings" label

---

### 5. CAMPAIGNS TAB

#### Screen 5.1: Campaign List
**Header:**
- [ ] "Campaigns" title
- [ ] [+ New] button (top right)

**Filter Tabs (Horizontal):**
- [ ] All | Active | Drafts | Completed

**Campaign Cards (List):**
- [ ] Campaign name
- [ ] Niche tag (e.g., "Med Spa")
- [ ] Location (e.g., "Union, NJ")
- [ ] Stats row: "50 leads • 23 sent • 3 replies"
- [ ] Status badge
- [ ] Date
- [ ] Swipe actions: Edit, Delete

**Empty State (if no campaigns):**
- [ ] Illustration: Empty folder
- [ ] "No campaigns yet"
- [ ] "Create your first campaign to start finding leads"
- [ ] [Create Campaign] button

---

### 6. CREATE CAMPAIGN WIZARD

#### Screen 6.1: Select Niche (Step 1/4)
**Header:**
- [ ] [X] Close button (top left)
- [ ] "New Campaign" title
- [ ] Progress bar (25%)

**Content:**
- [ ] Headline: "What type of business?"
- [ ] Popular Niches Grid (2x3):
  - 🦷 Dentists
  - 💆 Med Spas
  - 🔧 Plumbers
  - ❄️ HVAC
  - 🏠 Real Estate
  - 🏗️ Contractors
- [ ] [See More Niches] expandable (reveals: Chiropractors, Lawyers, Accountants, Car Dealerships, Gyms, Restaurants, etc.)
- [ ] OR divider
- [ ] Custom input: "Enter custom niche..." (with search icon)
- [ ] [Continue] button (disabled until selection)

#### Screen 6.2: Select Location (Step 2/4)
**Header:**
- [ ] [←] Back button
- [ ] Progress bar (50%)

**Content:**
- [ ] Headline: "Where should we search?"
- [ ] Location input field with location pin icon
  - Placeholder: "City, State (e.g., Union, NJ)"
  - Autocomplete dropdown as user types
- [ ] Recent locations list (if any):
  - "Recent: Summit, NJ • Elizabeth, NJ"
- [ ] Radius selector (optional):
  - "Include nearby cities" toggle
  - If on: "Within {X} miles" slider (5-50 miles)
- [ ] [Continue] button

#### Screen 6.3: Campaign Settings (Step 3/4)
**Header:**
- [ ] [←] Back button
- [ ] Progress bar (75%)

**Content:**
- [ ] Headline: "Campaign Settings"

- [ ] Section: "Lead Count"
  - Slider: 10 - 100 - 500
  - Current value shown: "50 leads"
  - Helper text: "More leads = more credits used"

- [ ] Section: "Enrichment Options"
  - [ ] Toggle: "Find owner LinkedIn" (default ON)
    - Helper: "Uses Google search - FREE"
  - [ ] Toggle: "Get owner email" (default ON)
    - Helper: "Uses Anymailfinder - 1 credit per email found"
  - [ ] Toggle: "Verify emails" (default ON)
    - Helper: "Check email deliverability - FREE"
  - [ ] Toggle: "Generate AI emails" (default ON)
    - Helper: "Personalized cold emails - 1 credit per email"

- [ ] Section: "Email Settings"
  - [ ] Sender name input: "Your name" (prefilled from profile)
  - [ ] Email template dropdown: "Default Cold Email" / "Follow-up" / "Custom"
  - [ ] [Preview Template] link

- [ ] [Continue] button

#### Screen 6.4: Review & Start (Step 4/4)
**Header:**
- [ ] [←] Back button
- [ ] Progress bar (100%)

**Content:**
- [ ] Headline: "Review Campaign"

- [ ] Summary Card:
  - Niche: "Med Spas"
  - Location: "Union, NJ"
  - Lead Count: "50"
  - Enrichment: "LinkedIn + Owner Email + AI Emails"
  
- [ ] Credits Estimate Card:
  - "Estimated credits: 50-75"
  - "Your balance: 200 credits"
  - Progress bar showing usage

- [ ] Campaign Name Input:
  - Placeholder: "Campaign name"
  - Auto-suggested: "Med Spas - Union NJ - Jan 2"

- [ ] [Start Campaign] button (primary, large)
- [ ] "By starting, {X} credits will be used"

---

### 7. CAMPAIGN PROCESSING SCREEN

**Purpose:** Show real-time progress while enriching leads

#### Header
- [ ] "Processing..." title
- [ ] Campaign name subtitle

#### Progress Section
- [ ] Large circular progress indicator (0-100%)
- [ ] Current step text: "Finding LinkedIn profiles..."

#### Steps Checklist
- [ ] ✅ Scraped 50 leads (completed - green check)
- [ ] ✅ Verified 43 emails (completed)
- [ ] 🔄 Finding LinkedIn profiles (28/43) (in progress - spinner)
- [ ] ⏳ Getting owner emails (pending - gray)
- [ ] ⏳ Generating personalized emails (pending)

#### Live Activity Log (Scrollable)
- [ ] Terminal-style log with recent activity:
  ```
  [12:34:15] Scraped 50 leads from Google Maps
  [12:34:18] Verified: smiles@lindendental.com ✓
  [12:34:21] Found LinkedIn: Anya Stassiy (Owner)
  [12:34:25] Email found: anyastassiy@highpointmedspa.com
  ```

#### Stats Row
- [ ] "8 Owners Found" | "5 Emails Retrieved" | "0 Failed"

#### Bottom
- [ ] [Cancel] button (destructive, outlined)
- [ ] Estimated time remaining: "~2 min remaining"

---

### 8. CAMPAIGN COMPLETE SCREEN

**Purpose:** Summary of enrichment results

#### Header
- [ ] ✅ Success icon (large, green)
- [ ] "Campaign Ready!"

#### Results Summary Cards
- [ ] Total Leads: 50
- [ ] Verified Emails: 43
- [ ] Owner LinkedIn Found: 18
- [ ] Owner Emails Retrieved: 12
- [ ] AI Emails Generated: 12
- [ ] Credits Used: 24

#### Action Buttons
- [ ] [View Leads] button (primary)
- [ ] [Review Emails] button (secondary)
- [ ] [Share Results] button (outlined)

---

### 9. LEADS TAB

#### Screen 9.1: Leads List
**Header:**
- [ ] "Leads" title
- [ ] [Filter] button (right)
- [ ] Search bar: "Search leads..."

**Filter Bar (Horizontal scroll):**
- [ ] All | Decision Maker Found | Email Verified | Contacted | Replied

**Sort Dropdown:**
- [ ] Sort by: Newest | Name A-Z | Rating | Status

**Lead Cards (List):**
- [ ] Business name (bold)
- [ ] Address (single line, truncated)
- [ ] Rating stars + review count
- [ ] Tags row:
  - 🟢 "Email Verified" (green badge)
  - 🟣 "Owner Found" (purple badge)
  - 📧 "Draft Ready" (blue badge)
- [ ] Status indicator: New / Contacted / Replied / Won / Lost
- [ ] Chevron right
- [ ] Tappable → Lead Detail

**Bulk Actions (appears when selecting):**
- [ ] "3 selected" count
- [ ] [Send All] button
- [ ] [Delete] button
- [ ] [Cancel] link

---

### 10. LEAD DETAIL SCREEN

**Header:**
- [ ] [←] Back button
- [ ] [⋮] More options menu (Edit, Delete, Add to List)

#### Business Info Card
- [ ] Business name (H2)
- [ ] Rating: ⭐ 4.8 (142 reviews)
- [ ] Category: "Med Spa"
- [ ] Address: "200 Sheffield St, Mountainside, NJ"
- [ ] [📍 Open in Maps] link

#### Contact Info Section
- [ ] Phone: (201) 618-5283 → [📞 Call] button
- [ ] Website: highpointmedspa.com → [🌐 Visit] button
- [ ] Email: highpointmedspa@gmail.com → [📧 Email] button
  - Badge: "Office Email" (gray) or "✓ Verified" (green)

#### Decision Maker Section (if found)
- [ ] Section title: "Decision Maker" + 🟢 dot
- [ ] Photo placeholder (circle)
- [ ] Name: "Anya Stassiy"
- [ ] Title: "Owner / Provider"
- [ ] LinkedIn icon → [View LinkedIn] button
- [ ] Email: anyastassiy@highpointmedspa.com
  - Badge: "✓ Verified Owner Email" (green)
- [ ] [📧 Email Owner] button (primary)

#### AI Email Draft Section
- [ ] Section title: "Email Draft" + [Edit] link
- [ ] Card with email preview:
  - Subject: "missed calls at high point medspa"
  - Body preview (first 2 lines): "Hi Anya, I'm guessing you often have to choose between answering the phone and being with a client..."
  - [Expand] button
- [ ] [Send Email] button (primary)
- [ ] [Edit Draft] button (secondary)

#### Quick Actions Row
- [ ] 📞 Call
- [ ] 📧 Email
- [ ] 🔗 LinkedIn
- [ ] 📝 Add Note

#### Notes Section
- [ ] Section title: "Notes" + [+ Add] button
- [ ] Note cards (if any):
  - Note text
  - Timestamp: "Added Jan 2, 2026"
- [ ] Add note input (expandable)

#### Activity Timeline
- [ ] Section title: "Activity"
- [ ] Timeline items:
  - "Lead created" - Jan 2, 12:30 PM
  - "Email draft generated" - Jan 2, 12:32 PM
  - "Email sent" - Jan 2, 1:15 PM
  - "Email opened" - Jan 2, 3:45 PM

#### Status Selector
- [ ] Current status pill (tappable)
- [ ] Dropdown options: New → Contacted → Replied → Meeting Scheduled → Won → Lost

---

### 11. EMAIL COMPOSER SCREEN

**Purpose:** Edit and send email

**Header:**
- [ ] [Cancel] button (left)
- [ ] "Compose Email" title
- [ ] [Send] button (right, primary color)

**From Section:**
- [ ] "From:" label
- [ ] Email dropdown (if multiple accounts): tedcharles@gmail.com ▼

**To Section:**
- [ ] "To:" label
- [ ] Recipient chip: "Anya Stassiy <anyastassiy@highpointmedspa.com>" [x]

**Subject Line:**
- [ ] "Subject:" label
- [ ] Input field: "missed calls at high point medspa"
- [ ] [🔄 Regenerate] button (AI regenerate subject)

**Email Body:**
- [ ] Rich text editor with formatting toolbar:
  - Bold, Italic, Link, Bullet list
- [ ] Email body text (editable)
- [ ] Signature preview (grayed out):
  ```
  Best,
  Tedca
  
  tedca.org
  ```

**Personalization Tokens:**
- [ ] Insertable tokens bar: {FirstName} {BusinessName} {City}

**Bottom Actions:**
- [ ] [Save as Draft] button
- [ ] [Schedule Send] button (with date/time picker)
- [ ] [Send Now] button (primary)

---

### 12. ANALYTICS TAB

**Header:**
- [ ] "Analytics" title
- [ ] Date range picker: "Last 7 days ▼"

#### Overview Stats Row
- [ ] Total Leads: 247
- [ ] Emails Sent: 89
- [ ] Open Rate: 42%
- [ ] Reply Rate: 8%
- [ ] Meetings: 3

#### Charts Section

**Chart 1: Leads Over Time (Line chart)**
- [ ] Title: "Leads Collected"
- [ ] X-axis: Days
- [ ] Y-axis: Count
- [ ] Tooltip on hover

**Chart 2: Email Performance (Bar chart)**
- [ ] Sent vs Opened vs Replied
- [ ] Stacked or grouped bars

**Chart 3: Top Performing Niches (Horizontal bar)**
- [ ] Niche names with reply rate percentage
- [ ] e.g., "Med Spas: 12% reply rate"

#### Campaign Performance Table
- [ ] Campaign name | Leads | Sent | Opens | Replies | Meetings
- [ ] Sortable columns
- [ ] Tappable rows → Campaign detail

#### Cost Breakdown Card
- [ ] Credits used this month: 156
- [ ] Estimated cost: $4.68
- [ ] Cost per lead: $0.03

---

### 13. SETTINGS TAB

**Header:**
- [ ] "Settings" title

**Profile Section**
- [ ] Profile photo (editable)
- [ ] Name: Yolande Jean
- [ ] Email: trdteddarwin@gmail.com
- [ ] [Edit Profile] button

**Connected Accounts Section**
- [ ] Gmail: trdteddarwin@gmail.com ✅ Connected
  - [Disconnect] link
- [ ] LinkedIn: Not connected
  - [Connect LinkedIn] button

**API Keys Section**
- [ ] Section title: "API Keys"
- [ ] Anymailfinder: ••••••VltYVP ✅
  - [Edit] | [Test] links
- [ ] OpenRouter: ••••••3420b ✅
  - [Edit] | [Test] links
- [ ] [+ Add API Key] button

**Email Settings Section**
- [ ] Default signature (editable text area)
- [ ] Default sender name
- [ ] Reply-to email

**Notifications Section**
- [ ] Push notifications toggle
- [ ] Email notifications toggle
- [ ] Notify on: Reply received, Campaign complete, Low credits

**Billing Section**
- [ ] Current plan: "Pro ($79/mo)"
- [ ] Credits remaining: 847 / 1000
- [ ] Next billing: Feb 2, 2026
- [ ] [Manage Subscription] button
- [ ] [View Invoices] link

**Support Section**
- [ ] [Help Center] link
- [ ] [Contact Support] link
- [ ] [Feature Request] link

**Legal Section**
- [ ] [Terms of Service] link
- [ ] [Privacy Policy] link

**Danger Zone**
- [ ] [Sign Out] button
- [ ] [Delete Account] link (red, requires confirmation)

**App Version**
- [ ] "LeadSnipe v1.0.0"

---

### 14. TEMPLATES SCREEN

**Header:**
- [ ] "Email Templates" title
- [ ] [+ New Template] button

**Template Categories Tabs:**
- [ ] All | Cold Outreach | Follow-up | Custom

**Template Cards:**
- [ ] Template name
- [ ] Preview text (first 50 chars)
- [ ] Usage count: "Used 23 times"
- [ ] Performance: "12% reply rate"
- [ ] [Edit] | [Duplicate] | [Delete] actions

**Default Templates (Pre-built):**
1. "Cold Outreach - Missed Calls"
2. "Cold Outreach - Hiring"
3. "Follow-up - No Reply"
4. "Follow-up - After Meeting"

---

### 15. NOTIFICATIONS SCREEN

**Header:**
- [ ] [←] Back
- [ ] "Notifications" title
- [ ] [Mark All Read] link

**Notification List:**
- [ ] Notification card:
  - Icon (email opened, reply, etc.)
  - Title: "New reply from Anya Stassiy"
  - Subtitle: "High Point Medspa"
  - Timestamp: "2 hours ago"
  - Unread indicator (purple dot)
- [ ] Swipe to delete

**Empty State:**
- [ ] "No notifications yet"
- [ ] "You'll see updates about your campaigns here"

---

### 16. UPGRADE/PRICING SCREEN

**Header:**
- [ ] [X] Close
- [ ] "Upgrade Your Plan" title

**Current Plan Card:**
- [ ] "You're on Free Plan"
- [ ] "25 leads/month • 10 enrichments"

**Plan Cards:**

**Starter - $29/mo**
- [ ] 200 leads/month
- [ ] 50 enrichments
- [ ] AI email generation
- [ ] Email support
- [ ] [Select Plan] button

**Pro - $79/mo** (Recommended badge)
- [ ] 1,000 leads/month
- [ ] 200 enrichments
- [ ] AI email generation
- [ ] Template library
- [ ] Priority support
- [ ] [Select Plan] button (highlighted)

**Agency - $199/mo**
- [ ] Unlimited leads
- [ ] 1,000 enrichments
- [ ] White-label exports
- [ ] Team seats (5)
- [ ] Dedicated support
- [ ] [Select Plan] button

**Footer:**
- [ ] "All plans include a 7-day free trial"
- [ ] [Compare all features] link

---

## 🔄 User Flows

### Flow 1: First-time User to First Campaign
```
Splash → Onboarding (3 slides) → Sign Up → Connect Gmail → Add API Key → Dashboard → New Campaign → Select Niche → Select Location → Settings → Review → Start → Processing → Complete → View Leads
```

### Flow 2: Returning User Sends Email
```
Open App → Dashboard → Recent Campaign → Lead Detail → Review Email Draft → Edit (optional) → Send → Confirmation
```

### Flow 3: Check Analytics
```
Dashboard → Analytics Tab → View Stats → Filter by Date → View Campaign Performance → Export (optional)
```

---

## 📲 Gestures & Interactions

| Gesture | Action |
|---------|--------|
| Pull down | Refresh data |
| Swipe left on card | Delete / Archive |
| Swipe right on card | Quick action (Send) |
| Long press | Multi-select mode |
| Double tap | Quick edit |
| Pinch | Zoom charts |

---

## 🔔 Notifications & Alerts

### Push Notifications
- "🎉 Campaign complete! 12 owner emails found."
- "📬 New reply from Anya Stassiy"
- "⚠️ Low credits - only 10 remaining"
- "✅ 5 emails sent successfully"

### In-App Toasts
- Success: "Email sent!" (green)
- Error: "Failed to send. Try again." (red)
- Info: "Draft saved" (blue)
- Warning: "2 invalid emails skipped" (amber)

### Modals
- Confirmation: "Delete this lead?" [Cancel] [Delete]
- Credit warning: "This will use 50 credits. Continue?" [Cancel] [Proceed]

---

## 💾 Data Models

### User
```json
{
  "id": "uuid",
  "email": "user@email.com",
  "name": "Yolande Jean",
  "avatar_url": "https://...",
  "gmail_connected": true,
  "anymailfinder_key": "encrypted",
  "openrouter_key": "encrypted",
  "plan": "pro",
  "credits_remaining": 847,
  "created_at": "2026-01-02T..."
}
```

### Campaign
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "Med Spas - Union NJ",
  "niche": "Med Spa",
  "location": "Union, NJ",
  "lead_count_target": 50,
  "status": "completed",
  "settings": {
    "find_linkedin": true,
    "get_owner_email": true,
    "verify_emails": true,
    "generate_ai_emails": true
  },
  "stats": {
    "leads_scraped": 50,
    "emails_verified": 43,
    "linkedin_found": 18,
    "owner_emails": 12,
    "emails_generated": 12
  },
  "credits_used": 24,
  "created_at": "2026-01-02T..."
}
```

### Lead
```json
{
  "id": "uuid",
  "campaign_id": "uuid",
  "business_name": "High Point Medspa",
  "address": "200 Sheffield St, Mountainside, NJ",
  "phone": "(201) 618-5283",
  "website": "http://www.highpointmedspa.com",
  "office_email": "highpointmedspa@gmail.com",
  "email_verified": true,
  "owner_name": "Anya Stassiy",
  "owner_title": "Owner",
  "owner_linkedin": "https://linkedin.com/in/anya-stassiy-90448424",
  "owner_email": "anyastassiy@highpointmedspa.com",
  "owner_email_verified": true,
  "status": "new",
  "rating": 5.0,
  "review_count": 133,
  "tags": ["Med Spa", "Owner Found", "Email Verified"],
  "notes": [],
  "created_at": "2026-01-02T..."
}
```

### EmailDraft
```json
{
  "id": "uuid",
  "lead_id": "uuid",
  "to_email": "anyastassiy@highpointmedspa.com",
  "to_name": "Anya Stassiy",
  "subject": "missed calls at high point medspa",
  "body": "Hi Anya,\n\nI'm guessing...",
  "status": "draft",
  "sent_at": null,
  "opened_at": null,
  "replied_at": null,
  "gmail_draft_id": "abc123",
  "created_at": "2026-01-02T..."
}
```

---

## 🚀 Technical Requirements

### APIs Needed (Backend)
- POST /auth/signup
- POST /auth/login
- GET /user/profile
- PUT /user/profile
- GET /campaigns
- POST /campaigns
- GET /campaigns/:id
- GET /campaigns/:id/leads
- POST /campaigns/:id/start
- GET /leads
- GET /leads/:id
- PUT /leads/:id
- POST /leads/:id/email
- GET /templates
- POST /templates
- GET /analytics
- POST /webhooks/gmail (for replies)

### External Services
- Firebase Auth (or Supabase)
- Supabase Database
- Gmail API
- Anymailfinder API
- OpenRouter API
- N8N Webhook
- Stripe (payments)

---

This specification should be comprehensive enough to build the entire app frontend. Let me know if you need any section expanded further!
