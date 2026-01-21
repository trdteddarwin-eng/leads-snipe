# N8N Google Maps Free Lead Scraper

Generate local business leads from Google Maps using the free N8N webhook workflow. No Apify costs.

## Overview

This pipeline scrapes Google Maps for local businesses using a self-hosted N8N workflow. Since each webhook call returns only **10-25 leads**, the script automatically generates **multiple location variations** and loops through them to maximize lead volume.

## Webhook Details

**Webhook URL:** `https://n8n.srv1080136.hstgr.cloud/webhook/c66d6d2a-f22d-4fb6-b874-18ae5915347b`

**Input Format:** Plain text query (POST body or query param)
- Example: `Dentist in Elizabeth, NJ`
- Example: `HVAC contractor in Newark, NJ`

**Output Format:** JSON array of businesses
```json
[
  {
    "name": "Business Name",
    "address": "Full address with city, state, zip",
    "place_id": "Google Place ID (for deduplication)",
    "rating": 4.6,
    "user_ratings_total": 123,
    "types": "dentist, doctor, health, point_of_interest, establishment",
    "phone": "(908) 469-9100",
    "website": "https://example.com/",
    "email": "contact@example.com"
  }
]
```

## When to Use

- Building lead lists for local service businesses (FREE, no Apify costs)
- Prospecting for AI voice receptionist, appointment reminders, etc.
- Generating leads in specific geographic areas
- When budget is a concern and you want to avoid per-lead costs

## Inputs

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--industry` | Yes | Business type (e.g., "Dentist", "Plumber", "HVAC contractor") |
| `--state` | Yes | State to target (e.g., "NJ", "New Jersey", "TX") |
| `--cities` | No | Comma-separated list of specific cities (auto-generates if omitted) |
| `--target-leads` | No | Target number of leads (default: 100, will loop until reached) |
| `--output` | No | Output file path (default: `.tmp/leads_[timestamp].json`) |
| `--sheet-url` | No | Google Sheet URL to append results |

## Execution

```bash
# Basic usage - auto-generates city variations for the state
python3 execution/n8n_gmaps_scraper.py --industry "Dentist" --state "NJ" --target-leads 100

# With specific cities
python3 execution/n8n_gmaps_scraper.py --industry "HVAC contractor" --state "NJ" \
  --cities "Newark,Jersey City,Paterson,Elizabeth,Trenton"

# Output to Google Sheet
python3 execution/n8n_gmaps_scraper.py --industry "Plumber" --state "NJ" \
  --target-leads 200 --sheet-url "https://docs.google.com/spreadsheets/d/..."
```

## Output Schema (9 fields)

| Field | Description |
|-------|-------------|
| `name` | Business name |
| `address` | Full street address with city, state, zip |
| `place_id` | Google Place ID (used for deduplication) |
| `rating` | Google rating (1-5 stars) |
| `user_ratings_total` | Number of reviews |
| `types` | Business categories (comma-separated) |
| `phone` | Phone number |
| `website` | Website URL (may be null) |
| `email` | Email address (may be null or invalid) |

## City Variation Strategy

Since each webhook call returns ~10-25 leads, the script uses **geographic expansion**:

### For New Jersey (NJ):
```
Newark, Jersey City, Paterson, Elizabeth, Trenton,
Edison, Woodbridge, Lakewood, Toms River, Hamilton,
Clifton, Camden, Brick, Cherry Hill, Passaic,
Union City, Bayonne, East Orange, Vineland, New Brunswick,
Hoboken, Perth Amboy, West New York, Plainfield, Hackensack,
Sayreville, Kearny, Linden, Atlantic City, Morristown
```

### For Other States:
The script includes pre-configured city lists for:
- **Texas (TX)**: Houston, Dallas, Austin, San Antonio, Fort Worth, etc.
- **California (CA)**: Los Angeles, San Diego, San Jose, San Francisco, etc.
- **Florida (FL)**: Miami, Orlando, Tampa, Jacksonville, etc.
- **New York (NY)**: New York City, Buffalo, Rochester, Syracuse, etc.
- **Pennsylvania (PA)**: Philadelphia, Pittsburgh, Allentown, etc.

## Pipeline Logic

1. **Parse Inputs** - Get industry, state, target lead count
2. **Generate Queries** - Create list of `"{industry} in {city}, {state}"` queries
3. **Loop & Scrape** - Call webhook for each query, collect results
4. **Deduplicate** - Use `place_id` to remove duplicates across queries
5. **Continue Until Target** - Keep looping through cities until target reached
6. **Clean Emails** - Filter out invalid emails (images, placeholders)
7. **Output** - Save to JSON and/or Google Sheet

## Cost Considerations

| Component | Cost |
|-----------|------|
| N8N Webhook | **FREE** (self-hosted) |
| Google Sheets API | FREE |
| **Total** | **$0.00** |

This is the **zero-cost** alternative to the Apify-based pipeline.

## Deduplication

Leads are deduplicated by `place_id` (Google's unique identifier). This prevents counting the same business twice when it appears in searches for nearby cities.

## Email Validation

The webhook sometimes returns invalid emails (image filenames, placeholders). The script filters out:
- Emails ending in `.png`, `.jpg`, etc.
- Generic placeholders like `example@email.com`
- Emails without valid format

## Troubleshooting

### "No leads found"
- Check that the webhook is running (N8N workflow must be active)
- Verify the query format: `{industry} in {city}, {state}`
- Try a different city or industry

### "Webhook timeout"
- N8N workflow may be slow; increase timeout in script
- Check N8N server status

### "Duplicate leads only"
- You've already scraped this area; try different cities
- The area may have limited businesses

### "Invalid email addresses"
- Many are image filenames or placeholders
- Script auto-filters these; remaining emails are valid

## Rate Limiting

To avoid overwhelming the N8N server:
- Default: 2-second delay between webhook calls
- Configurable via `--delay` argument

## Learnings

- Webhook returns 10-25 leads per query on average
- City variations are essential to reach 100+ leads
- `place_id` is the reliable deduplication key
- Some emails are invalid (images, placeholders) - filter them
- Nearby cities often return overlapping results - dedup handles this
- Rating/review count can be used to filter quality leads

## Files

- `execution/n8n_gmaps_scraper.py` - Main scraping script
- `execution/update_sheet.py` - Google Sheet upload (reused)

## Related Directives

- `gmaps_lead_generation.md` - Apify-based version (paid, more features)
- `scrape_leads.md` - General lead scraping with verification
