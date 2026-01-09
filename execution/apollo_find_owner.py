#!/usr/bin/env python3
"""
Apollo.io Integration for Finding Decision Makers

Uses Apollo.io's free tier to find business owners/CEOs/founders.
Free tier: 600 credits/month

Usage:
    python3 execution/apollo_find_owner.py --company "First Class Electric" --domain "firstclasselectricnj.com"
    python3 execution/apollo_find_owner.py --file leads.json --output enriched_leads.json
"""

import os
import sys
import json
import time
import argparse
from typing import Optional, Dict, List
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/v1"

# Job titles that indicate decision makers
OWNER_TITLES = [
    "owner",
    "founder", 
    "co-founder",
    "ceo",
    "president",
    "principal",
    "proprietor",
    "managing director",
    "general manager",
    "partner",
    "chief executive"
]


def search_people(
    company_name: str = None,
    domain: str = None,
    titles: List[str] = None,
    limit: int = 5
) -> List[Dict]:
    """
    Search Apollo for people at a company with specific titles.
    
    Args:
        company_name: Company name to search
        domain: Company domain (e.g., firstclasselectric.com)
        titles: List of job titles to filter by
        limit: Max results to return
        
    Returns: List of people found
    """
    if not APOLLO_API_KEY:
        print("❌ APOLLO_API_KEY not found in .env")
        return []
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY
    }
    
    # Build search query
    data = {
        "per_page": limit,
        "page": 1
    }
    
    # Add company/domain filter
    if domain:
        data["q_organization_domains"] = domain
    elif company_name:
        data["q_organization_name"] = company_name
    
    # Add title filter for owners/decision makers
    if titles:
        data["person_titles"] = titles
    else:
        data["person_titles"] = OWNER_TITLES
    
    try:
        response = requests.post(
            f"{APOLLO_BASE_URL}/mixed_people/search",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            people = result.get("people", [])
            return people
        else:
            print(f"      ❌ Apollo API error: {response.status_code}")
            if response.status_code == 401:
                print("      → Invalid API key. Check your APOLLO_API_KEY in .env")
            elif response.status_code == 429:
                print("      → Rate limited. Wait and try again.")
            return []
            
    except Exception as e:
        print(f"      ❌ Apollo request failed: {e}")
        return []


def get_email_for_person(person_id: str) -> Optional[str]:
    """
    Get email for a specific person by their Apollo ID.
    Uses separate endpoint to reveal email (costs 1 credit).
    """
    if not APOLLO_API_KEY:
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }
    
    data = {
        "api_key": APOLLO_API_KEY,
        "id": person_id,
        "reveal_personal_emails": True
    }
    
    try:
        response = requests.post(
            f"{APOLLO_BASE_URL}/people/match",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            person = result.get("person", {})
            return person.get("email")
        else:
            return None
            
    except Exception:
        return None


def find_decision_maker(
    company_name: str,
    domain: str = None,
    location: str = None
) -> Dict:
    """
    Find the decision maker (owner/CEO) for a company.
    
    Returns:
    {
        "found": bool,
        "owner_name": str,
        "owner_first_name": str,
        "owner_title": str,
        "email": str,
        "linkedin_url": str,
        "phone": str,
        "source": "apollo"
    }
    """
    result = {
        "found": False,
        "owner_name": None,
        "owner_first_name": None,
        "owner_title": None,
        "email": None,
        "linkedin_url": None,
        "phone": None,
        "source": "apollo"
    }
    
    # Clean domain
    if domain:
        domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    
    # Search for people with owner titles
    print(f"      🔍 Searching Apollo...")
    people = search_people(company_name=company_name, domain=domain)
    
    if not people:
        # Try with just company name if domain search failed
        if domain:
            print(f"      🔄 Retrying with company name only...")
            people = search_people(company_name=company_name)
    
    if people:
        # Get the first (best) match
        person = people[0]
        
        result["found"] = True
        result["owner_name"] = person.get("name")
        result["owner_first_name"] = person.get("first_name")
        result["owner_title"] = person.get("title")
        result["email"] = person.get("email")
        result["linkedin_url"] = person.get("linkedin_url")
        result["phone"] = person.get("phone_numbers", [{}])[0].get("sanitized_number") if person.get("phone_numbers") else None
        
        print(f"      ✅ Found: {result['owner_name']} ({result['owner_title']})")
        
        if result["email"]:
            print(f"      📧 Email: {result['email']}")
        else:
            print(f"      ⚠️  No email in response (may need credit to reveal)")
        
        if result["linkedin_url"]:
            print(f"      🔗 LinkedIn: {result['linkedin_url'][:50]}...")
    else:
        print(f"      ❌ No decision maker found in Apollo")
    
    return result


def enrich_leads_file(input_file: str, output_file: str = None, delay: float = 1.0) -> Dict:
    """
    Enrich all leads with Apollo decision maker data.
    """
    # Check API key first
    if not APOLLO_API_KEY:
        print("❌ APOLLO_API_KEY not found in .env")
        print("   Get your free API key at: https://app.apollo.io/signup")
        print("   Then add to .env: APOLLO_API_KEY=your_key_here")
        sys.exit(1)
    
    # Load leads
    with open(input_file, 'r') as f:
        leads = json.load(f)
    
    print(f"\n🎯 Apollo.io Decision Maker Search")
    print(f"   Total leads: {len(leads)}")
    print(f"   API Key: {'✅ Found' if APOLLO_API_KEY else '❌ Missing'}")
    print(f"   Searching for: Owners, CEOs, Founders")
    print()
    
    stats = {
        "total": len(leads),
        "found": 0,
        "with_email": 0,
        "with_linkedin": 0,
        "not_found": 0
    }
    
    for i, lead in enumerate(leads, 1):
        business_name = lead.get("name", "Unknown")
        website = lead.get("website", "")
        
        # Extract domain from website
        domain = None
        if website:
            domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        
        print(f"[{i}/{len(leads)}] {business_name[:40]}")
        
        result = find_decision_maker(business_name, domain)
        
        # Update lead with Apollo data
        if result["found"]:
            lead["apollo_owner_name"] = result["owner_name"]
            lead["apollo_owner_first_name"] = result["owner_first_name"]
            lead["apollo_owner_title"] = result["owner_title"]
            lead["apollo_linkedin"] = result["linkedin_url"]
            
            # Only update email if Apollo has one and current email is missing/invalid
            if result["email"]:
                lead["apollo_email"] = result["email"]
                stats["with_email"] += 1
            
            if result["linkedin_url"]:
                stats["with_linkedin"] += 1
            
            stats["found"] += 1
        else:
            stats["not_found"] += 1
        
        # Rate limiting
        if i < len(leads):
            time.sleep(delay)
    
    # Save enriched leads
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(leads, f, indent=2)
        print(f"\n💾 Saved to: {output_file}")
    
    # Print summary
    print(f"\n📊 Apollo Enrichment Summary:")
    print(f"   Total processed: {stats['total']}")
    print(f"   Decision makers found: {stats['found']}")
    print(f"   With email: {stats['with_email']}")
    print(f"   With LinkedIn: {stats['with_linkedin']}")
    print(f"   Not found: {stats['not_found']}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Find decision makers using Apollo.io")
    parser.add_argument("--company", "-c", help="Company name to search")
    parser.add_argument("--domain", "-d", help="Company domain")
    parser.add_argument("--file", "-f", help="JSON file with leads to enrich")
    parser.add_argument("--output", "-o", help="Output file for enriched leads")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    
    args = parser.parse_args()
    
    if args.company:
        # Single company lookup
        print(f"\n🎯 Searching Apollo for: {args.company}")
        result = find_decision_maker(args.company, args.domain)
        
        print(f"\n📋 Results:")
        print(json.dumps(result, indent=2))
        
    elif args.file:
        # File enrichment
        output = args.output or args.file.replace('.json', '_apollo.json')
        enrich_leads_file(args.file, output, delay=args.delay)
    else:
        parser.print_help()
        print("\n❌ Please provide --company or --file argument")
        print("\n📝 First, add your Apollo API key to .env:")
        print("   APOLLO_API_KEY=your_api_key_here")
        print("\n   Get free key at: https://app.apollo.io/signup")
        sys.exit(1)


if __name__ == "__main__":
    main()
