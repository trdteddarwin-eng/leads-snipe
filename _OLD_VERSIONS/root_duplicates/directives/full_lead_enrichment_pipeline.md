# Full Lead Enrichment & Cold Outreach Pipeline

## Overview
End-to-end workflow for finding local business leads, enriching them with decision-maker LinkedIn profiles and verified emails, and generating personalized cold outreach emails.

---

## Pipeline Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FULL LEAD ENRICHMENT PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│ STEP 1: N8N SCRAPE (FREE)                                               │
│         Input: Business type + Location                                  │
│         Output: 50+ leads with name, address, phone, website, email     │
│                                                                          │
│ STEP 2: EMAIL VERIFICATION (FREE)                                       │
│         Input: Scraped leads                                             │
│         Output: Leads with verified emails only                          │
│                                                                          │
│ STEP 3: LINKEDIN DISCOVERY (FREE - Browser Automation)                  │
│         Input: Business names                                            │
│         Method: Google X-Ray search via browser                          │
│         Output: LinkedIn URLs for owners/decision makers                 │
│                                                                          │
│ STEP 4: DECISION-MAKER EMAIL (Anymailfinder ~$0.01-0.02/email)          │
│         Input: LinkedIn URLs                                             │
│         Output: Verified owner/decision-maker emails                     │
│                                                                          │
│ STEP 5: WEBSITE TRIGGER ANALYSIS (FREE)                                 │
│         Input: Business websites                                         │
│         Output: Personalization hooks (hiring, hours, awards)            │
│                                                                          │
│ STEP 6: EMAIL GENERATION (OpenRouter ~$0.01/batch)                      │
│         Input: Enriched leads + triggers                                 │
│         Output: Personalized cold emails                                 │
│                                                                          │
│ STEP 7: GMAIL DRAFT CREATION (FREE)                                     │
│         Input: Generated emails                                          │
│         Output: Drafts in Gmail ready to send                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: N8N Lead Scrape

### Command
```bash
curl -X POST "https://n8n.srv1080136.hstgr.cloud/webhook/c66d6d2a-f22d-4fb6-b874-18ae5915347b" \
  -H "Content-Type: application/json" \
  -d '["Med Spa in Union, NJ", "Med Spa in Elizabeth, NJ", "Med Spa in Summit, NJ"]' \
  --max-time 180
```

### Input Format
Array of search queries with city variations:
```json
["Business Type in City1, State", "Business Type in City2, State", ...]
```

### Output Format
```json
[
  {
    "name": "Business Name",
    "address": "Full Address",
    "phone": "(908) 555-1234",
    "website": "https://example.com",
    "email": "info@example.com",
    "rating": 4.8
  }
]
```

### City Variations for Union, NJ Area
- Union, NJ
- Elizabeth, NJ
- Summit, NJ
- Westfield, NJ
- Cranford, NJ
- Linden, NJ
- Rahway, NJ
- Springfield, NJ
- Mountainside, NJ
- Scotch Plains, NJ
- Maplewood, NJ
- Millburn, NJ
- Short Hills, NJ

---

## Step 2: Email Verification (FREE)

### Script
`execution/verify_email.py`

### Command
```bash
python3 execution/verify_email.py --file leads.json --output verified_leads.json
```

### What It Checks
1. **Syntax** - Valid email format, not image files
2. **DNS/MX** - Domain has mail servers
3. **SMTP** - Optional mailbox verification (use --no-smtp for speed)

### Skip SMTP for Speed
```bash
python3 execution/verify_email.py --file leads.json --output verified.json --no-smtp
```

---

## Step 3: LinkedIn Discovery (FREE - Browser Automation)

### Method: Google X-Ray Search
Use browser automation to search Google with LinkedIn site operator.

### Search Query Format
```
site:linkedin.com/in "[Business Name]" owner OR founder OR CEO OR dentist
```

### Browser Subagent Task
```
1. Open Google
2. For each business:
   - Search: site:linkedin.com/in "[Business Name]" owner
   - Extract LinkedIn URLs from results
   - Save URL + person name + title
3. Return all LinkedIn URLs found
```

### Manual Alternative
If browser automation fails:
1. Go to google.com
2. Search: `site:linkedin.com/in "Business Name" owner`
3. Copy LinkedIn profile URLs from results

### Expected Hit Rate
- Small local businesses: 20-40%
- Professional services (dentists, med spas): 40-60%
- Tech companies: 70-90%

---

## Step 4: Anymailfinder Email Lookup (~$0.01-0.02/email)

### Script
`execution/anymailfinder_email.py`

### Command - Single LinkedIn URL
```bash
python3 execution/anymailfinder_email.py --linkedin "https://linkedin.com/in/username"
```

### Command - Name + Domain
```bash
python3 execution/anymailfinder_email.py --name "John Smith" --domain "company.com"
```

### Command - Bulk File
```bash
python3 execution/anymailfinder_email.py --file enriched_leads.json --output final_leads.json
```

### Cost
- **Only charged when email is found** (~$0.01-0.02)
- No charge if email not found
- Check credits at: anymailfinder.com/dashboard

### API Key
In `.env`:
```
ANYMAILFINDER_API_KEY=your_key_here
```

---

## Step 5: Website Trigger Analysis

### Script
Website scraping built into `generate_outreach_emails.py`

### Triggers to Look For
| Website Section | What to Find | Email Hook |
|-----------------|--------------|------------|
| Careers page | Hiring receptionist/admin | "Need a bridge solution while hiring?" |
| Footer/Contact | 24/7 claims but 9-5 hours | "How do you handle after-hours calls?" |
| News/Blog | Recent awards, expansion | "Congrats on the award—bet phones are ringing" |
| Contact form | Slow response time | "I submitted an inquiry and waited X hours" |

### Documentation
See: `directives/website_scraping_for_outreach.md`

---

## Step 6: Email Generation

### Script
`execution/generate_outreach_emails.py`

### Command
```bash
python3 execution/generate_outreach_emails.py --leads final_leads.json --sender "Tedca"
```

### Email Templates Used
Based on triggers found:
1. **Hiring Template** - "question about your receptionist post"
2. **After-Hours Template** - "after-hours dispatch question"
3. **Expansion Template** - "new [city] location"
4. **Operational Reality** - "missed calls at [company]"

### Required Links
Every email must include:
- **Free Demo:** tedca.org
- **Book a Call:** https://cal.com/ted-charles-enqyjn/30min
- **Signature:** Tedca

### Cost
- OpenRouter API: ~$0.01 per batch of 15 emails
- Cost cap: $1.00 (configurable)

---

## Step 7: Gmail Draft Creation

### Built into `generate_outreach_emails.py`

Automatically creates Gmail drafts using OAuth token in `token.json`.

### Manual Token Refresh
If token expires:
```bash
# Delete old token
rm token.json
# Run script again - will open browser for OAuth
python3 execution/generate_outreach_emails.py --leads leads.json
```

---

## Full Workflow Example

### 1. Scrape 50 Med Spas
```bash
curl -X POST "https://n8n.srv1080136.hstgr.cloud/webhook/..." \
  -d '["Med Spa in Union, NJ", "Med Spa in Elizabeth, NJ", ...]'
```
Save output to `.tmp/medspa_raw.json`

### 2. Verify Emails
```bash
python3 execution/verify_email.py --file .tmp/medspa_raw.json \
  --output .tmp/medspa_verified.json --no-smtp
```

### 3. Find LinkedIn (Browser Automation)
Use browser subagent to search Google for each business.
Goal: Find at least 20 LinkedIn URLs from 50 leads.

### 4. Get Decision-Maker Emails
```bash
python3 execution/anymailfinder_email.py --file .tmp/medspa_linkedin.json \
  --output .tmp/medspa_final.json
```

### 5. Generate & Send Emails
```bash
python3 execution/generate_outreach_emails.py --leads .tmp/medspa_final.json \
  --sender "Tedca"
```

---

## Cost Summary

| Step | Tool | Cost |
|------|------|------|
| N8N Scrape | N8N Webhook | FREE |
| Email Verify | verify_email.py | FREE |
| LinkedIn Search | Browser + Google | FREE |
| Owner Email | Anymailfinder | $0.01-0.02/found |
| Email Generation | OpenRouter | ~$0.01/15 emails |
| Gmail Drafts | Google API | FREE |

**Total for 50 leads:** ~$0.50-$1.00 (only charged for verified emails found)

---

## Files Reference

| File | Purpose |
|------|---------|
| `execution/verify_email.py` | Email verification |
| `execution/find_owner_linkedin.py` | Owner/LinkedIn finder |
| `execution/anymailfinder_email.py` | Anymailfinder API integration |
| `execution/generate_outreach_emails.py` | Email generation + Gmail drafts |
| `Plumber Outreach Email Setup Guide` | Email templates and strategy |
| `directives/website_scraping_for_outreach.md` | Website trigger guide |
| `directives/how_to_sell_ai_voice_receptionist.md` | Sales strategy |

---

## Troubleshooting

### N8N Webhook Error
- Check if workflow is active in N8N dashboard
- Try smaller batch of queries
- Check execution logs in N8N

### LinkedIn Search Returns Nothing
- Try different search terms (owner vs founder vs CEO)
- Use browser automation instead of script
- Some small businesses won't have LinkedIn

### Anymailfinder Credits
- Only charged for found emails
- Check dashboard for remaining credits
- Use sparingly - only for high-value leads

### Gmail Draft Errors
- Delete token.json and re-authenticate
- Check credentials.json is valid
- Ensure Gmail API is enabled in Google Cloud
