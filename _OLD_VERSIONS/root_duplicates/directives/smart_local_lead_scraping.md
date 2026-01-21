# Smart Local Lead Scraping Pipeline

**Last Updated:** January 4, 2026

---

## Overview

The Smart Local Lead Scraper finds local business leads within a specific geographic radius, ensuring all results are relevant to the target area. It uses:

1. **32,109 US city database** with GPS coordinates (free, from US Census)
2. **Proximity-based targeting** (10-mile radius by default)
3. **Adaptive batching** (sends N8N batches until target lead count met)
4. **JSON array batching** (sends multiple cities in ONE N8N request)

---

## How It Works

### Input
```
Industry: "Dentist"
Location: "Union, NJ"
Target: 100 leads
```

### Process

**Step 1: Location Expansion**
- Loads US city database (32K cities)
- Finds target city coordinates: Union, NJ → (40.6976, -74.2632)
- Calculates distance to all NJ cities using Haversine formula
- Returns cities within 10-mile radius, sorted by distance

Example Output:
```
1. Union, NJ (0.0 mi)
2. Hillside, NJ (1.8 mi)
3. Irvington, NJ (2.3 mi)
4. Springfield, NJ (3.1 mi)
5. Elizabeth, NJ (4.2 mi)
... (up to 100 nearby cities)
```

**Step 2: Adaptive Batching**
- Calculates cities needed: 100 leads ÷ 20 per city = 5 cities
- First round: over-provision by 30% → 7 cities
- Builds JSON array:
  ```json
  ["Dentist in Union, NJ", "Dentist in Hillside, NJ", ...]
  ```

**Step 3: Send to N8N**
- Sends ONE HTTP POST with JSON array of 7 queries
- N8N processes all 7 cities and returns combined results
- Example: Gets 89 leads

**Step 4: Check Target**
- Need 11 more leads
- Round 2: Calculate 11 ÷ 15 = 1 city
- Send batch with 1 query
- Get 18 more leads (total: 107)
- Trim to exactly 100

**Step 5: Deduplication & Save**
- Removes duplicate businesses (same place_id)
- Saves to `.tmp/n8n_leads_TIMESTAMP.json`

---

## Usage

### Command Line

```bash
# Basic usage
python3 execution/n8n_gmaps_scraper_smart.py \
  --industry "Dentist" \
  --location "Union, NJ" \
  --target-leads 100

# With custom radius
python3 execution/n8n_gmaps_scraper_smart.py \
  --industry "Plumber" \
  --location "Austin, TX" \
  --target-leads 50 \
  --radius 15

# Regional search
python3 execution/n8n_gmaps_scraper_smart.py \
  --industry "HVAC" \
  --location "North New Jersey" \
  --target-leads 200
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--industry` | Yes | - | Business type (e.g., "Dentist", "Plumber") |
| `--location` | Yes | - | City ("Union, NJ") or region ("North New Jersey") |
| `--target-leads` | No | 100 | Number of leads to collect |
| `--radius` | No | 10 | Search radius in miles |
| `--max-rounds` | No | 5 | Maximum batch rounds (safety limit) |
| `--output` | No | Auto | Output file path |

---

## Location Formats Supported

### 1. Specific City (Proximity Mode)
```bash
--location "Union, NJ"
--location "Austin, TX"
--location "Seattle, WA"
```
→ Finds cities within 10-mile radius

### 2. Predefined Regions
```bash
--location "North New Jersey"
--location "Central New Jersey"
--location "South New Jersey"
```
→ Uses curated list of cities in that region

### 3. County (Coming Soon)
```bash
--location "Essex County, NJ"
```

---

## Files

| File | Purpose |
|------|---------|
| `execution/n8n_gmaps_scraper_smart.py` | Main scraper script |
| `execution/us_cities.json` | 32K US city database (2.7MB) |
| `execution/download_us_cities.py` | Database builder (re-run to update) |
| `.tmp/n8n_leads_TIMESTAMP.json` | Output file |

---

## Technical Details

### Proximity Calculation

Uses **Haversine formula** to calculate great-circle distance:

```python
distance = 2 * R * arcsin(sqrt(
    sin²((lat2-lat1)/2) +
    cos(lat1) * cos(lat2) * sin²((lon2-lon1)/2)
))
```

Where R = 3959 miles (Earth's radius)

### Adaptive Batching Logic

**Round 1:**
```
Needed: 100 leads
Estimate: ~20 per city
Over-provision: 100 ÷ 20 × 1.3 = 7 cities
```

**Round 2+ (if needed):**
```
Remaining: 11 leads
Estimate: ~15 per city
Exact calculation: 11 ÷ 15 + 1 = 2 cities
```

**Safety Limits:**
- Max 10 cities per batch (N8N capacity)
- Max 5 rounds total (prevent infinite loops)
- Stops if run out of nearby cities

### N8N Batch Format

**Request:**
```json
POST https://n8n.srv1080136.hstgr.cloud/webhook/...
Content-Type: application/json

[
  "Dentist in Union, NJ",
  "Dentist in Hillside, NJ",
  "Dentist in Irvington, NJ"
]
```

**Response:**
```json
[
  {
    "name": "Union Dental",
    "address": "123 Main St, Union, NJ",
    "phone": "(908) 555-1234",
    "website": "https://uniondental.com",
    "email": "info@uniondental.com",
    "place_id": "ChIJ...",
    "rating": 4.8,
    "user_ratings_total": 142
  },
  ...
]
```

---

## Performance

| Target Leads | Expected Rounds | Time | Cities Queried |
|--------------|-----------------|------|----------------|
| 25 | 1 | ~30s | 2-3 |
| 50 | 1 | ~35s | 3-4 |
| 100 | 1-2 | ~45s | 5-7 |
| 200 | 2-3 | ~90s | 10-15 |
| 500 | 3-4 | ~180s | 25-30 |

---

## Regional Expansions

Predefined city lists for common regions:

```python
REGION_EXPANSION = {
    "north new jersey": [
        "Newark", "Jersey City", "Paterson", "Elizabeth",
        "Clifton", "Passaic", "Union City", "Bayonne",
        "East Orange", "Hackensack"
    ],
    "central new jersey": [
        "Edison", "Woodbridge", "New Brunswick", "Perth Amboy",
        "Sayreville", "East Brunswick", "Old Bridge", "Piscataway"
    ],
    "south new jersey": [
        "Camden", "Cherry Hill", "Trenton", "Atlantic City",
        "Vineland", "Gloucester", "Pennsauken"
    ]
}
```

To add more regions, edit this dict in `n8n_gmaps_scraper_smart.py`.

---

## Troubleshooting

### "City not found in database"
**Solution:** Check spelling and format. Must be "City, STATE" (e.g., "Union, NJ" not "Union New Jersey")

### "No cities found"
**Solution:**
1. Increase `--radius` (try 20 miles)
2. Use a larger city nearby
3. Check if city exists: `grep "Union, NJ" execution/us_cities.json`

### "Ran out of cities"
**Solution:** Target too high for rural area. Either:
- Increase radius: `--radius 25`
- Lower target: `--target-leads 50`
- Use regional search

### "N8N timeout"
**Solution:** Batch too large. The script auto-caps at 10 cities per batch, but if still timing out:
- Check N8N workflow is running
- Reduce batch size in code (line 337: change `min(cities_needed, 10)` to `min(cities_needed, 5)`)

---

## Cost

- **US City Database:** $0 (free from US Census)
- **Proximity Calculations:** $0 (pure math, local)
- **N8N Scraping:** $0 (assuming you control N8N)
- **Total:** $0

---

## Next Steps

After scraping, leads flow through:

1. **Email Verification** → `execution/verify_email.py`
2. **Owner LinkedIn Discovery** → `execution/find_owner_linkedin.py` or Apollo.io
3. **Owner Email Lookup** → `execution/anymailfinder_email.py`
4. **AI Email Generation** → `execution/generate_outreach_emails.py`

See `directives/full_lead_enrichment_pipeline.md` for complete workflow.

---

## Changelog

**v2.0 - January 4, 2026**
- Added 32K US city database (all 50 states)
- Proximity-based targeting (Haversine formula)
- Adaptive batching (sends batches until target met)
- JSON array batching to N8N (not individual requests)
- Regional expansion support

**v1.0 - Previous**
- Basic sequential scraping (one city at a time)
- Hard-coded city lists
- No proximity calculation
