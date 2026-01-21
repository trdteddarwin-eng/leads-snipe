# AI-Powered Lead Scraper

## Overview

This directive describes the **AI-powered Google Maps lead scraper** that uses a FREE LLM (Llama 3.3 70B) to dynamically generate nearby cities for local business search. This eliminates the need for static city databases and enables global coverage.

**Key Innovation**: Instead of maintaining a database of 30,000+ US cities, we ask a FREE AI to generate relevant nearby cities on-demand for any location query.

## Tool

**Script**: `execution/n8n_gmaps_scraper_ai.py`

## What It Does

1. **User provides search intent**:
   - Industry: "Dentist", "Plumber", "HVAC", "Med Spa", etc.
   - Location: "New Jersey", "Phoenix area", "North NJ", "Austin, TX", etc.
   - Target: Number of leads desired (e.g., 100)

2. **AI generates nearby cities dynamically**:
   - Uses `meta-llama/llama-3.3-70b-instruct:free` via OpenRouter
   - Asks: "Give me 5 major cities for local business search in New Jersey"
   - Returns: `["Newark, NJ", "Jersey City, NJ", "Paterson, NJ", ...]`
   - **100% FREE** - no API costs

3. **Adaptive batching with city tracking**:
   - Sends queries to N8N webhook sequentially (one at a time to avoid timeouts)
   - Tracks used cities to avoid duplicates
   - Keeps requesting more cities from AI until target leads met
   - Maximum 5 rounds to prevent infinite loops

4. **Query format**:
   - Combines industry + location in single string
   - Example: `"Dentist in Newark, NJ"`
   - Sends as JSON array to N8N: `["Dentist in Newark, NJ"]`

5. **Deduplication and cleaning**:
   - Tracks `place_id` or MD5 hash of name+address
   - Validates emails (filters out images, invalid formats)
   - Adds metadata: `scraped_at` timestamp

## Inputs

### Required
- `--industry` or `-i`: Business type (e.g., "Dentist", "Plumber")
- `--location` or `-l`: Target location (e.g., "New Jersey", "Phoenix area", "Union, NJ")
- `--target-leads` or `-t`: Number of leads to collect (default: 100)

### Optional
- `--max-rounds`: Maximum batch rounds (default: 5)
- `--output` or `-o`: Output JSON file path (default: `.tmp/leads_[timestamp].json`)

## Outputs

**JSON file** with lead data:
```json
[
  {
    "name": "Dental Health Associates, P.A.",
    "address": "9-25 Alling St, Newark, NJ 07102, United States",
    "place_id": "ChIJZ1zgb4NTwokRL-zmyBkq3LM",
    "rating": 3.6,
    "user_ratings_total": 263,
    "types": "dentist, doctor, health, point_of_interest, establishment",
    "phone": "(973) 297-1550",
    "website": "http://njdha.com/",
    "email": "info@njdha.com",
    "scraped_text": "...",
    "scraped_meta": "...",
    "scraped_at": "2026-01-04T22:27:22.444251"
  }
]
```

## Usage Examples

### Basic usage
```bash
python3 execution/n8n_gmaps_scraper_ai.py \
  --industry "Dentist" \
  --location "New Jersey" \
  --target-leads 100
```

### Specific city with radius
```bash
python3 execution/n8n_gmaps_scraper_ai.py \
  --industry "Plumber" \
  --location "Phoenix area" \
  --target-leads 50
```

### Regional search
```bash
python3 execution/n8n_gmaps_scraper_ai.py \
  --industry "HVAC" \
  --location "North New Jersey" \
  --target-leads 200
```

### Custom output path
```bash
python3 execution/n8n_gmaps_scraper_ai.py \
  --industry "Med Spa" \
  --location "Austin, TX" \
  --target-leads 75 \
  --output ".tmp/medspa_austin.json"
```

## How It Works (Technical Flow)

### Round 1: Over-provisioning
1. User wants 100 leads
2. Calculate: `(100 / 20) * 1.3 = 6.5 → 7 cities` (30% buffer)
3. Cap at 15 cities max to avoid N8N timeout
4. Ask AI: "Give me 7 cities in New Jersey"
5. AI returns: `["Newark, NJ", "Jersey City, NJ", "Paterson, NJ", ...]`
6. Build queries: `["Dentist in Newark, NJ", "Dentist in Jersey City, NJ", ...]`
7. Send queries to N8N **sequentially** (one at a time)
8. Collect results, deduplicate
9. Total: 45 leads collected

### Round 2: Conservative estimation
1. Still need: 55 leads
2. Calculate: `55 / 15 + 1 = 4.67 → 5 cities`
3. Ask AI: "Give me 5 cities in New Jersey, EXCLUDE: [Newark, Jersey City, ...]"
4. AI returns new cities: `["Elizabeth, NJ", "Edison, NJ", ...]`
5. Send queries sequentially
6. Total: 85 leads collected

### Round 3-5: Continue until target met or max rounds reached

## AI City Generation

### Prompt Template
```python
f"""Generate {num_cities} major cities for local business search in: "{location_query}"

EXCLUDE these cities (already used): {exclude_cities}

Return ONLY a valid JSON array of city names with state codes.
Format: ["City, STATE", "City, STATE", ...]

Example for "New Jersey":
["Newark, NJ", "Jersey City, NJ", "Paterson, NJ", "Elizabeth, NJ", "Edison, NJ"]

Example for "Phoenix area":
["Phoenix, AZ", "Scottsdale, AZ", "Tempe, AZ", "Mesa, AZ", "Chandler, AZ"]

Location: "{location_query}"
JSON array:"""
```

### LLM Model
- **Model**: `meta-llama/llama-3.3-70b-instruct:free`
- **Provider**: OpenRouter
- **Cost**: $0.00 (FREE tier)
- **API Key**: `OPENROUTER_API_KEY` from `.env`

## N8N Webhook Integration

### Endpoint
```
https://n8n.srv1080136.hstgr.cloud/webhook/c66d6d2a-f22d-4fb6-b874-18ae5915347b
```

### Request Format
```python
POST https://n8n.srv1080136.hstgr.cloud/webhook/...
Content-Type: application/json

["Dentist in Newark, NJ"]
```

**IMPORTANT**: Send ONE query at a time as a JSON array with single element. N8N times out on batch arrays with multiple cities.

### Response Format
```json
[
  {
    "name": "...",
    "address": "...",
    "place_id": "...",
    "rating": 4.5,
    "user_ratings_total": 100,
    "types": "dentist, doctor, health",
    "phone": "(555) 123-4567",
    "website": "https://example.com",
    "email": "contact@example.com",
    "scraped_text": "...",
    "scraped_meta": "..."
  }
]
```

## Error Handling

### Common Issues

**Issue**: Most cities return empty results
- **Cause**: Google Maps data availability varies by city, or N8N rate limiting
- **Solution**: AI will keep requesting more cities until target met

**Issue**: LLM returns malformed JSON
- **Cause**: LLM includes markdown code blocks or extra text
- **Solution**: Script automatically strips markdown and extracts JSON

**Issue**: N8N timeout
- **Cause**: Batch requests with multiple cities overwhelm N8N
- **Solution**: Send queries sequentially, one at a time

**Issue**: API key not found
- **Cause**: `OPENROUTER_API_KEY` missing from `.env`
- **Solution**: Add key to `.env` file

## Performance

### Typical Metrics
- **Speed**: ~5-10 seconds per city (N8N processing time)
- **Success rate**: ~20% of cities return results (varies by location/industry)
- **Average leads per city**: 15-25 leads
- **Email coverage**: 80-100% (N8N scrapes websites for emails)
- **Cost**: **$0.00** (100% FREE - no API costs)

### Example Run
```
Input: "Find 100 dentists in New Jersey"

Round 1: 7 cities → 45 leads
Round 2: 5 cities → 30 leads
Round 3: 3 cities → 25 leads
Total: 15 cities queried, 100 leads collected

Time: ~2-3 minutes
Cost: $0.00
```

## Advantages Over Database Approach

### OLD: Static City Database
- ❌ Requires downloading/maintaining 30,000+ US cities
- ❌ File size: ~5MB for coordinates
- ❌ Limited to predefined locations
- ❌ No global coverage (US-only)
- ❌ Needs periodic updates

### NEW: AI-Powered Dynamic Generation
- ✅ No database needed - works instantly
- ✅ Global coverage (any country, any location)
- ✅ Always up-to-date (LLM has recent knowledge)
- ✅ Handles ambiguous queries ("Phoenix area", "North NJ")
- ✅ 100% FREE (no API costs)
- ✅ Simple codebase (200 lines vs 1000+ lines)

## Next Steps

After scraping leads, use the enrichment pipeline:

1. **Verify Emails**: `execution/verify_email.py` (FREE)
2. **Find Owner LinkedIn**: `execution/find_owner_linkedin.py` (requires Apollo/browser automation)
3. **Get Owner Email**: AnyMailFinder API ($0.20/email found)
4. **Generate Outreach**: OpenRouter + FREE LLM

Full pipeline: `directives/full_lead_enrichment_pipeline.md`

## Dependencies

### Python Packages
```bash
pip install requests python-dotenv
```

### Environment Variables
```bash
# .env file
OPENROUTER_API_KEY=sk-or-v1-...
```

### External Services
- **N8N Webhook**: Free Google Maps scraping (hosted)
- **OpenRouter**: Free LLM API (Llama 3.3 70B)

## Testing

### Quick Test (20 leads)
```bash
python3 execution/n8n_gmaps_scraper_ai.py \
  --industry "Dentist" \
  --location "New Jersey" \
  --target-leads 20
```

Expected output:
```
======================================================================
🤖 AI-POWERED LEAD SCRAPER
======================================================================
Industry: Dentist
Location: New Jersey
Target: 20 leads
Max rounds: 5

──────────────────────────────────────────────────────────────────────
📦 ROUND 1
──────────────────────────────────────────────────────────────────────
Need: 20 more leads
Requesting: 3 cities
   🤖 Asking AI for 3 cities in 'New Jersey'...
   ✅ AI generated: ['Newark, NJ', 'Jersey City, NJ', 'Paterson, NJ']
   🚀 Sending 3 queries to N8N sequentially...
      [1/3] Dentist in Newark, NJ... ✅ 6 leads
      [2/3] Dentist in Jersey City, NJ... ❌ No results
      [3/3] Dentist in Paterson, NJ... ❌ No results

   ✅ Got 6 results, 6 new leads
   📊 Total: 6/20 leads

[... continues until target reached ...]

======================================================================
✅ SCRAPING COMPLETE
======================================================================
Rounds: 3
Cities queried: 8
Total leads: 20
Leads with email: 20 (100%)

💾 Saved 20 leads to: .tmp/leads_20260104_222736.json

🎉 Done! 20 leads from New Jersey
```

## Edge Cases

### Empty Location
- **Input**: `--location ""`
- **Behavior**: AI may return generic major US cities
- **Recommendation**: Always provide specific location

### Very Small Target
- **Input**: `--target-leads 5`
- **Behavior**: May over-fetch (AI requests minimum 3 cities)
- **Result**: Script trims to exact target

### Very Large Target
- **Input**: `--target-leads 10000`
- **Behavior**: Will stop after 5 rounds (max_rounds limit)
- **Recommendation**: Run multiple times with different regions

### Non-US Locations
- **Input**: `--location "London, UK"`
- **Behavior**: AI should generate UK cities
- **Status**: ✅ Works globally (N8N supports international Google Maps)

## Troubleshooting

### No leads collected
1. Check N8N webhook is online: `curl https://n8n.srv1080136.hstgr.cloud/webhook/...`
2. Verify OpenRouter API key: `echo $OPENROUTER_API_KEY`
3. Try different location/industry combination
4. Check `.tmp/` folder for partial results

### LLM returns invalid cities
1. AI sometimes hallucinates city names
2. N8N will return empty results for invalid cities
3. System will request more cities automatically

### Slow performance
1. N8N processes ~1 query per 5-10 seconds
2. For 100 leads, expect ~2-5 minutes total
3. Consider running multiple instances in parallel for different regions

## Future Improvements

1. **Parallel N8N requests**: Test if N8N can handle 3-5 concurrent queries
2. **Better city validation**: Ask AI to verify cities exist before querying
3. **Proximity intelligence**: Ask AI to prioritize nearby cities based on first successful city
4. **Industry-specific cities**: "Find cities with high dentist demand in New Jersey"
5. **Fallback models**: If Llama fails, try other free models (Mixtral, etc.)

## Conclusion

This AI-powered approach eliminates the complexity of maintaining city databases while providing better flexibility, global coverage, and zero cost. The system is self-healing - if a city fails, it simply requests more cities from the AI until the target is met.

**Key Metrics**:
- ✅ 100% FREE (no API costs)
- ✅ Global coverage (any location worldwide)
- ✅ No database maintenance required
- ✅ Adaptive batching (automatically adjusts to N8N response rates)
- ✅ Production-ready (handles errors, deduplication, validation)
