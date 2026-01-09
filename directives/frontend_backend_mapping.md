# LeadSnipe Frontend-Backend Function Mapping

## Overview

This document maps every UI function/button from the LeadSnipe app specification to the backend pipeline components. Use this as a blueprint for frontend implementation.

---

## Function Categories

### 1. CAMPAIGN CREATION & MANAGEMENT

#### UI: Create Campaign Wizard (Screens 5-8)

**Screen 5: Campaign Setup**
- **Function**: `[Create Campaign]` button
  - **Backend**: `execution/n8n_gmaps_scraper_ai.py`
  - **Inputs**:
    - Industry/business type (e.g., "HVAC", "Dentist")
    - Location (city, state)
    - Target lead count
  - **Output**: `.tmp/leads_{timestamp}.json`
  - **Data Flow**: User input → Python script → N8N webhook → JSON file → Display in app

**Screen 6: Lead Criteria**
- **Function**: Lead count selector (10/25/50/100/Custom)
  - **Backend**: `--target-leads` parameter in `n8n_gmaps_scraper_ai.py`
  - **Validation**: Min 5, max 500

**Screen 7: Message Template**
- **Function**: Email template editor
  - **Backend**: TBD - Email generation script (not yet built)
  - **Storage**: Campaign settings JSON

**Screen 8: Review & Launch**
- **Function**: `[Launch Campaign]` button
  - **Backend Pipeline**:
    1. `n8n_gmaps_scraper_ai.py` → Scrape leads
    2. `anymailfinder_decision_maker.py` → Find decision makers
    3. `find_linkedin_smart.py` → Find LinkedIn profiles
  - **Output**: Enriched leads in `.tmp/{campaign_id}_final.json`

---

### 2. LEAD ENRICHMENT

#### UI: Lead Detail Screen (Screen 11)

**Automatic Enrichment Functions**:
- **Function**: Auto-enrich on campaign creation
  - **Backend Pipeline**:
    - Step 1: N8N scraper → Business data + website HTML
    - Step 2: Anymailfinder → Decision maker email
    - Step 3: LinkedIn finder → LinkedIn URL
  - **Data**: 19+ data points per lead (see Data Available section)

**Manual Enrichment Actions**:
- **Function**: `[Refresh Data]` button
  - **Backend**: Re-run enrichment scripts on single lead
  - **Use Case**: Update stale data, retry failed lookups

- **Function**: `[Find LinkedIn]` button
  - **Backend**: `find_linkedin_smart.py` with single lead
  - **Inputs**: Lead name, company, website

- **Function**: `[Verify Email]` button
  - **Backend**: Email verification (existing script: `execution/verify_email.py`)
  - **Output**: Email status (valid/invalid/risky)

---

### 3. LEAD BROWSING & FILTERING

#### UI: All Leads Screen (Screen 10)

**Filter Functions**:
- **Function**: Search bar (search by name/company)
  - **Backend**: Client-side filtering of JSON data
  - **Data Source**: Campaign's enriched leads JSON

- **Function**: Filter chips (All/New/Contacted/Replied/Meeting Booked)
  - **Backend**: Client-side filtering by lead status
  - **Data Model**: Lead.status field

- **Function**: Sort dropdown (Newest/Oldest/Name A-Z)
  - **Backend**: Client-side sorting of lead array

**List Actions**:
- **Function**: Lead card tap → Navigate to Lead Detail
  - **Backend**: Pass lead ID, fetch full lead data from JSON

- **Function**: Star/favorite toggle
  - **Backend**: Update lead.is_favorite in storage
  - **Data**: Boolean flag

---

### 4. EMAIL GENERATION & SENDING

#### UI: Email Draft Screen (Screen 12)

**Generation Functions**:
- **Function**: `[Generate Email]` button
  - **Backend**: TBD - Email generation script (next pipeline step)
  - **Inputs**:
    - Lead data (name, company, industry)
    - Website triggers (from scraped HTML)
    - Email template
    - Personalization variables
  - **Output**: Personalized email draft
  - **LLM**: OpenRouter API (cheap model like Llama 3.3 70B)

- **Function**: `[Regenerate]` button
  - **Backend**: Call email generation again with same inputs
  - **Use Case**: User doesn't like first draft

**Editing Functions**:
- **Function**: Email editor (subject + body)
  - **Backend**: Client-side text editing
  - **Storage**: Draft saved to campaign data

- **Function**: Variable insertion `{firstName}`, `{company}`
  - **Backend**: Client-side template string replacement
  - **Variables Available**: All 19+ data points from enriched lead

**Sending Functions**:
- **Function**: `[Send Now]` button
  - **Backend**: Gmail API integration (existing: Gmail draft creation)
  - **Script**: Extend existing Gmail functionality
  - **Process**: Create draft → Send email → Update lead.status = "contacted"

- **Function**: `[Schedule]` button
  - **Backend**: Store scheduled time, background job to send
  - **Storage**: Campaign.scheduled_emails array

- **Function**: `[Save as Draft]` button
  - **Backend**: Gmail API - create draft only
  - **Storage**: Store draft_id in lead data

---

### 5. CAMPAIGN ANALYTICS

#### UI: Campaign Detail Screen (Screen 9)

**Stats Display** (read-only, calculated from lead data):
- **Function**: Show campaign stats
  - **Backend**: Aggregate from campaign's leads JSON
  - **Stats Calculated**:
    - Total leads: `leads.length`
    - Emails sent: `leads.filter(l => l.status === 'contacted').length`
    - Opened: `leads.filter(l => l.email_opened).length`
    - Replied: `leads.filter(l => l.status === 'replied').length`
    - Meetings booked: `leads.filter(l => l.status === 'meeting_booked').length`
    - Open rate: `(opened / sent) * 100`
    - Reply rate: `(replied / sent) * 100`

**Action Functions**:
- **Function**: `[View Leads]` button
  - **Backend**: Navigate to All Leads screen with campaign filter

- **Function**: `[Edit Campaign]` button
  - **Backend**: Load campaign settings, allow editing
  - **Editable**: Name, template, settings (not industry/location after creation)

- **Function**: `[Pause Campaign]` button
  - **Backend**: Update campaign.status = "paused"
  - **Effect**: Stop scheduled emails

- **Function**: `[Export Data]` button
  - **Backend**: Generate CSV from enriched leads JSON
  - **Format**: CSV with all 19+ data points

---

### 6. DASHBOARD

#### UI: Main Dashboard (Screen 4)

**Stats Cards** (read-only, aggregated from all campaigns):
- **Function**: Display global stats
  - **Backend**: Aggregate from all campaign JSONs
  - **Stats**:
    - Total leads: Sum of all campaigns
    - Sent: Sum of contacted leads
    - Replies: Sum of replied leads
    - Meetings: Sum of meeting_booked leads
  - **Trend**: Calculate change vs previous 7 days

**Quick Actions**:
- **Function**: `[+ New Campaign]` button
  - **Backend**: Navigate to Campaign Creation wizard

- **Function**: `[View All Leads]` button
  - **Backend**: Navigate to All Leads screen (all campaigns)

**Recent Activity Feed**:
- **Function**: Show recent events
  - **Backend**: Aggregate timeline from campaign events
  - **Events**:
    - "Email sent to {name} at {company}"
    - "Reply received from {name}"
    - "Meeting booked with {name}"
  - **Storage**: Campaign.events array with timestamps

---

### 7. AUTHENTICATION

#### UI: Login/Signup Screens (Screen 3)

**Auth Functions**:
- **Function**: `[Sign Up]` button
  - **Backend**: Firebase Auth or Supabase Auth
  - **Inputs**: Email, password, full name
  - **Output**: User ID, auth token

- **Function**: `[Log In]` button
  - **Backend**: Firebase/Supabase login
  - **Inputs**: Email, password
  - **Output**: Auth token, user data

- **Function**: `[Sign in with Google]` button
  - **Backend**: OAuth with Google
  - **Flow**: Redirect → Google consent → Return with token

- **Function**: `[Forgot Password?]` link
  - **Backend**: Firebase/Supabase password reset
  - **Flow**: Send reset email → User clicks link → Reset password

---

### 8. SETTINGS & PROFILE

#### UI: Settings Screen (Screen 14)

**Profile Functions**:
- **Function**: `[Edit Profile]` section
  - **Backend**: Update user document in database
  - **Fields**: Full name, email, company name, role

- **Function**: `[Change Password]` button
  - **Backend**: Firebase/Supabase password update
  - **Validation**: Current password required

**Email Integration**:
- **Function**: `[Connect Gmail]` button
  - **Backend**: Gmail OAuth flow
  - **Storage**: Store refresh token in user.gmail_token
  - **Script**: Extend existing Gmail API integration

- **Function**: `[Disconnect Gmail]` button
  - **Backend**: Revoke OAuth token, delete from storage

**Subscription**:
- **Function**: `[Upgrade Plan]` button
  - **Backend**: Stripe Checkout integration
  - **Flow**: Create checkout session → Redirect → Webhook updates subscription

- **Function**: `[Manage Subscription]` button
  - **Backend**: Stripe Customer Portal
  - **Features**: Cancel, update payment method, view invoices

**Notification Settings**:
- **Function**: Toggle switches for notification preferences
  - **Backend**: Update user.notification_settings object
  - **Settings**:
    - Email notifications (on/off)
    - Push notifications (on/off)
    - Reply notifications (on/off)
    - Daily summary (on/off)

---

### 9. ANALYTICS

#### UI: Analytics Screen (Screen 13)

**Chart Functions** (read-only visualizations):
- **Function**: Performance chart (line graph)
  - **Backend**: Aggregate campaign data by date
  - **Metrics**: Sent, opened, replied, meetings
  - **Time Range**: Filter by week/month/quarter

- **Function**: Best performing campaigns list
  - **Backend**: Sort campaigns by reply_rate desc
  - **Display**: Campaign name, reply rate, meetings booked

- **Function**: Export analytics button
  - **Backend**: Generate CSV with time-series data
  - **Format**: Date, sent, opened, replied, meetings, rates

---

## Data Available (Per Enriched Lead)

### From N8N Scraper (12 fields):
1. `name` - Business name
2. `address` - Full address
3. `phone` - Phone number
4. `website` - Website URL
5. `email` - Business email
6. `rating` - Google rating (1-5)
7. `user_ratings_total` - Number of reviews
8. `types` - Business category
9. `place_id` - Google Place ID
10. `scraped_text` - Full website HTML (for triggers)
11. `scraped_meta` - Meta description
12. `scraped_at` - Timestamp

### From Anymailfinder (5 fields):
13. `decision_maker.email` - Owner/CEO email
14. `decision_maker.full_name` - Owner full name
15. `decision_maker.job_title` - Job title (CEO, Owner, Founder)
16. `decision_maker.linkedin_url` - LinkedIn profile URL (sometimes)
17. `decision_maker.status` - Email validation status

### From LinkedIn Finder (1 field):
18. `decision_maker.linkedin_source` - Where LinkedIn was found

### Metadata (1 field):
19. `anymailfinder_credits_used` - Cost tracking

### Extractable from Website HTML (`scraped_text`):
- Social media links (Facebook, Instagram, Twitter)
- Team member names (from About page)
- Services offered
- Operating hours
- Recent news/awards
- Hiring posts
- Contact forms

---

## Backend Scripts Reference

### Existing Scripts (Working):
1. **`execution/n8n_gmaps_scraper_ai.py`** - Lead scraper
   - Command: `python3 execution/n8n_gmaps_scraper_ai.py --industry "X" --location "Y" --target-leads N`
   - Output: `.tmp/leads_{timestamp}.json`

2. **`execution/anymailfinder_decision_maker.py`** - Decision maker finder
   - Command: `python3 execution/anymailfinder_decision_maker.py --input X.json --output Y.json --category ceo`
   - Output: Enriched leads with decision_maker field

3. **`execution/find_linkedin_smart.py`** - LinkedIn finder
   - Command: `python3 execution/find_linkedin_smart.py --input X.json --output Y.json --delay 2`
   - Output: Leads with LinkedIn URLs

4. **`execution/verify_email.py`** - Email verification (from old pipeline)
   - Command: `python3 execution/verify_email.py --file X.json --output Y.json`
   - Output: Email validation status

### Scripts Needed (TBD):
5. **`execution/generate_outreach_email.py`** - Email generation
   - Inputs: Lead data, template, personalization settings
   - Output: Personalized email subject + body
   - LLM: OpenRouter API (Llama 3.3 70B FREE tier)

6. **`execution/send_email_gmail.py`** - Email sending
   - Inputs: Email draft, recipient email
   - Backend: Gmail API
   - Actions: Create draft, send email, track status

7. **`execution/track_email_engagement.py`** - Email tracking
   - Monitor: Opens, clicks, replies
   - Update: Lead status in database

---

## API Endpoints Needed

### Campaign Management
- `POST /campaigns/create` - Create new campaign
- `GET /campaigns/:id` - Get campaign details
- `PATCH /campaigns/:id` - Update campaign
- `DELETE /campaigns/:id` - Delete campaign
- `GET /campaigns` - List all user campaigns

### Lead Management
- `GET /campaigns/:id/leads` - Get campaign leads
- `GET /leads/:id` - Get single lead details
- `PATCH /leads/:id` - Update lead (status, notes, favorite)
- `POST /leads/:id/enrich` - Trigger re-enrichment

### Email Operations
- `POST /emails/generate` - Generate email from template
- `POST /emails/send` - Send email via Gmail
- `POST /emails/schedule` - Schedule email
- `GET /emails/drafts` - List Gmail drafts

### Analytics
- `GET /analytics/dashboard` - Global stats
- `GET /analytics/campaign/:id` - Campaign-specific stats
- `GET /analytics/export` - Export CSV

### User Management
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login
- `GET /user/profile` - Get user data
- `PATCH /user/profile` - Update profile
- `POST /user/gmail/connect` - Connect Gmail OAuth
- `DELETE /user/gmail/disconnect` - Disconnect Gmail

---

## Technology Stack Recommendations

### Frontend
- **Framework**: React Native (cross-platform iOS/Android)
- **State Management**: Redux Toolkit or Zustand
- **Navigation**: React Navigation
- **UI Components**: React Native Paper or NativeBase
- **Charts**: react-native-chart-kit
- **Forms**: React Hook Form

### Backend
- **Database**: Firebase Firestore or Supabase (PostgreSQL)
- **Authentication**: Firebase Auth or Supabase Auth
- **File Storage**: Firebase Storage or Supabase Storage
- **Email Sending**: Gmail API (already integrated)
- **Payments**: Stripe

### APIs
- **Lead Scraping**: N8N Webhook (existing)
- **Decision Maker**: Anymailfinder API (existing)
- **LinkedIn Search**: DuckDuckGo (existing, free)
- **Email Generation**: OpenRouter API (cheap LLM)
- **Email Tracking**: Custom or SendGrid/Mailgun

---

## Data Storage Structure

### Campaign Document
```json
{
  "id": "campaign_123",
  "user_id": "user_456",
  "name": "HVAC Businesses in Newark",
  "industry": "HVAC",
  "location": "Newark, NJ",
  "target_leads": 50,
  "status": "active",
  "created_at": "2026-01-05T...",
  "template": {
    "subject": "Question about your {businessType} service",
    "body": "Hi {firstName},\n\nI noticed..."
  },
  "stats": {
    "total_leads": 50,
    "emails_sent": 30,
    "opened": 12,
    "replied": 5,
    "meetings_booked": 2
  },
  "leads_file": ".tmp/campaign_123_final.json"
}
```

### Lead Document (stored in JSON file)
```json
{
  "id": "lead_789",
  "campaign_id": "campaign_123",
  "name": "ABC Heating & Cooling",
  "address": "123 Main St, Newark, NJ",
  "phone": "(973) 555-1234",
  "website": "https://abchvac.com",
  "email": "info@abchvac.com",
  "decision_maker": {
    "email": "john.smith@abchvac.com",
    "full_name": "John Smith",
    "job_title": "Owner",
    "linkedin_url": "https://linkedin.com/in/johnsmith"
  },
  "status": "new",
  "is_favorite": false,
  "notes": "",
  "email_draft": {
    "subject": "Question about your HVAC service",
    "body": "Hi John,\n\n...",
    "generated_at": "2026-01-05T..."
  },
  "email_sent_at": null,
  "email_opened_at": null,
  "replied_at": null,
  "meeting_booked_at": null
}
```

---

## Implementation Priority

### Phase 1: Core Pipeline (DONE ✅)
- [x] N8N lead scraper
- [x] Anymailfinder integration
- [x] LinkedIn finder
- [x] Documentation

### Phase 2: Frontend Screens (NEXT)
1. **Authentication** (Screens 3)
   - Sign up, log in, forgot password
   - Firebase/Supabase integration

2. **Campaign Creation** (Screens 5-8)
   - Wizard UI
   - Integration with backend scripts
   - Display enrichment progress

3. **Dashboard** (Screen 4)
   - Stats display
   - Quick actions
   - Recent activity

4. **Lead Browsing** (Screens 10-11)
   - Lead list with filters
   - Lead detail view
   - Manual actions (refresh, verify)

### Phase 3: Email Features
1. **Email Generation** (Screen 12)
   - Build `generate_outreach_email.py`
   - Template editor
   - Personalization variables

2. **Email Sending**
   - Extend Gmail API integration
   - Send/schedule/draft functions
   - Status tracking

3. **Email Tracking**
   - Open tracking
   - Reply detection
   - Status updates

### Phase 4: Analytics & Settings
1. **Analytics** (Screen 13)
   - Charts and metrics
   - Export functionality

2. **Settings** (Screen 14)
   - Profile editing
   - Gmail connection
   - Subscription management

---

## Next Steps

1. **Review this mapping** with user to confirm all functions are correct
2. **Choose frontend framework** (React Native recommended)
3. **Set up project structure** with screens and navigation
4. **Implement Phase 2 screens** (Auth → Campaign → Dashboard → Leads)
5. **Build email generation script** (`execution/generate_outreach_email.py`)
6. **Integrate backend with frontend** (API layer or direct script calls)
7. **Add Stripe subscription** for paid plans
8. **Deploy backend** (if needed - scripts can run locally for now)

---

## Questions to Resolve

1. **Database choice**: Firebase Firestore or Supabase?
2. **Frontend framework**: React Native or Flutter?
3. **Backend deployment**: Scripts run locally or deploy to cloud?
4. **Email tracking**: Build custom or use third-party service?
5. **File storage**: Where to store campaign JSON files in production?
