#!/usr/bin/env python3
"""
Direct Lead Generation Engine (Hard-coded alternative to N8N)

Features:
1. Parallel Google Maps Scraping (via Apify)
2. Parallel Website HTML Fetching
3. Advanced Email Extraction (Regex + Meta Tag Scanning)
4. Automatic De-duplication
5. Real-time logging for LeadSnipe UI

Usage:
    python3 execution/direct_lead_gen.py --industry "Dentist" --location "Union, NJ" --limit 50
"""

import os
import sys
import json
import time
import re
import math
import hashlib
import argparse
import requests
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse
from apify_client import ApifyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Email Regex
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@(?![a-zA-Z0-9.-]*\.(?:png|jpg|jpeg|gif|svg|webp|js|css|pdf))\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', re.IGNORECASE)

# ============================================================================
# Helpers
# ============================================================================

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)

def generate_id(item):
    """Generate unique ID based on name and address."""
    unique_str = f"{item.get('title', item.get('name', ''))}|{item.get('address', '')}"
    return hashlib.md5(unique_str.encode()).hexdigest()

def clean_url(url):
    if not url: return None
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')

# Regional expansions for common search terms
REGION_EXPANSION = {
    "north new jersey": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack"],
    "northern nj": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack"],
    "north nj": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack"],
    "central new jersey": ["Edison", "Woodbridge", "New Brunswick", "Perth Amboy", "Sayreville", "East Brunswick", "Old Bridge", "Piscataway"],
    "central nj": ["Edison", "Woodbridge", "New Brunswick", "Perth Amboy", "Sayreville", "East Brunswick", "Old Bridge", "Piscataway"],
    "south new jersey": ["Camden", "Cherry Hill", "Trenton", "Atlantic City", "Vineland", "Gloucester", "Pennsauken"],
    "southern nj": ["Camden", "Cherry Hill", "Trenton", "Atlantic City", "Vineland", "Gloucester", "Pennsauken"],
}

def load_city_database():
    """Load US cities database from JSON file."""
    db_path = 'execution/us_cities.json'
    if not os.path.exists(db_path):
        return {}
    with open(db_path, 'r') as f:
        return json.load(f)

def calculate_distance_miles(lat1, lon1, lat2, lon2):
    R = 3959
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat, delta_lon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def expand_location(location, city_db, radius_miles=15):
    """Expand location string into a list of nearby cities."""
    location_lower = location.lower().strip()
    if location_lower in REGION_EXPANSION:
        return [f"{c}, NJ" for c in REGION_EXPANSION[location_lower]]

    # City, State format
    if "," in location:
        parts = location.split(",")
        city = parts[0].strip()
        state = parts[1].strip()
        
        # If no city provided, search for major cities in that state
        if not city:
            major_cities = []
            for c_name, coords in city_db.items():
                if coords['state'] == state:
                    major_cities.append(c_name)
            return major_cities[:15] if major_cities else [location]

        if location in city_db:
            target = city_db[location]
            nearby = [location]
            for c_name, coords in city_db.items():
                if coords['state'] == state and c_name != location:
                    if calculate_distance_miles(target['lat'], target['lon'], coords['lat'], coords['lon']) <= radius_miles:
                        nearby.append(c_name)
            return nearby
    
    return [location]

# ============================================================================
# Stage 1: Search (via Apify)
# ============================================================================

def search_google_maps_batch(industry, location_list, target_count=50):
    """Run Apify searches for multiple cities until target count met."""
    if not APIFY_TOKEN:
        log("APIFY_API_TOKEN missing", "ERROR")
        return []

    client = ApifyClient(APIFY_TOKEN)
    all_results = []
    seen_ids = set()

    # Calculate limit per city - be aggressive to hit 200+
    # Google Maps usually gives max 60-120 per search even with pagination
    limit_per_city = 120 
    
    # Randomize location list to get better geographical variety
    random.shuffle(location_list)
    
    for loc in location_list:
        if len(all_results) >= target_count:
            log(f"✅ Target of {target_count} reached.")
            break
            
        query = f"{industry} in {loc}"
        log(f"🔍 Swarming: '{query}'...")
        
        try:
            # Note: compass/crawler-google-places is high-performance
            run_input = {
                "searchStringsArray": [query],
                "maxCrawledPlacesPerSearch": limit_per_city,
                "language": "en",
                "maxImages": 0, # Faster
                "maxReviews": 0, # Faster
                "deeperCityScrape": True if len(location_list) < 3 else False,
            }
            # Start the actor
            run = client.actor("compass/crawler-google-places").call(run_input=run_input)
            
            new_count = 0
            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                place_id = item.get("placeId") or generate_id(item)
                if place_id not in seen_ids:
                    seen_ids.add(place_id)
                    all_results.append(item)
                    new_count += 1
            
            log(f"   ✨ Harvested {new_count} new leads from {loc} (Running Total: {len(all_results)})")
            
        except Exception as e:
            log(f"   ❌ Swarm failed for {loc}: {e}", "WARN")

    return all_results[:target_count]

# ============================================================================
# Stage 2: Scrape & Extract (Parallel)
# ============================================================================

def scrape_emails_direct(url):
    """Fetch website HTML and extract meta info + emails."""
    if not url: return {"email": None, "scraped_text": "", "scraped_meta": ""}
    
    url = clean_url(url)
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if resp.status_code != 200:
            return {"email": None, "scraped_text": "", "scraped_meta": ""}
        
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Extract Meta Description
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')

        # 2. Extract Text
        for script in soup(["script", "style"]):
            script.decompose()
        scraped_text = soup.get_text(separator=' ', strip=True)
        
        # 3. Extract Emails - EXTENDED REGEX Match (N8N Blueprint)
        # Match standard emails and obfuscated ones
        emails = EMAIL_REGEX.findall(html)
        
        # Additional deep-scan for cases where regex might miss due to spacing/obfuscation
        if not emails:
            # Look for "mailto:" links specifically
            mailto_matches = re.findall(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', html, re.I)
            emails.extend(mailto_matches)
        
        # Filter common junk emails and duplicates
        seen_emails = set()
        valid_emails = []
        junk = {'example@email.com', 'info@example.com', 'contact@example.com', 'support@example.com', 'admin@example.com'}
        
        for e in emails:
            e_low = e.lower()
            if e_low not in junk and e_low not in seen_emails:
                valid_emails.append(e)
                seen_emails.add(e_low)
        
        email = valid_emails[0] if valid_emails else None
        
        return {
            "email": email,
            "scraped_text": scraped_text[:2000],  # Limit text
            "scraped_meta": meta_desc
        }
        
    except Exception:
        return {"email": None, "scraped_text": "", "scraped_meta": ""}

def process_leads_parallel(raw_leads, max_workers=25):
    """Scrape websites for all leads in parallel (High-Speed Swarm)."""
    log(f"🚀 Swarming {len(raw_leads)} websites (Parallel Workers: {max_workers})...")
    
    processed = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create mapping of future to lead
        future_to_lead = {executor.submit(scrape_emails_direct, lead.get('website')): lead for lead in raw_leads}
        
        for i, future in enumerate(as_completed(future_to_lead), 1):
            lead = future_to_lead[future]
            try:
                enrichment = future.result()
                
                # Merge data
                final_lead = {
                    "id": generate_id(lead),
                    "name": lead.get("title", lead.get("name")),
                    "address": lead.get("address"),
                    "phone": lead.get("phone") or lead.get("formattedPhoneNumber"),
                    "website": lead.get("website"),
                    "category": lead.get("categoryName") or lead.get("type"),
                    "rating": lead.get("totalScore"),
                    "reviews": lead.get("reviewsCount"),
                    "email": enrichment.get("email"),
                    "meta_description": enrichment.get("scraped_meta"),
                    "scraped_at": datetime.now().isoformat()
                }
                processed.append(final_lead)
                
                if i % 5 == 0:
                    log(f"   → Processed {i}/{len(raw_leads)}...")
            except Exception as e:
                log(f"   ❌ Error processing lead: {e}", "WARN")
                
    return processed

# ============================================================================
# Main Logic
# ============================================================================

def run_lead_gen(industry, location, target_count=50):
    """Full pipeline: Search -> Scrape -> Enrich."""
    log("="*60)
    log("  Direct Lead Generation Engine Starting")
    log("="*60)
    log(f"Industry: {industry}")
    log(f"Location: {location}")
    log(f"Target: {target_count}")
    print()

    # Step 0: Expand Cities
    city_db = load_city_database()
    cities = expand_location(location, city_db)
    log(f"📍 Expanded to {len(cities)} cities for deeper coverage")

    # Step 1: Search
    raw_leads = search_google_maps_batch(industry, cities, target_count=target_count)
    
    if not raw_leads:
        log("No leads found in initial search.", "ERROR")
        return []

    # Step 2: Enrich (Direct Scraping)
    enriched_leads = process_leads_parallel(raw_leads)
    
    # Step 3: De-duplication
    seen_ids = set()
    final_leads = []
    for l in enriched_leads:
        if l['id'] not in seen_ids:
            seen_ids.add(l['id'])
            final_leads.append(l)

    log(f"✅ Completed! Found {len(final_leads)} unique leads.")
    log(f"📊 Email coverage: {sum(1 for l in final_leads if l.get('email'))}/{len(final_leads)}")
    
    return final_leads

def main():
    parser = argparse.ArgumentParser(description="Direct Lead Generation Engine")
    parser.add_argument("--industry", "-i", required=True, help="Business type")
    parser.add_argument("--location", "-l", required=True, help="Location")
    parser.add_argument("--limit", "-t", type=int, default=50, help="Target leads")
    parser.add_argument("--output", "-o", help="Output JSON path")
    
    args = parser.parse_args()
    
    leads = run_lead_gen(args.industry, args.location, args.limit)
    
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".tmp", exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(leads, f, indent=2)
        log(f"💾 Results saved to: {args.output}")
    else:
        # Default output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f".tmp/direct_leads_{timestamp}.json"
        with open(output_path, 'w') as f:
            json.dump(leads, f, indent=2)
        log(f"💾 Results saved to: {output_path}")

if __name__ == "__main__":
    main()
