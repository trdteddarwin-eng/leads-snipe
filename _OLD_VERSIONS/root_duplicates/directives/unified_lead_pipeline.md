# Unified Lead Generation Pipeline

> Optimized, fast, and reliable lead generation with guaranteed email verification, LinkedIn discovery, and strategic personalization.

## Overview

The Unified Pipeline is an optimized lead generation system that **ALWAYS** runs:
1. **Email Verification** (FREE 3-layer: Syntax + DNS/MX + SMTP)
2. **LinkedIn Discovery** (FREE multi-strategy: HTML + DuckDuckGo + Google)
3. **Icebreaker Engine** (Regex-first, AI-second personalization)

**Performance**: 200 leads in 3-5 minutes
**Cost**: ~$0.50-1.00 per 200 leads (SerpAPI only)

## Architecture

```
Input: Industry + Location + Target (200+)
           |
           v
+--------------------------------------+
|  STAGE 1: Lead Discovery             |
|  Engine Zero (SerpAPI, 50 workers)   |
|  + Haversine city expansion          |
|  -> 250+ raw leads with websites     |
+--------------------------------------+
           |
           v
+--------------------------------------+
|  STAGE 2: Email Verification (FREE)  |
|  20 parallel workers                 |
|  Syntax -> DNS/MX -> SMTP            |
|  -> Leads with email_verified flag   |
+--------------------------------------+
           |
           v
+--------------------------------------+
|  STAGE 3: LinkedIn Discovery (FREE)  |
|  10 workers, multi-strategy:         |
|  1. HTML extract from scraped text   |
|  2. DuckDuckGo search                |
|  3. Google HTML fallback             |
|  -> Leads with linkedin_url          |
+--------------------------------------+
           |
           v
+--------------------------------------+
|  STAGE 4: Paid Fallback (OPTIONAL)   |
|  Anymailfinder for failed SMTP only  |
|  Cost-capped at $2 per hunt          |
+--------------------------------------+
           |
           v
+--------------------------------------+
|  STAGE 5: Icebreaker Engine          |
|  Regex Sniper (zero-cost patterns)   |
|  AI Compliment (Gemini/GPT fallback) |
|  -> Leads with icebreaker field      |
+--------------------------------------+
           |
           v
Output: 200+ enriched leads
- email (verified)
- linkedin_url
- owner_name
- icebreaker (personalized opener)
```

## Files

### New Files (Created)

| File | Purpose |
|------|---------|
| `execution/unified_pipeline.py` | Main orchestrator with all stages |
| `execution/rate_limiter.py` | Adaptive rate limiting with User-Agent rotation |
| `execution/linkedin_finder_unified.py` | Consolidated FREE LinkedIn discovery |
| `execution/icebreaker_engine.py` | Regex-first, AI-second personalization |

### Modified Files

| File | Changes |
|------|---------|
| `execution/verify_email.py` | Added `verify_batch()` for parallel verification |
| `execution/leadsnipe_api.py` | Integrated unified pipeline as default |

## Usage

### CLI Usage

```bash
# Basic usage (200 leads)
python3 execution/unified_pipeline.py --industry "Dentist" --location "Newark, NJ"

# Custom target
python3 execution/unified_pipeline.py -i "Plumber" -l "Union, NJ" -t 300

# Enable paid fallback
python3 execution/unified_pipeline.py -i "HVAC" -l "Edison, NJ" --paid-fallback --max-spend 3.0

# Skip SMTP verification (faster, less accurate)
python3 execution/unified_pipeline.py -i "Dentist" -l "Newark, NJ" --no-smtp
```

### API Usage

The LeadSnipe API (`leadsnipe_api.py`) now uses the unified pipeline by default:

```bash
# Start server
python3 execution/leadsnipe_api.py

# Create hunt (uses unified pipeline)
curl -X POST http://localhost:8000/api/hunt \
  -H "Content-Type: application/json" \
  -d '{"niche": "Dentist", "location": "Newark, NJ", "limit": 200}'
```

### Python Import

```python
from unified_pipeline import UnifiedPipeline, PipelineConfig

config = PipelineConfig(
    target_leads=200,
    enable_email_verification=True,  # Always ON
    enable_linkedin_discovery=True,  # Always ON
    enable_paid_fallback=False,      # Optional
)

pipeline = UnifiedPipeline(config)
leads = pipeline.run("Dentist", "Newark, NJ")

# Each lead has:
# - email (str or None)
# - email_verified (bool)
# - linkedin_url (str or None)
# - owner_name (str or None)
```

## Rate Limiting Strategy

The pipeline uses adaptive rate limiting to avoid bans:

| Target | Rate Limit | Base Delay |
|--------|------------|------------|
| SerpAPI | 5 req/sec | 0.2s |
| Website scrape | 3 req/domain/min | 1.0s |
| DuckDuckGo | 30 req/min | 2.0s |
| Google HTML | 10 req/min | 3.0s |
| SMTP verify | 2 conn/server | 0.5s |

### Anti-Ban Features

- **User-Agent Rotation**: Pool of 20+ real browser agents (Chrome/Safari weighted)
- **Adaptive Backoff**: Doubles delay on 429/503, gradually reduces on success
- **Per-Domain Throttling**: Tracks requests per domain, enforces limits
- **Referer Headers**: Appropriate referer for search engines

## Email Verification Details

### 3-Layer FREE Verification

1. **Syntax Check** (instant)
   - RFC 5322 regex validation
   - Filters junk patterns (noreply@, images, hashes)
   - Blocks disposable domains

2. **DNS/MX Check** (instant)
   - Verifies domain exists
   - Checks MX records for mail servers
   - Caches results by domain

3. **SMTP Check** (slow, ~2-5s per email)
   - Connects to mail server
   - Verifies mailbox exists via RCPT TO
   - **Limitation**: ~10-20% false negatives on Gmail/Microsoft (they block SMTP verification)

### Verification Results

```json
{
  "email": "john@example.com",
  "email_verified": true,
  "email_verification": {
    "valid": true,
    "deliverable": true,
    "reason": "Verified"
  }
}
```

## LinkedIn Discovery Details

### Multi-Strategy FREE Approach

1. **HTML Extraction** (instant)
   - Scans scraped website text for LinkedIn URLs
   - No network request needed
   - Highest priority (fastest)

2. **DuckDuckGo Search** (2-3s)
   - Searches `"{business_name}" owner linkedin`
   - Uses HTML endpoint (no API limits)
   - Extracts owner name from results

3. **Google HTML Fallback** (3-5s)
   - Used if DuckDuckGo fails
   - More aggressive rate limiting
   - Site-restricted search

### Success Rates

| Strategy | Success Rate |
|----------|--------------|
| HTML Extract | 10-20% |
| DuckDuckGo | 40-50% |
| Google Fallback | 10-20% |
| **Combined** | **60-80%** |

## Cost Breakdown

### FREE Tier (Default)

| Component | Cost |
|-----------|------|
| SerpAPI (Engine Zero) | ~$0.50-1.00 (250 searches @ $0.004/search) |
| Website Scraping | $0 |
| Email Verification | $0 |
| LinkedIn Discovery | $0 |
| **TOTAL** | **$0.50-1.00** |

### With Paid Fallback (Optional)

| Component | Cost |
|-----------|------|
| FREE tier | $0.50-1.00 |
| Anymailfinder | $0-2.00 (capped, only for failed SMTP) |
| **TOTAL** | **$0.50-3.00** |

## Configuration Options

```python
@dataclass
class PipelineConfig:
    # Target
    target_leads: int = 200

    # Workers
    discovery_workers: int = 5      # SerpAPI calls
    scraping_workers: int = 50      # Website scraping
    verification_workers: int = 20  # Email verification
    linkedin_workers: int = 10      # LinkedIn discovery
    icebreaker_workers: int = 10    # Personalization

    # Features (DO NOT DISABLE)
    enable_email_verification: bool = True  # Always ON
    enable_linkedin_discovery: bool = True  # Always ON
    enable_icebreaker: bool = True          # Strategic personalization
    enable_paid_fallback: bool = False      # Optional

    # Budget (only if paid fallback enabled)
    paid_fallback_max_spend: float = 2.0

    # Verification
    do_smtp_check: bool = True  # Set False for faster, less accurate
```

## Output Format

Each lead in the output includes:

```json
{
  "id": "ChIJ...",
  "name": "ABC Dental",
  "address": "123 Main St, Newark, NJ 07102",
  "phone": "(973) 555-1234",
  "website": "https://abcdental.com",
  "email": "info@abcdental.com",
  "email_verified": true,
  "email_verification_reason": "Verified",
  "rating": 4.5,
  "user_ratings_total": 127,
  "linkedin_url": "https://linkedin.com/in/john-smith",
  "owner_name": "John Smith",
  "owner_first_name": "John",
  "linkedin_source": "duckduckgo",
  "icebreaker": "I noticed you've been serving the community since 1984—that's incredible longevity.",
  "scraped_text": "Welcome to ABC Dental...",
  "scraped_at": "2026-01-13T10:30:00"
}
```

## Icebreaker Engine

The Icebreaker Engine generates human-like personalized opening lines for cold outreach.

### Philosophy: Regex-First, AI-Second

1. **Regex Sniper (Zero Cost)**: Pattern matching for common hooks
2. **AI Compliment (Low Cost)**: LLM fallback for unique compliments
3. **Location Fallback**: When website is unreachable

### Regex Patterns (Zero Cost)

| Pattern | Example Match | Template |
|---------|---------------|----------|
| Years in Business | "Since 1984" | "I noticed you've been serving the community since {year}—that's incredible longevity." |
| Family Owned | "family-owned" | "I love that you're a family-owned and operated business—those local roots really matter." |
| Awards | "voted best" | "Congrats on being recognized as one of the best in your industry—well deserved." |

### AI Fallback (Low Cost)

When regex patterns don't match, the engine uses a fast AI model:
- **Model**: `google/gemini-2.0-flash-exp:free` (via OpenRouter)
- **Prompt**: Extracts ONE specific compliment under 15 words
- **Cost**: ~$0.0001 per lead (effectively free)

### Example Icebreakers

```
"I noticed you guys have been serving the community since 1984—that's incredible longevity."
"I love that you're a family-owned and operated business—those local roots really matter."
"Congrats on being recognized as one of the best in your industry—well deserved."
"I noticed you specialize in high-efficiency heat pumps—rare to find that expertise locally."
```

### Configuration

```python
enable_icebreaker: bool = True      # Enable/disable icebreaker generation
icebreaker_workers: int = 10        # Parallel workers for async scraping
```

## Troubleshooting

### No Leads Found

1. Check SerpAPI key is valid: `echo $SERPAPI_API_KEY`
2. Try a different location (more populated area)
3. Try a different industry

### Low Email Verification Rate

1. Enable SMTP check: `do_smtp_check=True`
2. Expected rate: 80-90% (Gmail/Microsoft may block SMTP)
3. Consider paid fallback for unverified emails

### Low LinkedIn Discovery Rate

1. Ensure `scraped_text` is populated (from Engine Zero)
2. Expected rate: 60-80%
3. Check rate limiter stats for blocks

### Rate Limited

1. The pipeline automatically adapts delays
2. Check `rate_limiter.get_stats()` for current delays
3. Wait 5-10 minutes if heavily rate limited

## Switching Back to Legacy Pipeline

If needed, you can switch back to the legacy pipeline:

1. Edit `execution/leadsnipe_api.py`
2. Change line ~1887:
   ```python
   target=run_pipeline_with_logging,  # Legacy
   # target=run_unified_pipeline,     # Optimized
   ```

## Success Metrics

The unified pipeline should achieve:

- [ ] 200 leads generated per hunt
- [ ] 80-90% email verification rate (FREE)
- [ ] 60-80% LinkedIn discovery rate (FREE)
- [ ] No rate limit errors (429/503)
- [ ] Total cost under $1.50 per 200 leads
