#!/usr/bin/env python3
"""
N8N Google Maps Free Lead Scraper

Scrapes local businesses from Google Maps using a free N8N webhook.
Loops through city variations to maximize lead volume since each call returns 10-25 leads.

Usage:
    python3 execution/n8n_gmaps_scraper.py --industry "Dentist" --state "NJ" --target-leads 100
"""

import os
import sys
import json
import time
import argparse
import hashlib
import re
from datetime import datetime
from typing import Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# N8N Webhook URL
WEBHOOK_URL = "https://n8n.srv1080136.hstgr.cloud/webhook/c66d6d2a-f22d-4fb6-b874-18ae5915347b"

# Pre-configured city lists by state
STATE_CITIES = {
    "NJ": [
        "Newark", "Jersey City", "Paterson", "Elizabeth", "Trenton",
        "Edison", "Woodbridge", "Lakewood", "Toms River", "Hamilton",
        "Clifton", "Camden", "Brick", "Cherry Hill", "Passaic",
        "Union City", "Bayonne", "East Orange", "Vineland", "New Brunswick",
        "Hoboken", "Perth Amboy", "West New York", "Plainfield", "Hackensack",
        "Sayreville", "Kearny", "Linden", "Atlantic City", "Morristown",
        "Livingston", "Watchung", "Summit", "Westfield", "Scotch Plains",
        "Millburn", "Maplewood", "South Orange", "Montclair", "Glen Ridge",
        "Bloomfield", "Nutley", "Belleville", "Irvington", "Orange",
        "West Orange", "Caldwell", "Verona", "Cedar Grove", "Fairfield"
    ],
    "NY": [
        "New York City", "Buffalo", "Rochester", "Yonkers", "Syracuse",
        "Albany", "New Rochelle", "Mount Vernon", "Schenectady", "Utica",
        "White Plains", "Troy", "Niagara Falls", "Binghamton", "Freeport",
        "Long Beach", "Ithaca", "Poughkeepsie", "North Tonawanda", "Jamestown",
        "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"
    ],
    "TX": [
        "Houston", "San Antonio", "Dallas", "Austin", "Fort Worth",
        "El Paso", "Arlington", "Corpus Christi", "Plano", "Laredo",
        "Lubbock", "Garland", "Irving", "Amarillo", "Grand Prairie",
        "Brownsville", "McKinney", "Frisco", "Pasadena", "Mesquite",
        "Killeen", "McAllen", "Waco", "Denton", "Carrollton"
    ],
    "CA": [
        "Los Angeles", "San Diego", "San Jose", "San Francisco", "Fresno",
        "Sacramento", "Long Beach", "Oakland", "Bakersfield", "Anaheim",
        "Santa Ana", "Riverside", "Stockton", "Irvine", "Chula Vista",
        "Fremont", "San Bernardino", "Modesto", "Fontana", "Moreno Valley",
        "Santa Clarita", "Glendale", "Huntington Beach", "Garden Grove", "Oceanside"
    ],
    "FL": [
        "Miami", "Orlando", "Tampa", "Jacksonville", "St. Petersburg",
        "Hialeah", "Tallahassee", "Fort Lauderdale", "Port St. Lucie", "Cape Coral",
        "Pembroke Pines", "Hollywood", "Miramar", "Gainesville", "Coral Springs",
        "Miami Gardens", "Clearwater", "Palm Bay", "Pompano Beach", "West Palm Beach",
        "Lakeland", "Davie", "Boca Raton", "Sunrise", "Deltona"
    ],
    "PA": [
        "Philadelphia", "Pittsburgh", "Allentown", "Reading", "Scranton",
        "Bethlehem", "Lancaster", "Harrisburg", "Altoona", "Erie",
        "York", "Wilkes-Barre", "Chester", "Easton", "Lebanon",
        "Hazleton", "New Castle", "Johnstown", "McKeesport", "Williamsport"
    ],
    "OH": [
        "Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron",
        "Dayton", "Parma", "Canton", "Youngstown", "Lorain",
        "Hamilton", "Springfield", "Kettering", "Elyria", "Lakewood"
    ],
    "IL": [
        "Chicago", "Aurora", "Naperville", "Joliet", "Rockford",
        "Springfield", "Elgin", "Peoria", "Champaign", "Waukegan",
        "Cicero", "Bloomington", "Arlington Heights", "Evanston", "Schaumburg"
    ],
    "GA": [
        "Atlanta", "Augusta", "Columbus", "Macon", "Savannah",
        "Athens", "Sandy Springs", "Roswell", "Johns Creek", "Albany",
        "Warner Robins", "Alpharetta", "Marietta", "Valdosta", "Smyrna"
    ],
    "NC": [
        "Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem",
        "Fayetteville", "Cary", "Wilmington", "High Point", "Concord",
        "Greenville", "Asheville", "Gastonia", "Jacksonville", "Chapel Hill"
    ]
}

# State name to abbreviation mapping
STATE_ABBREV = {
    "new jersey": "NJ", "new york": "NY", "texas": "TX", "california": "CA",
    "florida": "FL", "pennsylvania": "PA", "ohio": "OH", "illinois": "IL",
    "georgia": "GA", "north carolina": "NC"
}


def normalize_state(state: str) -> str:
    """Convert state name to abbreviation."""
    state_lower = state.lower().strip()
    if state_lower in STATE_ABBREV:
        return STATE_ABBREV[state_lower]
    return state.upper().strip()


def get_cities_for_state(state: str) -> list:
    """Get list of cities for a state."""
    state_code = normalize_state(state)
    if state_code in STATE_CITIES:
        return STATE_CITIES[state_code]
    else:
        print(f"⚠️  No pre-configured cities for '{state}'. Please provide --cities manually.")
        return []


def is_valid_email(email: str) -> bool:
    """Check if email is valid (not an image or placeholder)."""
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip().lower()
    
    # Filter out image files
    if any(email.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
        return False
    
    # Filter out placeholders
    if email in ['example@email.com', 'info@example.com', 'contact@example.com']:
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


def generate_lead_id(lead: dict) -> str:
    """Generate unique ID for deduplication."""
    # Use place_id if available (most reliable)
    if lead.get('place_id'):
        return lead['place_id']
    
    # Fallback to name + address hash
    unique_str = f"{lead.get('name', '')}|{lead.get('address', '')}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def call_webhook(query: str, timeout: int = 60) -> list:
    """
    Call the N8N webhook with a query.
    
    Args:
        query: Search query like "Dentist in Newark, NJ"
        timeout: Request timeout in seconds
        
    Returns:
        List of lead dictionaries
    """
    try:
        print(f"   🔍 Querying: {query}")
        
        # Send query as plain text in body
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
            else:
                print(f"   ⚠️  Unexpected response format")
                return []
        else:
            print(f"   ❌ Webhook error: {response.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Timeout after {timeout}s")
        return []
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
        return []
    except json.JSONDecodeError:
        print(f"   ❌ Invalid JSON response")
        return []


def scrape_leads(
    industry: str,
    state: str,
    cities: Optional[list] = None,
    target_leads: int = 100,
    delay: float = 2.0,
    timeout: int = 60
) -> list:
    """
    Scrape leads by looping through city variations.
    
    Args:
        industry: Business type (e.g., "Dentist", "Plumber")
        state: State abbreviation or name
        cities: Optional list of cities (auto-generates if None)
        target_leads: Target number of leads to collect
        delay: Delay between webhook calls in seconds
        timeout: Webhook timeout in seconds
        
    Returns:
        List of deduplicated leads
    """
    state_code = normalize_state(state)
    
    # Get cities list
    if cities:
        city_list = cities
    else:
        city_list = get_cities_for_state(state)
        
    if not city_list:
        print("❌ No cities to search. Provide --cities or use a supported state.")
        return []
    
    print(f"\n🚀 Starting N8N Google Maps Scrape")
    print(f"   Industry: {industry}")
    print(f"   State: {state_code}")
    print(f"   Cities to search: {len(city_list)}")
    print(f"   Target leads: {target_leads}")
    print(f"   Delay between calls: {delay}s")
    print()
    
    all_leads = []
    seen_ids = set()
    queries_made = 0
    
    # Loop through cities until we hit target
    for city in city_list:
        if len(all_leads) >= target_leads:
            print(f"\n✅ Reached target of {target_leads} leads!")
            break
            
        query = f"{industry} in {city}, {state_code}"
        queries_made += 1
        
        results = call_webhook(query, timeout=timeout)
        
        new_leads = 0
        for lead in results:
            lead_id = generate_lead_id(lead)
            if lead_id not in seen_ids:
                seen_ids.add(lead_id)
                cleaned = clean_lead(lead)
                cleaned['search_query'] = query
                cleaned['scraped_at'] = datetime.now().isoformat()
                all_leads.append(cleaned)
                new_leads += 1
        
        print(f"      → Got {len(results)} results, {new_leads} new (Total: {len(all_leads)})")
        
        # Delay between calls to avoid overwhelming server
        if len(all_leads) < target_leads and city != city_list[-1]:
            time.sleep(delay)
    
    print(f"\n📊 Scraping Complete!")
    print(f"   Queries made: {queries_made}")
    print(f"   Total unique leads: {len(all_leads)}")
    
    # Stats on email quality
    valid_emails = sum(1 for l in all_leads if l.get('email'))
    print(f"   Leads with valid email: {valid_emails} ({100*valid_emails//max(len(all_leads),1)}%)")
    
    return all_leads


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
    
    print(f"\n💾 Saved {len(leads)} leads to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Maps leads using free N8N webhook"
    )
    parser.add_argument(
        "--industry", "-i",
        required=True,
        help="Business type (e.g., 'Dentist', 'Plumber', 'HVAC contractor')"
    )
    parser.add_argument(
        "--state", "-s",
        required=True,
        help="State abbreviation or name (e.g., 'NJ', 'New Jersey')"
    )
    parser.add_argument(
        "--cities", "-c",
        help="Comma-separated list of cities (auto-generates if omitted)"
    )
    parser.add_argument(
        "--target-leads", "-t",
        type=int,
        default=100,
        help="Target number of leads (default: 100)"
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=2.0,
        help="Delay between webhook calls in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Webhook timeout in seconds (default: 60)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: .tmp/n8n_leads_[timestamp].json)"
    )
    parser.add_argument(
        "--sheet-url",
        help="Google Sheet URL to append results (optional)"
    )
    
    args = parser.parse_args()
    
    # Parse cities if provided
    cities = None
    if args.cities:
        cities = [c.strip() for c in args.cities.split(",")]
    
    # Run the scraper
    leads = scrape_leads(
        industry=args.industry,
        state=args.state,
        cities=cities,
        target_leads=args.target_leads,
        delay=args.delay,
        timeout=args.timeout
    )
    
    if not leads:
        print("❌ No leads found.")
        sys.exit(1)
    
    # Save to JSON
    output_path = save_results(leads, args.output)
    
    # Optionally upload to Google Sheet
    if args.sheet_url and output_path:
        print(f"\n📤 Uploading to Google Sheet...")
        # Use existing update_sheet.py script
        import subprocess
        result = subprocess.run(
            ["python3", "execution/update_sheet.py", output_path, "--sheet-url", args.sheet_url],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Uploaded to Google Sheet!")
        else:
            print(f"❌ Sheet upload failed: {result.stderr}")
    
    print(f"\n🎉 Done! {len(leads)} leads ready for outreach.")


if __name__ == "__main__":
    main()
