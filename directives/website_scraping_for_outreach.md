# Website Scraping for Cold Outreach Personalization

## Purpose
When scraping a prospect's website for cold outreach, don't look for generic information. Hunt for **triggers** and **operational gaps** that reveal hidden costs they're ignoring.

## The Trigger Checklist

### 1. Operational Gaps (Pain Signals)

#### A. Business Hours vs. Emergency Claims
**Where to look:** Contact page, footer, homepage
**What to find:** 
- Do they advertise "24/7 Emergency Service" but list 9-5 office hours?
- Any disconnect between promise and capability

**The Hook:** "How do you handle the 2am emergency calls if your office closes at 5?"

#### B. The Contact Experience
**Where to look:** Contact form, chat widgets
**What to find:**
- Static form vs. modern scheduling widget?
- Phone number prominently displayed or buried?
- Submit a test inquiry and time the response

**The Hook:** "I submitted an inquiry and noticed it took X hours to get a response..."

#### C. Hiring Pages (Goldmine)
**Where to look:** Careers page, job boards (Indeed, LinkedIn)
**What to find:**
- Receptionist, Dispatcher, Admin, SDR postings
- High turnover indicators (same role listed multiple times)

**The Hook:** "Saw you're hiring a receptionist—usually that means the current team is drowning in call volume and response times are slipping."

---

### 2. Growth & Financial Triggers

#### A. Recent Awards/Milestones
**Where to look:** News, Blog, About Us, Homepage banners
**What to find:**
- "Best of [City] 2024"
- Anniversary ("Serving NJ for 20 years")
- Industry awards

**The Hook:** "Congrats on the Best of [City] award—bet the phones are ringing off the hook now."

#### B. Expansion Indicators
**Where to look:** News, Press releases, About page
**What to find:**
- New location openings
- Expanded service areas
- New team members

**The Hook:** "Saw the news about the new [City] location—with that kind of expansion, lead handling usually becomes a nightmare."

#### C. Funding/Acquisitions
**Where to look:** Press section, CrunchBase, LinkedIn
**What to find:**
- Recent funding rounds
- Merger/acquisition announcements
- Investor mentions

**The Hook:** "Saw the recent funding news—usually that means a mandate to scale quickly."

---

### 3. Tech Stack (Technographic Data)

#### A. CRM/Scheduling Tools
**Where to look:** 
- Footer links/logos
- Page source (look for tracking codes)
- Use Wappalyzer or BuiltWith browser extensions

**What to find:**
- ServiceTitan, Housecall Pro, Jobber (contractors)
- HubSpot, Salesforce (B2B)
- Calendly, Acuity (scheduling)

**The Hook:** "I see you use ServiceTitan; we integrate natively to automate your call logs."

#### B. Chat Widgets
**Where to look:** Bottom right corner of website
**What to find:**
- Intercom, Drift, LiveChat
- No chat = opportunity

**The Hook:** "Noticed you don't have a chat widget—most of your leads are probably calling, which means after-hours is a gap."

---

### 4. About Us Page (Human Connection)

#### A. Decision Maker's Voice
**Where to look:** About Us, Team page, Founder bio
**What to find:**
- Letter from the founder
- Mission statement
- Specific philosophy ("we prioritize instant response")

**The Hook:** "I saw on your About page that you prioritize 'instant response'—that's exactly what our AI enables 24/7."

#### B. Team Size Indicators
**Where to look:** Team page, About section
**What to find:**
- Small team (1-5) = owner is overwhelmed
- Medium team (10-20) = operational growing pains
- Look for admin/support roles or lack thereof

**The Hook:** "Looks like you run a lean team—my guess is you're often choosing between answering phones and doing the actual work."

---

## The Speed-to-Lead Test (Empirical Evidence)

This is the most powerful trigger because you have PROOF.

### How to Execute:
1. Go to their contact form
2. Submit a realistic inquiry (fake name, real-looking details)
3. Start a timer
4. Note how long until you get a response

### What the Data Means:
| Response Time | What It Means | Your Hook |
|---------------|---------------|-----------|
| Under 1 min | They're doing well (harder sell) | Focus on after-hours gap |
| 5-15 min | Losing 50%+ of leads | "Data shows 5 min delay = 80% drop in qualification" |
| 1+ hour | Major problem | "I submitted an inquiry X hours ago and just got a response" |
| No response | Critical failure | "I submitted an inquiry yesterday and haven't heard back" |

---

## Scraping Best Practices

### Pages to Prioritize
1. **Contact/Footer** - Hours, phone, form quality
2. **Careers** - Hiring signals
3. **About Us** - Team size, mission, founder voice
4. **News/Blog** - Recent wins, expansions
5. **Services** - Emergency offerings, scope

### What to Extract for Email Personalization
```
- Business name
- City/location
- Business type (plumber, HVAC, electrician)
- Owner/decision maker name (if found)
- Hours of operation
- Emergency service claims
- Current tech stack (CRM, scheduling)
- Recent news/awards
- Hiring status
- Response time to test inquiry
```

### Connect Observation to Business Impact
| Observation | Business Impact |
|-------------|-----------------|
| Hiring receptionist | Drowning in calls, $40K+ expense |
| 24/7 claim but 9-5 hours | Missing after-hours revenue |
| Slow form response | Losing 80% of leads to faster competitors |
| Recent expansion | Operational chaos, inconsistent handling |
| Uses ServiceTitan | Integration opportunity, technical credibility |

---

## Output Format for Email Generation

When passing scraped data to email generation, structure it as:

```json
{
  "trigger_type": "hiring|speed_test|expansion|after_hours|tech_stack",
  "trigger_details": "Specific observation from website",
  "business_impact": "What this costs them in dollars or leads",
  "personalization_hook": "Ready-to-use email opener"
}
```

Example:
```json
{
  "trigger_type": "hiring",
  "trigger_details": "Job posting for 'Front Desk Receptionist' on Indeed, posted 3 days ago",
  "business_impact": "About to spend $40K+ on salary while losing leads during hiring process",
  "personalization_hook": "I noticed you're hiring a front desk receptionist—usually that means the current team is overwhelmed by inbound volume."
}
```
