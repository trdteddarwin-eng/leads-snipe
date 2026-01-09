#!/usr/bin/env python3
"""
N8N Google Maps AI-Powered Lead Scraper

🚀 KEY FEATURES:
- Uses FREE LLM (Llama 3.3 70B) to generate nearby cities dynamically
- No city database needed - works for ANY location worldwide
- Adaptive batch system - sends batches until target met
- Sends ONE batch request (JSON array) to N8N per round
- Never repeats cities across rounds
- 100% FREE (no API costs)

Usage:
    python3 execution/n8n_gmaps_scraper_ai.py --industry "Dentist" --location "New Jersey" --target-leads 100
    python3 execution/n8n_gmaps_scraper_ai.py --industry "Plumber" --location "Phoenix area" --target-leads 50
"""

import os
import sys
import json
import hashlib
import argparse
import re
from datetime import datetime
from typing import Optional, List
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
WEBHOOK_URL = "https://n8n.srv1080136.hstgr.cloud/webhook/c66d6d2a-f22d-4fb6-b874-18ae5915347b"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not found in .env")
    sys.exit(1)


# ============================================================================
# FREE LLM FUNCTIONS (OpenRouter)
# ============================================================================

def call_free_llm(prompt: str, model: str = "meta-llama/llama-3.3-70b-instruct:free") -> Optional[str]:
    """
    Call FREE LLM via OpenRouter.
    
    Args:
        prompt: The prompt to send
        model: FREE model to use (default: Llama 3.3 70B)
    
    Returns:
        LLM response text or None if failed
    """
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"   ❌ LLM API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ LLM request failed: {e}")
        return None


def get_hardcoded_cities(location_query: str, num_cities: int = 5) -> List[str]:
    """
    Get hardcoded cities for common locations (faster for small hunts).

    Args:
        location_query: User's location
        num_cities: How many cities to return

    Returns:
        List of city names or empty list if not found
    """
    # Common location mappings
    hardcoded = {
        "new jersey": ["Newark, NJ", "Jersey City, NJ", "Paterson, NJ", "Elizabeth, NJ", "Edison, NJ", "Trenton, NJ", "Clifton, NJ"],
        "phoenix area": ["Phoenix, AZ", "Scottsdale, AZ", "Tempe, AZ", "Mesa, AZ", "Chandler, AZ", "Glendale, AZ"],
        "los angeles": ["Los Angeles, CA", "Long Beach, CA", "Glendale, CA", "Pasadena, CA", "Burbank, CA", "Santa Monica, CA"],
        "new york": ["New York, NY", "Brooklyn, NY", "Queens, NY", "Bronx, NY", "Staten Island, NY", "Yonkers, NY"],
        "chicago": ["Chicago, IL", "Naperville, IL", "Aurora, IL", "Joliet, IL", "Evanston, IL", "Cicero, IL"],
    }

    # Normalize query
    query_lower = location_query.lower().strip()

    # Check for matches
    for key, cities in hardcoded.items():
        if key in query_lower:
            return cities[:num_cities]

    return []


def get_cities_from_ai(
    location_query: str,
    exclude_cities: List[str] = None,
    num_cities: int = 5
) -> List[str]:
    """
    Ask FREE LLM to generate nearby cities for a location.

    Args:
        location_query: User's location (e.g., "New Jersey", "Phoenix area")
        exclude_cities: Cities already used (to avoid duplicates)
        num_cities: How many cities to generate

    Returns:
        List of city names with state codes ["City, ST", ...]
    """
    exclude_cities = exclude_cities or []

    # Quick optimization: For small hunts, try hardcoded cities first
    if not exclude_cities:  # First round
        hardcoded = get_hardcoded_cities(location_query, num_cities)
        if hardcoded:
            print(f"   ⚡ Using hardcoded cities (faster): {hardcoded}")
            return hardcoded
    
    prompt = f"""Generate {num_cities} major cities for local business search in: "{location_query}"

EXCLUDE these cities (already used): {exclude_cities}

Return ONLY a valid JSON array of city names with state codes.
Format: ["City, STATE", "City, STATE", ...]

Example for "New Jersey":
["Newark, NJ", "Jersey City, NJ", "Paterson, NJ", "Elizabeth, NJ", "Edison, NJ"]

Example for "Phoenix area":
["Phoenix, AZ", "Scottsdale, AZ", "Tempe, AZ", "Mesa, AZ", "Chandler, AZ"]

Location: "{location_query}"
JSON array:"""

    print(f"   🤖 Asking AI for {num_cities} cities in '{location_query}'...")
    
    llm_response = call_free_llm(prompt)
    
    if not llm_response:
        return []
    
    # Try to parse JSON from response
    try:
        # Clean response (remove markdown code blocks if present)
        cleaned = llm_response.strip()
        if cleaned.startswith("```"):
            # Extract JSON from code block
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        
        cities = json.loads(cleaned)
        
        if isinstance(cities, list):
            print(f"   ✅ AI generated: {cities}")
            return cities
        else:
            print(f"   ⚠️  Unexpected format: {cities}")
            return []
            
    except json.JSONDecodeError as e:
        print(f"   ❌ Failed to parse LLM response: {e}")
        print(f"   Raw response: {llm_response}")
        return []


# ============================================================================
# N8N WEBHOOK FUNCTIONS
# ============================================================================

def call_n8n_single(query: str, timeout: int = 60) -> List[dict]:
    """
    Send a SINGLE query to N8N webhook.

    Args:
        query: Search query (e.g., "Dentist in Newark, NJ")

    Returns:
        List of leads from this query
    """
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=[query],  # JSON array with single query
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
                return []
        else:
            return []

    except Exception as e:
        return []


def call_n8n_sequential(queries: List[str]) -> List[dict]:
    """
    Send multiple queries to N8N sequentially (one at a time).

    N8N times out on batch arrays, so we send one query at a time.

    Args:
        queries: Array of search queries

    Returns:
        Combined list of all leads from all cities
    """
    all_results = []

    print(f"   🚀 Sending {len(queries)} queries to N8N sequentially...")

    for i, query in enumerate(queries, 1):
        print(f"      [{i}/{len(queries)}] {query}... ", end="", flush=True)

        results = call_n8n_single(query)

        if results:
            all_results.extend(results)
            print(f"✅ {len(results)} leads")
        else:
            print("❌ No results")

    return all_results


# ============================================================================
# LEAD PROCESSING FUNCTIONS
# ============================================================================

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


# ============================================================================
# AI-POWERED ADAPTIVE SCRAPER (MAIN LOGIC)
# ============================================================================

def scrape_with_ai(
    industry: str,
    location: str,
    target_leads: int = 100,
    max_rounds: int = 5
) -> list:
    """
    AI-powered lead scraper with adaptive batching.
    Uses FREE LLM to generate cities dynamically - no database needed!
    
    Args:
        industry: Business type (e.g., "Dentist", "Plumber")
        location: Location query (e.g., "New Jersey", "Phoenix area", "North NJ")
        target_leads: Target number of leads (default: 100)
        max_rounds: Maximum rounds to prevent infinite loops (default: 5)
    
    Returns:
        List of leads (deduplicated and trimmed to target)
    """
    print(f"\n{'='*70}")
    print(f"🤖 AI-POWERED LEAD SCRAPER")
    print(f"{'='*70}")
    print(f"Industry: {industry}")
    print(f"Location: {location}")
    print(f"Target: {target_leads} leads")
    print(f"Max rounds: {max_rounds}")
    print()
    
    # Track state
    collected_leads = []
    seen_ids = set()
    used_cities = []
    
    # Main adaptive loop
    for round_num in range(1, max_rounds + 1):
        # How many more leads do we need?
        remaining = target_leads - len(collected_leads)
        
        if remaining <= 0:
            print(f"\n✅ Target reached! ({len(collected_leads)} leads)")
            break
        
        # Calculate how many cities to ask for
        if round_num == 1:
            # First round: over-provision by 30%
            avg_per_city = 20
            cities_needed = max(3, int((remaining / avg_per_city) * 1.3))
        else:
            # Subsequent rounds: conservative estimate
            avg_per_city = 15
            cities_needed = max(1, remaining // avg_per_city + 1)
        
        # Cap at 15 cities to avoid N8N timeout
        cities_needed = min(cities_needed, 15)
        
        print(f"\n{'─'*70}")
        print(f"📦 ROUND {round_num}")
        print(f"{'─'*70}")
        print(f"Need: {remaining} more leads")
        print(f"Requesting: {cities_needed} cities")
        
        # Ask AI for cities (excluding already-used ones)
        new_cities = get_cities_from_ai(
            location_query=location,
            exclude_cities=used_cities,
            num_cities=cities_needed
        )
        
        if not new_cities:
            print(f"\n⚠️  AI failed to generate cities. Stopping.")
            break
        
        # Build query array for N8N
        queries = [f"{industry} in {city}" for city in new_cities]

        # Send queries sequentially to N8N (one at a time)
        batch_results = call_n8n_sequential(queries)
        
        # Deduplicate and add to collection
        new_leads = 0
        for lead in batch_results:
            lead_id = generate_lead_id(lead)
            if lead_id not in seen_ids:
                seen_ids.add(lead_id)
                cleaned = clean_lead(lead)
                cleaned['scraped_at'] = datetime.now().isoformat()
                collected_leads.append(cleaned)
                new_leads += 1
        
        print(f"\n   ✅ Got {len(batch_results)} results, {new_leads} new leads")
        print(f"   📊 Total: {len(collected_leads)}/{target_leads} leads")
        
        # Track used cities
        used_cities.extend(new_cities)
    
    # Trim to exact target
    if len(collected_leads) > target_leads:
        print(f"\n✂️  Trimming from {len(collected_leads)} to {target_leads} leads")
        collected_leads = collected_leads[:target_leads]
    
    # Final stats
    print(f"\n{'='*70}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Rounds: {round_num}")
    print(f"Cities queried: {len(used_cities)}")
    print(f"Total leads: {len(collected_leads)}")
    
    valid_emails = sum(1 for l in collected_leads if l.get('email'))
    print(f"Leads with email: {valid_emails} ({100*valid_emails//max(len(collected_leads),1)}%)")
    print()
    
    return collected_leads


# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_results(leads: list, output_path: Optional[str] = None) -> str:
    """Save leads to JSON file."""
    if not leads:
        print("❌ No leads to save.")
        return None
    
    # Generate default path if not provided
    if not output_path:
        os.makedirs(".tmp", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f".tmp/leads_{timestamp}.json"
    
    with open(output_path, 'w') as f:
        json.dump(leads, f, indent=2)
    
    print(f"💾 Saved {len(leads)} leads to: {output_path}")
    return output_path


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered Lead Scraper - Uses FREE LLM to generate cities dynamically"
    )
    parser.add_argument(
        "--industry", "-i",
        required=True,
        help="Business type (e.g., 'Dentist', 'Plumber', 'HVAC contractor')"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="Location query (e.g., 'New Jersey', 'Phoenix area', 'North NJ')"
    )
    parser.add_argument(
        "--target-leads", "-t",
        type=int,
        default=100,
        help="Target number of leads (default: 100)"
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=5,
        help="Maximum batch rounds (default: 5)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (default: .tmp/leads_[timestamp].json)"
    )
    
    args = parser.parse_args()
    
    # Run the scraper
    leads = scrape_with_ai(
        industry=args.industry,
        location=args.location,
        target_leads=args.target_leads,
        max_rounds=args.max_rounds
    )
    
    if not leads:
        print("❌ No leads found.")
        sys.exit(1)
    
    # Save to JSON
    save_results(leads, args.output)
    
    print(f"\n🎉 Done! {len(leads)} leads from {args.location}")


if __name__ == "__main__":
    main()
