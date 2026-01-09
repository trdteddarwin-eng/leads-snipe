#!/usr/bin/env python3
"""
N8N Google Maps Smart Local Scraper

FEATURES:
1. Proximity-based city selection (10-mile radius by default)
2. Adaptive batching (sends batches until target lead count met)
3. Works for ALL 50 US states (32,000+ cities)
4. Sends JSON array batches to N8N (not individual requests)

Usage:
    python3 execution/n8n_gmaps_scraper_smart.py --industry "Dentist" --location "Union, NJ" --target-leads 100
    python3 execution/n8n_gmaps_scraper_smart.py --industry "Plumber" --location "Austin, TX" --target-leads 50
    python3 execution/n8n_gmaps_scraper_smart.py --industry "HVAC" --location "North New Jersey" --target-leads 200
"""

import os
import sys
import json
import math
import argparse
import hashlib
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# N8N Webhook URL
WEBHOOK_URL = "https://n8n.srv1080136.hstgr.cloud/webhook/c66d6d2a-f22d-4fb6-b874-18ae5915347b"

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
        print(f"❌ City database not found at {db_path}")
        print(f"   Run: python3 execution/download_us_cities.py")
        sys.exit(1)

    with open(db_path, 'r') as f:
        return json.load(f)


def calculate_distance_miles(lat1, lon1, lat2, lon2):
    """
    Calculate distance in miles between two coordinates using Haversine formula.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in miles
    """
    # Earth radius in miles
    R = 3959

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_lat/2)**2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance = R * c
    return distance


def get_nearby_cities(target_city, city_db, radius_miles=10, max_cities=100):
    """
    Find cities within X miles of target city.

    Args:
        target_city: City name (e.g., "Union, NJ")
        city_db: City database dict
        radius_miles: Search radius in miles
        max_cities: Maximum cities to return

    Returns:
        List of city names sorted by distance (closest first)
    """
    if target_city not in city_db:
        print(f"⚠️  City not found: {target_city}")
        return []

    target_coords = city_db[target_city]
    target_lat = target_coords['lat']
    target_lon = target_coords['lon']

    # Calculate distances to all cities in same state
    target_state = target_coords['state']
    distances = []

    for city, coords in city_db.items():
        # Only consider cities in same state
        if coords['state'] != target_state:
            continue

        if city == target_city:
            continue  # Skip target city itself

        dist = calculate_distance_miles(
            target_lat, target_lon,
            coords['lat'], coords['lon']
        )

        if dist <= radius_miles:
            distances.append((city, dist))

    # Sort by distance (closest first)
    distances.sort(key=lambda x: x[1])

    # Return city names (always include target city first)
    nearby_cities = [target_city] + [city for city, dist in distances[:max_cities-1]]

    return nearby_cities


def expand_location_smart(location, city_db, radius_miles=10):
    """
    Expand location input to list of nearby cities.

    Handles:
        - Specific city: "Union, NJ" → nearby cities within radius
        - Region: "North New Jersey" → predefined list
        - State: "NJ" → major cities in state

    Args:
        location: User input location
        city_db: City database
        radius_miles: Search radius for specific cities

    Returns:
        List of city names with state (e.g., ["Union, NJ", "Elizabeth, NJ", ...])
    """
    location_lower = location.lower().strip()

    # Check if it's a known region
    if location_lower in REGION_EXPANSION:
        city_names = REGION_EXPANSION[location_lower]
        # Convert to "City, State" format
        state = "NJ"  # Default for NJ regions
        return [f"{city}, {state}" for city in city_names]

    # Check if it's "City, State" format
    if "," in location:
        # Exact city match
        if location in city_db:
            return get_nearby_cities(location, city_db, radius_miles)
        else:
            print(f"⚠️  City not found in database: {location}")
            return []

    # Fallback: return empty
    print(f"⚠️  Could not expand location: {location}")
    print(f"   Try format: 'City, STATE' (e.g., 'Union, NJ')")
    return []


def call_n8n_batch(queries: List[str], timeout=180):
    """
    Send multiple queries to N8N in ONE batch request.

    Args:
        queries: Array of search queries
                 ["Dentist in Union, NJ", "Dentist in Hillside, NJ", ...]
        timeout: Request timeout in seconds

    Returns:
        Combined list of all leads from all queries
    """
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=queries,  # Send as JSON array
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'results' in data:
                return data['results']
        else:
            print(f"   ❌ N8N error: HTTP {response.status_code}")

        return []

    except requests.exceptions.Timeout:
        print(f"   ⏱️  Timeout after {timeout}s")
        return []
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return []


def generate_lead_id(lead: dict) -> str:
    """Generate unique ID for deduplication."""
    if lead.get('place_id'):
        return lead['place_id']
    unique_str = f"{lead.get('name', '')}|{lead.get('address', '')}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def is_valid_email(email: str) -> bool:
    """Check if email is valid."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if any(email.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
        return False
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False
    return True


def clean_lead(lead: dict) -> dict:
    """Clean and normalize a lead."""
    cleaned = lead.copy()
    if 'email' in cleaned:
        if not is_valid_email(cleaned['email']):
            cleaned['email'] = None
    return cleaned


def scrape_leads_adaptive(
    industry: str,
    location: str,
    target_leads: int = 100,
    radius_miles: int = 10,
    max_rounds: int = 5
) -> list:
    """
    Scrape leads with adaptive batching strategy.
    Sends batches until target lead count is met.

    Args:
        industry: Business type (e.g., "Dentist")
        location: Target location (e.g., "Union, NJ", "North New Jersey")
        target_leads: Target number of leads
        radius_miles: Search radius for proximity
        max_rounds: Maximum number of batch rounds

    Returns:
        List of leads (up to target_leads)
    """
    print(f"\n{'='*70}")
    print(f"🎯 SMART LOCAL LEAD SCRAPER")
    print(f"{'='*70}")
    print(f"Industry: {industry}")
    print(f"Location: {location}")
    print(f"Target: {target_leads} leads")
    print(f"Radius: {radius_miles} miles")
    print()

    # Step 1: Load city database
    print("📍 Loading US city database...")
    city_db = load_city_database()
    print(f"   ✅ Loaded {len(city_db):,} cities")

    # Step 2: Expand location to nearby cities
    print(f"\n🔍 Expanding location: {location}")
    all_cities = expand_location_smart(location, city_db, radius_miles)

    if not all_cities:
        print("❌ No cities found. Exiting.")
        return []

    print(f"   ✅ Found {len(all_cities)} nearby cities")
    print(f"   📋 Top cities:")
    for i, city in enumerate(all_cities[:10], 1):
        print(f"      {i}. {city}")
    if len(all_cities) > 10:
        print(f"      ... and {len(all_cities) - 10} more")

    # Step 3: Adaptive batching loop
    collected_leads = []
    seen_ids = set()
    cities_used = 0

    print(f"\n🚀 Starting adaptive batch scraping...")

    for round_num in range(1, max_rounds + 1):
        # How many more leads do we need?
        remaining_needed = target_leads - len(collected_leads)

        if remaining_needed <= 0:
            print(f"\n✅ Target reached!")
            break

        # Calculate cities needed for this round
        if round_num == 1:
            # First round: over-provision by 30%
            cities_needed = int((remaining_needed / 20) * 1.3)
        else:
            # Later rounds: conservative estimate
            cities_needed = max(1, remaining_needed // 15 + 1)

        # Cap at 10 cities per batch (avoid overwhelming N8N)
        cities_needed = min(cities_needed, 10)

        # Get next batch of cities
        cities_batch = all_cities[cities_used:cities_used + cities_needed]

        if not cities_batch:
            print(f"\n⚠️  Ran out of cities to search!")
            break

        # Build query array
        queries = [f"{industry} in {city}" for city in cities_batch]

        print(f"\n📦 Round {round_num}/{max_rounds}:")
        print(f"   Need: {remaining_needed} more leads")
        print(f"   Sending batch with {len(queries)} cities...")

        # Send ONE batch to N8N
        batch_results = call_n8n_batch(queries)

        # Deduplicate and collect
        new_leads = 0
        for lead in batch_results:
            lead_id = generate_lead_id(lead)
            if lead_id not in seen_ids:
                seen_ids.add(lead_id)
                cleaned = clean_lead(lead)
                cleaned['search_query'] = f"{industry} in {location}"
                cleaned['scraped_at'] = datetime.now().isoformat()
                collected_leads.append(cleaned)
                new_leads += 1

        print(f"   → Got {len(batch_results)} results, {new_leads} new")
        print(f"   📊 Total: {len(collected_leads)}/{target_leads} leads")

        cities_used += len(cities_batch)

    # Step 4: Trim to exact target
    final_leads = collected_leads[:target_leads]

    print(f"\n{'='*70}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Cities queried: {cities_used}")
    print(f"Leads collected: {len(final_leads)}")
    print(f"Email coverage: {sum(1 for l in final_leads if l.get('email'))}/{len(final_leads)}")
    print()

    return final_leads


def save_results(leads: list, output_path: Optional[str] = None) -> str:
    """Save leads to JSON file."""
    if not leads:
        print("❌ No leads to save.")
        return None

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
        description="Smart Local Lead Scraper with Proximity Targeting"
    )
    parser.add_argument(
        "--industry", "-i",
        required=True,
        help="Business type (e.g., 'Dentist', 'Plumber', 'HVAC')"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="Target location (e.g., 'Union, NJ', 'Austin, TX', 'North New Jersey')"
    )
    parser.add_argument(
        "--target-leads", "-t",
        type=int,
        default=100,
        help="Target number of leads (default: 100)"
    )
    parser.add_argument(
        "--radius", "-r",
        type=int,
        default=10,
        help="Search radius in miles (default: 10)"
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=5,
        help="Maximum batch rounds (default: 5)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: .tmp/n8n_leads_[timestamp].json)"
    )

    args = parser.parse_args()

    # Run the scraper
    leads = scrape_leads_adaptive(
        industry=args.industry,
        location=args.location,
        target_leads=args.target_leads,
        radius_miles=args.radius,
        max_rounds=args.max_rounds
    )

    if not leads:
        print("❌ No leads found.")
        sys.exit(1)

    # Save results
    save_results(leads, args.output)

    print(f"\n🎉 Done! {len(leads)} local leads ready for outreach.")


if __name__ == "__main__":
    main()
