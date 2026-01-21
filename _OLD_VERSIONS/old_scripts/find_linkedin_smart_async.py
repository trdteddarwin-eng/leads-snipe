#!/usr/bin/env python3
"""
Smart LinkedIn Profile Finder (ASYNC VERSION)

Multi-source LinkedIn discovery using:
1. Anymailfinder response (if already provided)
2. Website HTML parsing (from N8N scraped_text)
3. DuckDuckGo search (FREE, unlimited) with async parallel processing

Usage:
    pip install ddgs aiohttp

    python3 execution/find_linkedin_smart_async.py \
      --input .tmp/leads_with_owners.json \
      --output .tmp/leads_final.json \
      --delay 0.5

Cost: $0.00 (100% FREE)
Performance: 5-10x faster with parallel processing
"""

import os
import sys
import json
import argparse
import asyncio
import re
from typing import Optional, Dict, List
from ddgs import DDGS
from datetime import datetime

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


async def search_linkedin_duckduckgo(
    query: str,
    max_results: int = 3,
    delay: float = 0.5
) -> Optional[str]:
    """
    Search for LinkedIn profile using DuckDuckGo (async).

    Args:
        query: Search query
        max_results: Number of results to fetch
        delay: Delay before search (seconds)

    Returns:
        LinkedIn profile URL or None
    """
    try:
        # Small delay to avoid rate limiting
        await asyncio.sleep(delay)

        # Search DuckDuckGo (note: ddgs library is sync, so we run in executor)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(DDGS().text(query, max_results=max_results))
        )

        # Extract LinkedIn URL from results
        linkedin_url = extract_linkedin_from_search_results(results)

        return linkedin_url

    except Exception as e:
        print(f"      ⚠️  Search error: {e}")
        return None


async def find_linkedin_multi_strategy(
    lead: Dict,
    delay: float = 0.5,
    max_strategies: int = 2
) -> Dict:
    """
    Find LinkedIn profile using multiple strategies (async).

    Strategies (in order):
    1. Check Anymailfinder response
    2. Parse website HTML
    3. DuckDuckGo: Full name + Job title + Company
    4. DuckDuckGo: Full name + Company + Location

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

    # Create search tasks for parallel execution
    search_tasks = []

    # STRATEGY 3: DuckDuckGo - Full name + Job title + Company
    if full_name and job_title and business_name and max_strategies >= 1:
        query = f'site:linkedin.com/in "{full_name}" "{job_title}" "{business_name}"'
        search_tasks.append(('strategy_1', query))

    # STRATEGY 4: DuckDuckGo - Full name + Company + Location
    if full_name and business_name and city and max_strategies >= 2:
        query = f'site:linkedin.com/in "{full_name}" "{business_name}" "{city}"'
        search_tasks.append(('strategy_2', query))

    # Execute searches in parallel
    if search_tasks:
        print(f"      🔍 Trying {len(search_tasks)} strategies in parallel...", end="", flush=True)

        tasks = [search_linkedin_duckduckgo(query, delay=delay) for _, query in search_tasks]
        results = await asyncio.gather(*tasks)

        # Check if any strategy found a result
        for (strategy_name, _), result in zip(search_tasks, results):
            if result:
                print(f" ✅ {strategy_name}")
                return {
                    "linkedin_url": result,
                    "linkedin_source": f"duckduckgo_{strategy_name}"
                }

        print(" ❌")

    # Not found
    return {
        "linkedin_url": None,
        "linkedin_source": None
    }


async def find_linkedin_for_single_lead(lead: Dict, delay: float = 0.5, max_strategies: int = 2) -> Dict:
    """
    Find LinkedIn profile for a single lead (async).

    Args:
        lead: Lead dictionary
        delay: Delay between searches
        max_strategies: Max DuckDuckGo strategies

    Returns:
        Lead with linkedin_url and linkedin_source added to decision_maker
    """
    decision_maker = lead.get('decision_maker', {})
    business_name = lead.get('name', 'Unknown')
    full_name = decision_maker.get('full_name') or 'Unknown'

    # Check Anymailfinder first
    anymailfinder_linkedin = decision_maker.get('linkedin_url')
    if anymailfinder_linkedin:
        lead['decision_maker']['linkedin_url'] = anymailfinder_linkedin
        lead['decision_maker']['linkedin_source'] = 'anymailfinder'
        return lead

    # Check HTML
    html_linkedin = extract_linkedin_from_html(lead.get('scraped_text', ''))
    if html_linkedin:
        lead['decision_maker']['linkedin_url'] = html_linkedin
        lead['decision_maker']['linkedin_source'] = 'website_html'
        return lead

    # Try DuckDuckGo
    if decision_maker.get('full_name') or decision_maker.get('email'):
        result = await find_linkedin_multi_strategy(lead, delay, max_strategies)
        lead['decision_maker']['linkedin_url'] = result['linkedin_url']
        lead['decision_maker']['linkedin_source'] = result['linkedin_source']
    else:
        lead['decision_maker']['linkedin_url'] = None
        lead['decision_maker']['linkedin_source'] = None

    return lead


async def find_linkedin_for_leads(
    leads: List[Dict],
    delay: float = 0.5,
    max_strategies: int = 2,
    max_concurrent: int = 5
) -> List[Dict]:
    """
    Find LinkedIn profiles for all leads (async parallel).

    Args:
        leads: List of enriched leads from anymailfinder
        delay: Delay between DuckDuckGo searches
        max_strategies: Max number of DuckDuckGo strategies per lead
        max_concurrent: Maximum concurrent lead processing

    Returns:
        List of leads with linkedin_url and linkedin_source added
    """
    stats = {
        "total": len(leads),
        "anymailfinder": 0,
        "website_html": 0,
        "duckduckgo": 0,
        "not_found": 0
    }

    print(f"\n{'='*70}")
    print(f"🔍 FINDING LINKEDIN PROFILES (ASYNC)")
    print(f"{'='*70}")
    print(f"Processing {len(leads)} leads in parallel...")
    print(f"Max concurrent: {max_concurrent}")
    print(f"DuckDuckGo delay: {delay}s between searches")
    print()

    enriched_leads = []

    # Process leads in batches to control concurrency
    for i in range(0, len(leads), max_concurrent):
        batch = leads[i:i+max_concurrent]

        # Create tasks for this batch
        tasks = [
            find_linkedin_for_single_lead(lead, delay, max_strategies)
            for lead in batch
        ]

        # Execute batch in parallel
        batch_results = await asyncio.gather(*tasks)

        # Update stats and collect results
        for j, lead in enumerate(batch_results, 1):
            global_index = i + j
            business_name = lead.get('name', 'Unknown')
            decision_maker = lead.get('decision_maker', {})
            full_name = decision_maker.get('full_name') or 'Unknown'

            linkedin_url = decision_maker.get('linkedin_url')
            linkedin_source = decision_maker.get('linkedin_source')

            if linkedin_source == 'anymailfinder':
                stats['anymailfinder'] += 1
                print(f"[{global_index}/{len(leads)}] {full_name} ({business_name}) ✅ anymailfinder")
            elif linkedin_source == 'website_html':
                stats['website_html'] += 1
                print(f"[{global_index}/{len(leads)}] {full_name} ({business_name}) ✅ website_html")
            elif linkedin_source and 'duckduckgo' in linkedin_source:
                stats['duckduckgo'] += 1
                print(f"[{global_index}/{len(leads)}] {full_name} ({business_name}) ✅ {linkedin_source}")
            else:
                stats['not_found'] += 1
                print(f"[{global_index}/{len(leads)}] {full_name} ({business_name}) ❌ Not found")

            enriched_leads.append(lead)

    # Summary
    total_found = stats['anymailfinder'] + stats['website_html'] + stats['duckduckgo']

    print(f"\n{'='*70}")
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
        description='Find LinkedIn profiles using multi-source discovery (async)'
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
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='Maximum concurrent lead processing (default: 5)'
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

    # Find LinkedIn profiles (async)
    enriched_leads = asyncio.run(find_linkedin_for_leads(
        leads,
        delay=args.delay,
        max_strategies=args.max_strategies,
        max_concurrent=args.max_concurrent
    ))

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
