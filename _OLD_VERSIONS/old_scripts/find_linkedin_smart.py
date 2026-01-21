#!/usr/bin/env python3
"""
Smart LinkedIn Profile Finder

Multi-source LinkedIn discovery using:
1. Anymailfinder response (if already provided)
2. Website HTML parsing (from N8N scraped_text)
3. DuckDuckGo search (FREE, unlimited)

Usage:
    pip install ddgs

    python3 execution/find_linkedin_smart.py \
      --input .tmp/leads_with_owners.json \
      --output .tmp/leads_final.json \
      --delay 2

Cost: $0.00 (100% FREE)
"""

import os
import sys
import json
import argparse
import time
import re
from typing import Optional, Dict, List
from ddgs import DDGS

def extract_linkedin_from_html(scraped_text: str) -> Optional[str]:
    """
    Extract LinkedIn profile URL from website HTML.

    Args:
        scraped_text: HTML content from N8N scraper

    Returns:
        LinkedIn profile URL or None
    """
    if not scraped_text:
        return None

    # Pattern for LinkedIn profile URLs
    # Matches: linkedin.com/in/username or www.linkedin.com/in/username
    pattern = r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+'

    matches = re.findall(pattern, scraped_text, re.IGNORECASE)

    if matches:
        # Return first profile found, clean it up
        url = matches[0]
        # Ensure it's not a company page
        if '/company/' not in url:
            return url

    return None


def validate_linkedin_url(url: str) -> bool:
    """
    Validate LinkedIn profile URL.

    Valid:
    - linkedin.com/in/username
    - www.linkedin.com/in/username

    Invalid:
    - linkedin.com/company/... (company page)
    - linkedin.com/feed/... (feed)

    Args:
        url: LinkedIn URL to validate

    Returns:
        True if valid profile URL
    """
    if not url:
        return False

    pattern = r'^https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?$'
    return bool(re.match(pattern, url))


def extract_linkedin_from_search_results(search_results: List) -> Optional[str]:
    """
    Extract LinkedIn profile URL from DuckDuckGo search results.

    Args:
        search_results: List of search result dictionaries

    Returns:
        First valid LinkedIn profile URL found or None
    """
    for result in search_results:
        # Check href/link
        url = result.get('href') or result.get('link') or ''

        if 'linkedin.com/in/' in url and '/company/' not in url:
            # Clean and validate
            if validate_linkedin_url(url):
                return url

        # Check body text for URLs
        body = result.get('body', '')
        linkedin_match = re.search(
            r'https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+',
            body,
            re.IGNORECASE
        )
        if linkedin_match:
            url = linkedin_match.group(0)
            if validate_linkedin_url(url):
                return url

    return None


def search_linkedin_duckduckgo(
    query: str,
    max_results: int = 3,
    delay: float = 0.5
) -> Optional[str]:
    """
    Search for LinkedIn profile using DuckDuckGo.

    Args:
        query: Search query
        max_results: Number of results to fetch
        delay: Delay before search (seconds)

    Returns:
        LinkedIn profile URL or None
    """
    try:
        # Small delay to avoid rate limiting
        time.sleep(delay)

        # Search DuckDuckGo
        results = DDGS().text(query, max_results=max_results)

        # Extract LinkedIn URL from results
        linkedin_url = extract_linkedin_from_search_results(results)

        return linkedin_url

    except Exception as e:
        print(f"      ⚠️  Search error: {e}")
        return None


def find_linkedin_multi_strategy(
    lead: Dict,
    delay: float = 0.5,
    max_strategies: int = 2
) -> Dict:
    """
    Find LinkedIn profile using multiple strategies.

    Strategies (in order):
    1. Check Anymailfinder response
    2. Parse website HTML
    3. DuckDuckGo: Full name + Job title + Company
    4. DuckDuckGo: Full name + Company + Location
    5. DuckDuckGo: Email username + Company
    6. DuckDuckGo: Company + "owner" OR "founder"

    Args:
        lead: Lead dictionary with decision_maker field
        delay: Delay between DuckDuckGo searches
        max_strategies: Maximum number of DuckDuckGo strategies to try

    Returns:
        Dict with linkedin_url and linkedin_source
    """
    # Extract data
    decision_maker = lead.get('decision_maker', {})
    business_name = lead.get('name', '')
    address = lead.get('address', '')
    scraped_text = lead.get('scraped_text', '')

    full_name = decision_maker.get('full_name')
    job_title = decision_maker.get('job_title')
    email = decision_maker.get('email')
    anymailfinder_linkedin = decision_maker.get('linkedin_url')

    # Extract city from address
    city = ''
    if address:
        # "123 Main St, Newark, NJ 07102" → "Newark, NJ"
        parts = address.split(',')
        if len(parts) >= 2:
            city = f"{parts[-2].strip()}, {parts[-1].split()[0].strip()}"

    # STRATEGY 1: Check Anymailfinder response
    if anymailfinder_linkedin and validate_linkedin_url(anymailfinder_linkedin):
        return {
            "linkedin_url": anymailfinder_linkedin,
            "linkedin_source": "anymailfinder"
        }

    # STRATEGY 2: Parse website HTML
    html_linkedin = extract_linkedin_from_html(scraped_text)
    if html_linkedin:
        return {
            "linkedin_url": html_linkedin,
            "linkedin_source": "website_html"
        }

    # If no decision maker info, skip DuckDuckGo searches
    if not full_name and not email:
        return {
            "linkedin_url": None,
            "linkedin_source": None
        }

    # STRATEGY 3: DuckDuckGo - Full name + Job title + Company
    if full_name and job_title and business_name and max_strategies >= 1:
        query = f'site:linkedin.com/in "{full_name}" "{job_title}" "{business_name}"'
        print(f"      🔍 Strategy 1: Name + Title + Company... ", end="", flush=True)

        result = search_linkedin_duckduckgo(query, delay=delay)
        if result:
            print("✅")
            return {
                "linkedin_url": result,
                "linkedin_source": "duckduckgo_strategy_1"
            }
        print("❌")

    # STRATEGY 4: DuckDuckGo - Full name + Company + Location
    if full_name and business_name and city and max_strategies >= 2:
        query = f'site:linkedin.com/in "{full_name}" "{business_name}" "{city}"'
        print(f"      🔍 Strategy 2: Name + Company + Location... ", end="", flush=True)

        result = search_linkedin_duckduckgo(query, delay=delay)
        if result:
            print("✅")
            return {
                "linkedin_url": result,
                "linkedin_source": "duckduckgo_strategy_2"
            }
        print("❌")

    # STRATEGY 5: DuckDuckGo - Email username + Company
    if email and business_name and max_strategies >= 3:
        # Extract username from email
        username = email.split('@')[0] if '@' in email else None

        if username:
            # Try both with dots and without
            username_nodots = username.replace('.', '')

            query = f'site:linkedin.com/in "{username}" OR "{username_nodots}" "{business_name}"'
            print(f"      🔍 Strategy 3: Email username + Company... ", end="", flush=True)

            result = search_linkedin_duckduckgo(query, delay=delay)
            if result:
                print("✅")
                return {
                    "linkedin_url": result,
                    "linkedin_source": "duckduckgo_strategy_3"
                }
            print("❌")

    # STRATEGY 6: DuckDuckGo - Company + owner keywords
    if business_name and max_strategies >= 4:
        query = f'site:linkedin.com/in "{business_name}" owner OR founder OR CEO'
        print(f"      🔍 Strategy 4: Company + owner keywords... ", end="", flush=True)

        result = search_linkedin_duckduckgo(query, delay=delay)
        if result:
            print("✅")
            return {
                "linkedin_url": result,
                "linkedin_source": "duckduckgo_strategy_4"
            }
        print("❌")

    # Not found
    return {
        "linkedin_url": None,
        "linkedin_source": None
    }


def find_linkedin_for_leads(
    leads: List[Dict],
    delay: float = 0.5,
    max_strategies: int = 2
) -> List[Dict]:
    """
    Find LinkedIn profiles for all leads.

    Args:
        leads: List of enriched leads from anymailfinder
        delay: Delay between DuckDuckGo searches
        max_strategies: Max number of DuckDuckGo strategies per lead

    Returns:
        List of leads with linkedin_url and linkedin_source added
    """
    enriched_leads = []

    stats = {
        "total": len(leads),
        "anymailfinder": 0,
        "website_html": 0,
        "duckduckgo": 0,
        "not_found": 0
    }

    print(f"\n{'='*70}")
    print(f"🔍 FINDING LINKEDIN PROFILES")
    print(f"{'='*70}")
    print(f"Processing {len(leads)} leads...")
    print(f"DuckDuckGo delay: {delay}s between searches")
    print()

    for i, lead in enumerate(leads, 1):
        business_name = lead.get('name', 'Unknown')
        decision_maker = lead.get('decision_maker', {})
        full_name = decision_maker.get('full_name') or 'Unknown'

        print(f"[{i}/{len(leads)}] {full_name} ({business_name})")

        # Check Anymailfinder first
        anymailfinder_linkedin = decision_maker.get('linkedin_url')
        if anymailfinder_linkedin:
            print(f"   ✅ Source: anymailfinder → {anymailfinder_linkedin}")
            stats['anymailfinder'] += 1

            lead['decision_maker']['linkedin_url'] = anymailfinder_linkedin
            lead['decision_maker']['linkedin_source'] = 'anymailfinder'
            enriched_leads.append(lead)
            continue

        # Try multi-strategy search
        print(f"   ⏭️  Anymailfinder: No LinkedIn")

        # Check HTML
        html_linkedin = extract_linkedin_from_html(lead.get('scraped_text', ''))
        if html_linkedin:
            print(f"   ✅ Source: website_html → {html_linkedin}")
            stats['website_html'] += 1

            lead['decision_maker']['linkedin_url'] = html_linkedin
            lead['decision_maker']['linkedin_source'] = 'website_html'
            enriched_leads.append(lead)
            continue

        print(f"   ⏭️  HTML: No LinkedIn found")

        # DuckDuckGo searches
        if decision_maker.get('full_name') or decision_maker.get('email'):
            print(f"   🔍 DuckDuckGo: Searching...")

            result = find_linkedin_multi_strategy(lead, delay, max_strategies)

            if result['linkedin_url']:
                print(f"   ✅ Source: {result['linkedin_source']} → {result['linkedin_url']}")
                stats['duckduckgo'] += 1

                lead['decision_maker']['linkedin_url'] = result['linkedin_url']
                lead['decision_maker']['linkedin_source'] = result['linkedin_source']
            else:
                print(f"   ❌ Not found")
                stats['not_found'] += 1

                lead['decision_maker']['linkedin_url'] = None
                lead['decision_maker']['linkedin_source'] = None
        else:
            print(f"   ⏭️  No decision maker info, skipping DuckDuckGo")
            stats['not_found'] += 1

            lead['decision_maker']['linkedin_url'] = None
            lead['decision_maker']['linkedin_source'] = None

        enriched_leads.append(lead)
        print()

    # Summary
    total_found = stats['anymailfinder'] + stats['website_html'] + stats['duckduckgo']

    print(f"{'='*70}")
    print(f"✅ LINKEDIN DISCOVERY COMPLETE")
    print(f"{'='*70}")
    print(f"Total leads: {stats['total']}")
    print(f"✅ LinkedIn found: {total_found}/{stats['total']} ({100*total_found//max(stats['total'],1)}%)")
    print(f"   - Anymailfinder: {stats['anymailfinder']}")
    print(f"   - Website HTML: {stats['website_html']}")
    print(f"   - DuckDuckGo: {stats['duckduckgo']}")
    print(f"❌ Not found: {stats['not_found']}")
    print(f"💰 Cost: $0.00 (FREE)")
    print()

    return enriched_leads


def main():
    parser = argparse.ArgumentParser(
        description='Find LinkedIn profiles using multi-source discovery'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input JSON file with decision makers'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output JSON file with LinkedIn profiles'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.5,
        help='Delay between DuckDuckGo searches in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--max-strategies', '-m',
        type=int,
        default=2,
        help='Maximum DuckDuckGo strategies to try per lead (default: 2)'
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

    # Find LinkedIn profiles
    enriched_leads = find_linkedin_for_leads(
        leads,
        delay=args.delay,
        max_strategies=args.max_strategies
    )

    # Save results
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
