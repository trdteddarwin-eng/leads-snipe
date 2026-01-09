#!/usr/bin/env python3
"""
Anymailfinder Integration for Email Discovery

Uses Anymailfinder API to find verified emails.
- From LinkedIn URL: find-email/linkedin-url
- From Name + Domain: find-email/personal

Pricing: Pay only for verified emails found (~$0.01-0.02/email)

Usage:
    python3 execution/anymailfinder_email.py --linkedin "https://linkedin.com/in/mattrusso"
    python3 execution/anymailfinder_email.py --name "John Smith" --domain "company.com"
    python3 execution/anymailfinder_email.py --file leads.json --output enriched_leads.json
"""

import os
import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ANYMAILFINDER_API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
ANYMAILFINDER_BASE_URL = "https://api.anymailfinder.com/v5.1"


def find_email_by_linkedin(linkedin_url: str) -> Dict:
    """
    Find email using LinkedIn profile URL.
    
    Args:
        linkedin_url: Full LinkedIn profile URL
        
    Returns:
        {
            "found": bool,
            "email": str,
            "name": str,
            "title": str,
            "company": str,
            "verification": str,
            "credits_used": int
        }
    """
    result = {
        "found": False,
        "email": None,
        "name": None,
        "title": None,
        "company": None,
        "verification": None,
        "credits_used": 0
    }
    
    if not ANYMAILFINDER_API_KEY:
        print("      ❌ ANYMAILFINDER_API_KEY not found in .env")
        return result
    
    try:
        response = requests.post(
            f"{ANYMAILFINDER_BASE_URL}/find-email/linkedin-url",
            headers={
                "Authorization": f"Bearer {ANYMAILFINDER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"linkedin_url": linkedin_url},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("email"):
                result["found"] = True
                result["email"] = data.get("email")
                result["name"] = data.get("name")
                result["title"] = data.get("title")
                result["company"] = data.get("company")
                result["verification"] = data.get("verification")
                result["credits_used"] = 1
                
        elif response.status_code == 404:
            # Email not found - no charge
            result["found"] = False
        elif response.status_code == 401:
            print("      ❌ Invalid API key")
        elif response.status_code == 402:
            print("      ❌ No credits remaining")
        else:
            print(f"      ❌ API error: {response.status_code}")
            
    except Exception as e:
        print(f"      ❌ Request failed: {e}")
    
    return result


def find_email_by_name_domain(first_name: str, last_name: str, domain: str) -> Dict:
    """
    Find email using name + company domain.
    
    Args:
        first_name: Person's first name
        last_name: Person's last name
        domain: Company domain (e.g., company.com)
        
    Returns:
        {
            "found": bool,
            "email": str,
            "verification": str,
            "credits_used": int
        }
    """
    result = {
        "found": False,
        "email": None,
        "verification": None,
        "credits_used": 0
    }
    
    if not ANYMAILFINDER_API_KEY:
        print("      ❌ ANYMAILFINDER_API_KEY not found in .env")
        return result
    
    # Clean domain
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
    
    try:
        response = requests.post(
            f"{ANYMAILFINDER_BASE_URL}/find-email/personal",
            headers={
                "Authorization": f"Bearer {ANYMAILFINDER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "first_name": first_name,
                "last_name": last_name,
                "domain": domain
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("email"):
                result["found"] = True
                result["email"] = data.get("email")
                result["verification"] = data.get("verification")
                # Extract extra info if Anymailfinder provides it (LinkedIn, Name, etc)
                result["linkedin_url"] = data.get("linkedin_url") or data.get("social", {}).get("linkedin")
                result["name"] = data.get("name") or f"{first_name} {last_name}"
                result["title"] = data.get("title")
                result["credits_used"] = 1
                
        elif response.status_code == 404:
            result["found"] = False
        elif response.status_code == 401:
            print("      ❌ Invalid API key")
        elif response.status_code == 402:
            print("      ❌ No credits remaining")
        else:
            print(f"      ❌ API error: {response.status_code}")
            
    except Exception as e:
        print(f"      ❌ Request failed: {e}")
    
    return result


def find_decision_maker(domain: str, category: List[str] = None) -> Dict:
    """
    Find decision maker (CEO/Owner) email using Anymailfinder's decision-maker endpoint.

    Args:
        domain: Company domain (e.g., company.com)
        category: List of roles to search for (default: ["ceo"])

    Returns:
        {
            "found": bool,
            "email": str,
            "name": str,
            "title": str,
            "linkedin_url": str,
            "credits_used": int
        }
    """
    if category is None:
        category = ["ceo"]

    result = {
        "found": False,
        "email": None,
        "name": None,
        "title": None,
        "linkedin_url": None,
        "credits_used": 0
    }

    if not ANYMAILFINDER_API_KEY:
        print("      ❌ ANYMAILFINDER_API_KEY not found in .env")
        return result

    # Clean domain
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

    try:
        response = requests.post(
            f"{ANYMAILFINDER_BASE_URL}/decision-maker",
            headers={
                "Authorization": f"Bearer {ANYMAILFINDER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "domain": domain,
                "category": category
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("email"):
                result["found"] = True
                result["email"] = data.get("email")
                result["name"] = data.get("name")
                result["title"] = data.get("title")
                result["linkedin_url"] = data.get("linkedin_url") or data.get("social", {}).get("linkedin")
                result["credits_used"] = 1
                print(f"      ⚡ Decision-maker found: {result['email']} ({result['title']})")

        elif response.status_code == 404:
            result["found"] = False
        elif response.status_code == 401:
            print("      ❌ Invalid API key")
        elif response.status_code == 402:
            print("      ❌ No credits remaining")
        else:
            print(f"      ❌ API error: {response.status_code}")

    except Exception as e:
        print(f"      ❌ Request failed: {e}")

    return result


def find_email_for_lead(lead: Dict) -> Dict:
    """
    Smart-Hunter tiered enrichment for finding CEO/Owner emails.

    Priority (Tiered System):
    Stage 1: LinkedIn URL lookup (if available) - most accurate
    Stage 2: Decision-maker fallback (if no LinkedIn) - finds CEO directly
    Stage 3: Name + domain lookup (legacy fallback)

    Returns updated lead with email data.
    """
    linkedin_url = lead.get("linkedin_url") or lead.get("apollo_linkedin")
    owner_name = lead.get("owner_name") or lead.get("apollo_owner_name")
    website = lead.get("website", "")

    # Extract domain
    domain = None
    if website:
        domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]

    result = {"found": False}

    # ========================================================================
    # STAGE 1: LinkedIn URL lookup (most accurate - identity verified)
    # ========================================================================
    if linkedin_url and "linkedin.com/in/" in linkedin_url:
        print(f"      🔗 Stage 1: LinkedIn lookup: {linkedin_url[:40]}...")
        result = find_email_by_linkedin(linkedin_url)

        if result["found"]:
            lead["anymailfinder_email"] = result["email"]
            lead["anymailfinder_name"] = result.get("name")
            lead["anymailfinder_title"] = result.get("title")
            lead["enrichment_source"] = "linkedin"
            print(f"      ✅ Found via LinkedIn: {result['email']}")
            return lead

    # ========================================================================
    # STAGE 2: Decision-maker fallback (CEO/Owner direct lookup)
    # Only triggered if NO LinkedIn URL was available
    # ========================================================================
    if not linkedin_url and domain:
        print(f"      ⚡ Stage 2: Decision-maker lookup (CEO) @ {domain}...")
        result = find_decision_maker(domain, category=["ceo"])

        if result["found"]:
            lead["anymailfinder_email"] = result["email"]
            lead["anymailfinder_name"] = result.get("name")
            lead["anymailfinder_title"] = result.get("title")
            lead["enrichment_source"] = "decision_maker"
            # Also capture LinkedIn if returned
            if result.get("linkedin_url") and not lead.get("linkedin_url"):
                lead["linkedin_url"] = result["linkedin_url"]
            # Update owner name if not set
            if result.get("name") and not lead.get("owner_name"):
                lead["owner_name"] = result["name"]
                lead["owner_first_name"] = result["name"].split()[0] if result["name"] else None
            print(f"      ✅ Found CEO: {result['email']}")
            return lead

    # ========================================================================
    # STAGE 3: Name + domain lookup (legacy fallback)
    # ========================================================================
    if owner_name and domain:
        # Parse name into first/last
        name_parts = owner_name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = " ".join(name_parts[1:])

            print(f"      👤 Stage 3: Name+domain lookup: {first_name} {last_name} @ {domain}")
            result = find_email_by_name_domain(first_name, last_name, domain)

            if result["found"]:
                lead["anymailfinder_email"] = result["email"]
                lead["enrichment_source"] = "name_domain"
                if result.get("linkedin_url"):
                    lead["linkedin_url"] = lead.get("linkedin_url") or result["linkedin_url"]
                if result.get("name") and not lead.get("owner_name"):
                    lead["owner_name"] = result["name"]
                print(f"      ✅ Found via name+domain: {result['email']}")
                return lead

    print(f"      ❌ No email found (all stages exhausted)")
    return lead


def enrich_leads_file(input_file: str, output_file: str = None, concurrency: int = 10) -> Dict:
    """
    Enrich leads with emails from Anymailfinder using parallel processing.

    Args:
        input_file: Path to JSON file with leads
        output_file: Path to save enriched leads
        concurrency: Number of parallel workers (default 8)

    Returns summary statistics.
    """
    import threading

    if not ANYMAILFINDER_API_KEY:
        print("❌ ANYMAILFINDER_API_KEY not found in .env")
        print("   Get your API key at: https://anymailfinder.com")
        print("   Then add to .env: ANYMAILFINDER_API_KEY=your_key_here")
        sys.exit(1)

    # Load leads
    with open(input_file, 'r') as f:
        leads = json.load(f)

    print(f"\n📧 Anymailfinder Email Discovery (Parallel Mode)")
    print(f"   Total leads: {len(leads)}")
    print(f"   Concurrency: {concurrency} workers")
    print(f"   API Key: ✅ Found")
    print(f"   Note: Only charged for verified emails found!")
    print()

    stats = {
        "total": len(leads),
        "emails_found": 0,
        "linkedin_used": 0,
        "name_domain_used": 0,
        "not_found": 0,
        "skipped": 0,
        "credits_used": 0
    }
    stats_lock = threading.Lock()

    def process_single_lead(idx_lead):
        """Process a single lead - designed for thread pool execution."""
        idx, lead = idx_lead
        business_name = lead.get("name", "Unknown")
        linkedin_url = lead.get("linkedin_url") or lead.get("apollo_linkedin")

        print(f"[{idx}/{len(leads)}] {business_name[:40]}")

        # Skip ONLY if already has a VALID AND DELIVERABLE email
        existing_email = lead.get("email", "")
        verif = lead.get("email_verification", {})

        # If it has an email and it's marked as deliverable, we skip
        if existing_email and verif.get("deliverable") is True:
            print(f"      ⏭️  Already has verified email: {existing_email}")
            with stats_lock:
                stats["skipped"] += 1
            return lead

        # If it has an email but NO verification yet, we check basic syntax as fallback
        if existing_email and not verif:
            if "@" in existing_email and ".com" in existing_email:
                if not any(ext in existing_email.lower() for ext in ['.png', '.jpg', '.webp', '.gif']):
                    print(f"      ⏭️  Existing unverified email (skipping to be safe): {existing_email}")
                    with stats_lock:
                        stats["skipped"] += 1
                    return lead

        # Try to find email
        enriched_lead = find_email_for_lead(lead)

        # Thread-safe stats update
        with stats_lock:
            if enriched_lead.get("anymailfinder_email"):
                stats["emails_found"] += 1
                stats["credits_used"] += 1

                if linkedin_url:
                    stats["linkedin_used"] += 1
                else:
                    stats["name_domain_used"] += 1
            else:
                stats["not_found"] += 1

        return enriched_lead

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all leads for processing
        futures = {executor.submit(process_single_lead, (i, lead)): i
                   for i, lead in enumerate(leads, 1)}

        # Wait for all to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                idx = futures[future]
                print(f"      ❌ Error processing lead {idx}: {e}")

    # Save enriched leads
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(leads, f, indent=2)
        print(f"\n💾 Saved to: {output_file}")

    # Print summary
    print(f"\n📊 Anymailfinder Summary:")
    print(f"   Total processed: {stats['total']}")
    print(f"   Emails found: {stats['emails_found']}")
    print(f"   Via LinkedIn: {stats['linkedin_used']}")
    print(f"   Via Name+Domain: {stats['name_domain_used']}")
    print(f"   Skipped (already had email): {stats['skipped']}")
    print(f"   Not found: {stats['not_found']}")
    print(f"   Credits used: {stats['credits_used']} (~${stats['credits_used'] * 0.02:.2f})")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Find emails using Anymailfinder")
    parser.add_argument("--linkedin", "-l", help="LinkedIn URL to find email for")
    parser.add_argument("--name", "-n", help="Full name (for name+domain search)")
    parser.add_argument("--domain", "-d", help="Domain (for name+domain search)")
    parser.add_argument("--file", "-f", help="JSON file with leads to enrich")
    parser.add_argument("--output", "-o", help="Output file for enriched leads")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (legacy, ignored)")
    parser.add_argument("--concurrency", "-c", type=int, default=10, help="Number of parallel workers (default: 10)")

    args = parser.parse_args()

    if args.linkedin:
        # LinkedIn lookup
        print(f"\n🔗 Finding email for: {args.linkedin}")
        result = find_email_by_linkedin(args.linkedin)
        print(json.dumps(result, indent=2))

    elif args.name and args.domain:
        # Name + domain lookup
        name_parts = args.name.split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        print(f"\n👤 Finding email for: {args.name} @ {args.domain}")
        result = find_email_by_name_domain(first_name, last_name, args.domain)
        print(json.dumps(result, indent=2))

    elif args.file:
        # File enrichment with parallel processing
        output = args.output or args.file.replace('.json', '_emails.json')
        enrich_leads_file(args.file, output, concurrency=args.concurrency)
        
    else:
        parser.print_help()
        print("\n📝 Add your API key to .env:")
        print("   ANYMAILFINDER_API_KEY=your_key_here")
        print("\n   Get key at: https://anymailfinder.com")


if __name__ == "__main__":
    main()
