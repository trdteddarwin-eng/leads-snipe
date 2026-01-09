#!/usr/bin/env python3
"""
N8N Google Maps Parallel Scraper (Improved)

KEY IMPROVEMENTS:
1. Sends multiple parallel queries to N8N at once (faster!)
2. Smart location expansion: "North NJ" → multiple nearby cities
3. Calculates optimal number of cities based on target leads

Usage:
    python3 execution/n8n_gmaps_scraper_parallel.py --industry "Dentist" --location "North New Jersey" --target-leads 100
    python3 execution/n8n_gmaps_scraper_parallel.py --industry "Plumber" --location "Newark, NJ" --target-leads 50
"""

import os
import sys
import json
import time
import argparse
import hashlib
import re
from datetime import datetime
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# N8N Webhook URL
WEBHOOK_URL = "https://n8n.srv1080136.hstgr.cloud/webhook/c66d6d2a-f22d-4fb6-b874-18ae5915347b"

# Regional city mappings
REGION_CITIES = {
    # New Jersey regions
    "north new jersey": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack"],
    "north nj": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack"],
    "northern nj": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack"],

    "central new jersey": ["Edison", "Woodbridge", "New Brunswick", "Perth Amboy", "Sayreville", "East Brunswick", "Old Bridge", "Piscataway"],
    "central nj": ["Edison", "Woodbridge", "New Brunswick", "Perth Amboy", "Sayreville", "East Brunswick", "Old Bridge", "Piscataway"],

    "south new jersey": ["Camden", "Cherry Hill", "Trenton", "Atlantic City", "Vineland", "Gloucester", "Pennsauken"],
    "south nj": ["Camden", "Cherry Hill", "Trenton", "Atlantic City", "Vineland", "Gloucester", "Pennsauken"],
    "southern nj": ["Camden", "Cherry Hill", "Trenton", "Atlantic City", "Vineland", "Gloucester", "Pennsauken"],

    "essex county nj": ["Newark", "East Orange", "Irvington", "Orange", "Bloomfield", "Montclair", "Belleville", "Nutley", "Livingston"],
    "union county nj": ["Elizabeth", "Union", "Plainfield", "Linden", "Rahway", "Westfield", "Summit", "Cranford", "Roselle"],
    "hudson county nj": ["Jersey City", "Hoboken", "Union City", "West New York", "Bayonne", "North Bergen", "Secaucus"],
    "bergen county nj": ["Hackensack", "Paramus", "Fort Lee", "Fair Lawn", "Garfield", "Lodi", "Englewood", "Teaneck"],

    # New York regions
    "new york city": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"],
    "nyc": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"],
    "manhattan": ["Manhattan"],
    "brooklyn": ["Brooklyn"],

    # Default fallback for state-wide
    "new jersey": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Edison", "Woodbridge", "Lakewood", "Trenton", "Camden", "Clifton"],
    "nj": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Edison", "Woodbridge", "Lakewood", "Trenton", "Camden", "Clifton"],
}


def expand_location(location: str) -> tuple[List[str], str]:
    """
    Expand a location string into a list of cities.

    Examples:
        "North New Jersey" → (["Newark", "Elizabeth", ...], "NJ")
        "Newark, NJ" → (["Newark"], "NJ")
        "Essex County NJ" → (["Newark", "East Orange", ...], "NJ")

    Returns:
        (cities_list, state_code)
    """
    location_lower = location.lower().strip()

    # Check if it's a regional query
    if location_lower in REGION_CITIES:
        cities = REGION_CITIES[location_lower]
        # Extract state from first match
        if "nj" in location_lower or "jersey" in location_lower:
            state = "NJ"
        elif "ny" in location_lower or "york" in location_lower:
            state = "NY"
        else:
            state = "NJ"  # Default
        return cities, state

    # Check if it's "City, State" format
    if "," in location:
        parts = location.split(",")
        city = parts[0].strip()
        state = parts[1].strip().upper()
        return [city], state

    # Fallback: treat as single city in NJ
    return [location], "NJ"


def calculate_cities_needed(target_leads: int, avg_leads_per_city: int = 15) -> int:
    """
    Calculate how many cities to query based on target leads.

    N8N typically returns 10-25 leads per city.
    We'll be conservative and assume 15 per city.
    """
    cities_needed = (target_leads // avg_leads_per_city) + 1
    return min(cities_needed, 20)  # Cap at 20 cities max


def call_webhook_single(query: str, timeout: int = 60) -> List[dict]:
    """Call N8N webhook for a single query."""
    try:
        response = requests.post(
            WEBHOOK_URL,
            data=query,
            headers={"Content-Type": "text/plain"},
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'results' in data:
                return data['results']
        return []
    except Exception as e:
        print(f"   ❌ Error querying '{query}': {e}")
        return []


def call_webhook_parallel(queries: List[str], max_workers: int = 3, batch_delay: float = 1.0) -> List[dict]:
    """
    Send multiple queries to N8N in parallel with batching to avoid overwhelming server.

    Args:
        queries: List of search queries
        max_workers: Number of parallel requests per batch (default 3)
        batch_delay: Delay between batches in seconds (default 1.0)

    Returns:
        Combined list of all leads from all queries
    """
    print(f"\n🚀 Sending {len(queries)} queries to N8N in batches...")
    print(f"   Batch size: {max_workers} workers")
    print(f"   Batch delay: {batch_delay}s")

    all_results = []
    seen_ids = set()

    # Process queries in batches to avoid overwhelming N8N
    batch_size = max_workers
    for batch_num, i in enumerate(range(0, len(queries), batch_size), 1):
        batch = queries[i:i+batch_size]

        print(f"\n📦 Batch {batch_num}/{(len(queries)-1)//batch_size + 1} ({len(batch)} queries)")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit batch
            future_to_query = {
                executor.submit(call_webhook_single, query): query
                for query in batch
            }

            # Process results as they complete
            for j, future in enumerate(as_completed(future_to_query), 1):
                query = future_to_query[future]
                try:
                    results = future.result()

                    # Deduplicate
                    new_leads = 0
                    for lead in results:
                        lead_id = generate_lead_id(lead)
                        if lead_id not in seen_ids:
                            seen_ids.add(lead_id)
                            lead['search_query'] = query
                            lead['scraped_at'] = datetime.now().isoformat()
                            all_results.append(lead)
                            new_leads += 1

                    print(f"   [{j}/{len(batch)}] {query}")
                    print(f"      → {len(results)} results, {new_leads} new (Total: {len(all_results)})")

                except Exception as e:
                    print(f"   ❌ Failed: {query} - {e}")

        # Delay between batches (except last batch)
        if i + batch_size < len(queries):
            time.sleep(batch_delay)

    return all_results


def generate_lead_id(lead: dict) -> str:
    """Generate unique ID for deduplication."""
    if lead.get('place_id'):
        return lead['place_id']
    unique_str = f"{lead.get('name', '')}|{lead.get('address', '')}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def is_valid_email(email: str) -> bool:
    """Check if email is valid (not an image or placeholder)."""
    if not email or not isinstance(email, str):
        return False

    email = email.strip().lower()

    # Filter out image files
    if any(email.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
        return False

    # Basic email format check
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False

    return True


def clean_lead(lead: dict) -> dict:
    """Clean and normalize a lead."""
    cleaned = lead.copy()

    # Clean email
    if 'email' in cleaned:
        if not is_valid_email(cleaned['email']):
            cleaned['email'] = None

    return cleaned


def scrape_leads_parallel(
    industry: str,
    location: str,
    target_leads: int = 100,
    max_workers: int = 3
) -> list:
    """
    Scrape leads using parallel N8N queries.

    Args:
        industry: Business type (e.g., "Dentist", "Plumber")
        location: Location string (e.g., "North New Jersey", "Newark, NJ")
        target_leads: Target number of leads
        max_workers: Number of parallel N8N requests

    Returns:
        List of deduplicated leads
    """
    print(f"\n{'='*70}")
    print(f"🎯 N8N PARALLEL SCRAPER")
    print(f"{'='*70}")
    print(f"Industry: {industry}")
    print(f"Location: {location}")
    print(f"Target: {target_leads} leads")
    print()

    # Step 1: Expand location into cities
    cities, state = expand_location(location)
    print(f"📍 Location expanded to {len(cities)} cities in {state}:")
    print(f"   {', '.join(cities[:10])}" + (f" (+{len(cities)-10} more)" if len(cities) > 10 else ""))
    print()

    # Step 2: Calculate how many cities we actually need
    cities_needed = calculate_cities_needed(target_leads)
    cities_to_query = cities[:cities_needed]

    print(f"📊 Query strategy:")
    print(f"   Estimated leads per city: ~15")
    print(f"   Cities needed for {target_leads} leads: {cities_needed}")
    print(f"   Cities selected: {len(cities_to_query)}")
    print()

    # Step 3: Build query list
    queries = [f"{industry} in {city}, {state}" for city in cities_to_query]

    # Step 4: Send parallel queries
    all_leads = call_webhook_parallel(queries, max_workers=max_workers)

    # Step 5: Clean leads
    cleaned_leads = [clean_lead(lead) for lead in all_leads]

    # Step 6: Trim to target if we got too many
    if len(cleaned_leads) > target_leads:
        print(f"\n✂️  Trimming from {len(cleaned_leads)} to {target_leads} leads")
        cleaned_leads = cleaned_leads[:target_leads]

    print(f"\n{'='*70}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Queries sent: {len(queries)}")
    print(f"Total unique leads: {len(cleaned_leads)}")

    valid_emails = sum(1 for l in cleaned_leads if l.get('email'))
    print(f"Leads with email: {valid_emails} ({100*valid_emails//max(len(cleaned_leads),1)}%)")
    print()

    return cleaned_leads


def save_results(leads: list, output_path: Optional[str] = None) -> str:
    """Save leads to JSON file."""
    if not leads:
        print("❌ No leads to save.")
        return None

    # Generate default path if not provided
    if not output_path:
        os.makedirs(".tmp", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f".tmp/n8n_leads_{timestamp}.json"

    with open(output_path, 'w') as f:
        json.dump(leads, f, indent=2)

    print(f"💾 Saved {len(leads)} leads to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Parallel N8N Google Maps Lead Scraper"
    )
    parser.add_argument(
        "--industry", "-i",
        required=True,
        help="Business type (e.g., 'Dentist', 'Plumber')"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="Location (e.g., 'North New Jersey', 'Newark, NJ', 'Essex County NJ')"
    )
    parser.add_argument(
        "--target-leads", "-t",
        type=int,
        default=100,
        help="Target number of leads (default: 100)"
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=3,
        help="Number of parallel requests per batch (default: 3)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: .tmp/n8n_leads_[timestamp].json)"
    )

    args = parser.parse_args()

    # Run the scraper
    leads = scrape_leads_parallel(
        industry=args.industry,
        location=args.location,
        target_leads=args.target_leads,
        max_workers=args.workers
    )

    if not leads:
        print("❌ No leads found.")
        sys.exit(1)

    # Save to JSON
    save_results(leads, args.output)

    print(f"\n🎉 Done! {len(leads)} leads ready for enrichment.")


if __name__ == "__main__":
    main()
