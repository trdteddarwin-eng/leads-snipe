#!/usr/bin/env python3
"""
Anymailfinder Decision Maker Email Finder (ASYNC VERSION)

Finds decision maker (CEO/Owner) emails using Anymailfinder API with async parallel processing.

Usage:
    python3 execution/anymailfinder_decision_maker_async.py \
      --input .tmp/leads.json \
      --output .tmp/leads_with_owners.json \
      --category ceo

Cost: 2 credits per valid email found (~$0.04/email)
Performance: 10x faster with parallel processing
"""

import os
import sys
import json
import argparse
import asyncio
from urllib.parse import urlparse
from typing import Optional, Dict, List
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
ANYMAILFINDER_API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
ANYMAILFINDER_API_URL = "https://api.anymailfinder.com/v5.1/find-email/decision-maker"

if not ANYMAILFINDER_API_KEY:
    print("❌ ANYMAILFINDER_API_KEY not found in .env")
    sys.exit(1)


def extract_domain(website_url: str) -> Optional[str]:
    """
    Extract clean domain from website URL.

    Examples:
        "https://abchvac.com" → "abchvac.com"
        "http://www.example.com/" → "example.com"
        "abchvac.com" → "abchvac.com"

    Args:
        website_url: Full website URL or domain

    Returns:
        Clean domain or None if invalid
    """
    if not website_url:
        return None

    # Add protocol if missing
    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url

    try:
        parsed = urlparse(website_url)
        domain = parsed.netloc or parsed.path

        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]

        # Remove trailing slash
        domain = domain.rstrip('/')

        return domain if domain else None
    except Exception as e:
        print(f"   ⚠️  Error parsing URL '{website_url}': {e}")
        return None


async def find_decision_maker_email(
    session: aiohttp.ClientSession,
    domain: str,
    category: str = "ceo",
    timeout: int = 15
) -> Optional[Dict]:
    """
    Find decision maker email using Anymailfinder API (async).

    Args:
        session: aiohttp session
        domain: Company domain (e.g., "abchvac.com")
        category: Decision maker category (default: "ceo")
        timeout: Request timeout in seconds

    Returns:
        Dict with email, full_name, job_title, linkedin_url, status
        or None if not found
    """
    try:
        payload = {
            "domain": domain,
            "decision_maker_category": [category]
        }

        headers = {
            "Authorization": f"Bearer {ANYMAILFINDER_API_KEY}",
            "Content-Type": "application/json"
        }

        async with session.post(
            ANYMAILFINDER_API_URL,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            if response.status == 200:
                data = await response.json()

                # Extract decision maker info
                email = data.get('email') or data.get('valid_email')
                status = data.get('email_status')

                # Only return if email found and valid
                if email and status == 'valid':
                    return {
                        "email": email,
                        "full_name": data.get('person_full_name'),
                        "job_title": data.get('person_job_title'),
                        "linkedin_url": data.get('person_linkedin_url'),
                        "status": status
                    }
                else:
                    return None

            elif response.status == 401:
                print(f"\n❌ API Authentication Error: Invalid API key")
                return None

            elif response.status == 429:
                print(f"\n❌ Rate Limit Exceeded: Too many requests")
                return None

            else:
                return None

    except asyncio.TimeoutError:
        print(f"   ⏱️  Timeout after {timeout}s for {domain}")
        return None

    except Exception as e:
        print(f"   ❌ Request failed for {domain}: {e}")
        return None


async def enrich_single_lead(
    session: aiohttp.ClientSession,
    lead: Dict,
    category: str = "ceo",
    timeout: int = 15
) -> Dict:
    """
    Enrich a single lead with decision maker information (async).

    Args:
        session: aiohttp session
        lead: Lead dictionary from N8N scraper
        category: Decision maker category to search for
        timeout: API timeout per request

    Returns:
        Enriched lead with decision_maker field
    """
    business_name = lead.get('name', 'Unknown')
    website = lead.get('website')
    business_email = lead.get('email')

    # Skip if no website
    if not website:
        lead['decision_maker'] = {
            "email": business_email,
            "full_name": None,
            "job_title": "Business Contact",
            "linkedin_url": None,
            "status": "no_website"
        }
        lead['anymailfinder_credits_used'] = 0
        return lead

    # Extract domain
    domain = extract_domain(website)
    if not domain:
        lead['decision_maker'] = {
            "email": business_email,
            "full_name": None,
            "job_title": "Business Contact",
            "linkedin_url": None,
            "status": "invalid_domain"
        }
        lead['anymailfinder_credits_used'] = 0
        return lead

    # Find decision maker
    decision_maker = await find_decision_maker_email(session, domain, category, timeout)

    if decision_maker:
        lead['decision_maker'] = decision_maker
        lead['anymailfinder_credits_used'] = 2
    else:
        # Fallback to business email
        lead['decision_maker'] = {
            "email": business_email,
            "full_name": None,
            "job_title": "Business Contact",
            "linkedin_url": None,
            "status": "not_found"
        }
        lead['anymailfinder_credits_used'] = 0

    return lead


async def enrich_leads_with_decision_makers(
    leads: List[Dict],
    category: str = "ceo",
    timeout: int = 15,
    max_concurrent: int = 10
) -> List[Dict]:
    """
    Enrich leads with decision maker information (async parallel).

    Args:
        leads: List of lead dictionaries from N8N scraper
        category: Decision maker category to search for
        timeout: API timeout per request
        max_concurrent: Maximum concurrent requests

    Returns:
        List of enriched leads with decision_maker field
    """
    stats = {
        "total": len(leads),
        "found": 0,
        "no_website": 0,
        "not_found": 0,
        "credits_used": 0
    }

    print(f"\n{'='*70}")
    print(f"🔍 FINDING DECISION MAKERS (ASYNC)")
    print(f"{'='*70}")
    print(f"Processing {len(leads)} leads in parallel...")
    print(f"Max concurrent: {max_concurrent}")
    print(f"Category: {category}")
    print()

    # Create aiohttp session with connection pooling
    connector = aiohttp.TCPConnector(limit=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Create tasks for all leads
        tasks = [
            enrich_single_lead(session, lead, category, timeout)
            for lead in leads
        ]

        # Process in parallel with progress tracking
        enriched_leads = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            enriched_lead = await task
            enriched_leads.append(enriched_lead)

            # Update stats
            dm = enriched_lead['decision_maker']
            if dm['status'] == 'valid':
                stats['found'] += 1
                stats['credits_used'] += 2
                print(f"[{i}/{len(leads)}] {enriched_lead.get('name', 'Unknown')} ✅ {dm['email']}")
            elif dm['status'] == 'no_website' or dm['status'] == 'invalid_domain':
                stats['no_website'] += 1
                print(f"[{i}/{len(leads)}] {enriched_lead.get('name', 'Unknown')} ❌ No website")
            else:
                stats['not_found'] += 1
                print(f"[{i}/{len(leads)}] {enriched_lead.get('name', 'Unknown')} ⚠️  Not found")

    # Print summary
    print(f"\n{'='*70}")
    print(f"✅ ENRICHMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Total leads: {stats['total']}")
    print(f"✅ Decision makers found: {stats['found']}/{stats['total']} ({100*stats['found']//max(stats['total'],1)}%)")
    print(f"❌ No website: {stats['no_website']}")
    print(f"⚠️  Not found (using business email): {stats['not_found']}")
    print(f"💰 Credits used: {stats['credits_used']} (~${stats['credits_used']*0.02:.2f})")
    print()

    return enriched_leads


def main():
    parser = argparse.ArgumentParser(
        description='Find decision maker emails using Anymailfinder API (async)'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input JSON file from N8N scraper'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file with decision makers'
    )
    parser.add_argument(
        '--category', '-c',
        default='ceo',
        choices=['ceo', 'finance', 'engineering', 'hr', 'it', 'logistics',
                 'marketing', 'operations', 'buyer', 'sales'],
        help='Decision maker category to search for (default: ceo)'
    )
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        default=15,
        help='API timeout in seconds (default: 15)'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=10,
        help='Maximum concurrent requests (default: 10)'
    )

    args = parser.parse_args()

    # Load leads
    try:
        with open(args.input, 'r') as f:
            leads = json.load(f)

        if not isinstance(leads, list):
            print(f"❌ Error: Input file must contain a JSON array of leads")
            sys.exit(1)

        print(f"📂 Loaded {len(leads)} leads from {args.input}")

    except FileNotFoundError:
        print(f"❌ Error: Input file '{args.input}' not found")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}")
        sys.exit(1)

    # Enrich leads (async)
    enriched_leads = asyncio.run(enrich_leads_with_decision_makers(
        leads,
        category=args.category,
        timeout=args.timeout,
        max_concurrent=args.max_concurrent
    ))

    # Save enriched leads
    try:
        with open(args.output, 'w') as f:
            json.dump(enriched_leads, f, indent=2)

        print(f"💾 Saved {len(enriched_leads)} enriched leads to {args.output}")
        print(f"🎉 Done!")

    except Exception as e:
        print(f"❌ Error saving output: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
