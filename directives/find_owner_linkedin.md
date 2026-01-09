# Owner & LinkedIn Finder

## Purpose
Find business owner names and LinkedIn profiles to personalize cold outreach without paid APIs.

## Tool
**Script:** `execution/find_owner_linkedin.py`

## How It Works

### Step 1: Website Scraping (Owner Name)
Scrapes company website for owner/founder name:
- Checks About page, Team page, Leadership page
- Looks for keywords: owner, founder, president, CEO
- Extracts names near these keywords

### Step 2: Search Engine Lookup (LinkedIn)
Searches Google/DuckDuckGo for LinkedIn profile:
- Query: `"[Owner Name]" "[Business Name]" site:linkedin.com/in`
- Parses search results for LinkedIn URLs
- Falls back to DuckDuckGo if Google blocks

## Usage

### Single Business Lookup
```bash
python3 execution/find_owner_linkedin.py --business "First Class Electric" --website "https://firstclasselectricnj.com"
```

### Bulk Enrichment (Leads File)
```bash
python3 execution/find_owner_linkedin.py --file leads.json --output enriched_leads.json
```

### With Custom Delay
```bash
python3 execution/find_owner_linkedin.py --file leads.json --delay 3
```

## Output Format

### Single Lookup
```json
{
  "owner_name": "John Smith",
  "owner_first_name": "John",
  "linkedin_url": "https://linkedin.com/in/johnsmith",
  "source": "google_search",
  "names_found": ["John Smith", "Jane Doe"]
}
```

### Bulk Enrichment
Adds fields to each lead:
```json
{
  "name": "Business Name",
  "email": "contact@business.com",
  "owner_name": "John Smith",
  "owner_first_name": "John",
  "linkedin_url": "https://linkedin.com/in/johnsmith",
  "owner_source": "website"
}
```

## What It Finds

| Source | Success Rate | Best For |
|--------|--------------|----------|
| **Website "About" page** | 30-50% | Small businesses with owner bios |
| **Website "Team" page** | 20-30% | Companies with team listings |
| **Google search** | 10-20%* | Finding LinkedIn profiles |
| **DuckDuckGo search** | 10-20%* | Backup when Google blocks |

*Note: Search engines may block automated requests

## Known Limitations

### 1. Search Engine Blocking
Google and DuckDuckGo detect and block automated searches:
- Results may be empty even when profiles exist
- Rate limiting helps but doesn't guarantee access
- Consider using a browser automation approach for higher success

### 2. Website Structure Varies
Some websites don't have owner information:
- Large corporations don't list owners
- Some businesses only list company info
- False positives occur (CTA buttons, navigation)

### 3. False Positives
The name extraction may pick up:
- Business names instead of person names
- Call-to-action buttons ("Get Started", "Save Now")
- Service descriptions

**Mitigation:** Review results before using in emails

## Best Practices

1. **Use owner_first_name for emails** - More personal than full name
2. **Fallback to generic greeting** - If no name found, use "Hi there"
3. **Review before sending** - Some names may be incorrect
4. **Rate limit requests** - 2-3 second delay between lookups
5. **Prioritize website scraping** - More reliable than search

## Integration with Email Generation

```python
from find_owner_linkedin import find_owner_linkedin

# Get owner info
owner_info = find_owner_linkedin(
    business_name=lead["name"],
    website=lead.get("website"),
    address=lead.get("address")
)

# Use in email greeting
if owner_info.get("owner_first_name"):
    greeting = f"Hi {owner_info['owner_first_name']},"
else:
    greeting = "Hi there,"
```

## Alternative Approaches (If Needed)

For higher success rates, consider:

### 1. Browser Automation (Playwright/Selenium)
- Mimics real browser behavior
- Bypasses some anti-bot measures
- Slower but more reliable

### 2. LinkedIn Sales Navigator ($99/month)
- Official LinkedIn API access
- Higher rate limits
- Best for high-volume

### 3. Apollo.io (Freemium)
- 50 free credits/month
- Contact enrichment
- Good for small batches

## Cost

**$0** - Uses only:
- Python requests library
- BeautifulSoup for parsing
- Public websites and search engines

## Dependencies

```bash
pip install beautifulsoup4 requests
```

## Files Created
- `execution/find_owner_linkedin.py` - Main script
- `directives/find_owner_linkedin.md` - This documentation
