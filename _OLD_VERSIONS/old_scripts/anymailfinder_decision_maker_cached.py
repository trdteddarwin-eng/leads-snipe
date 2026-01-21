#!/usr/bin/env python3
"""
Anymailfinder Decision Maker Email Finder (CACHED + ASYNC)

Combines Redis caching with async processing for maximum performance:
- Cache hit: <1ms response time
- Cache miss: 15s timeout (vs 180s before)
- Parallel processing: 10 concurrent requests

Usage:
    python3 execution/anymailfinder_decision_maker_cached.py \
      --input .tmp/leads.json \
      --output .tmp/leads_with_owners.json \
      --category ceo

Cost: 2 credits per valid email found (~$0.04/email), but only for cache misses
Performance: Near-instant for cached results, 10x faster for new requests
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
from cache_redis import get_cache

# Load environment variables
load_dotenv()

# API Configuration
ANYMAILFINDER_API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
ANYMAILFINDER_API_URL = "https://api.anymailfinder.com/v5.1/find-email/decision-maker"

if not ANYMAILFINDER_API_KEY:
    print("❌ ANYMAILFINDER_API_KEY not found in .env")
    sys.exit(1)


def extract_domain(website_url: str) -> Optional[str]:
    """Extract clean domain from website URL."""
    if not website_url:
        return None

    if not website_url.startswith(('http://', 'https://')):
        website_url = 'https://' + website_url

    try:
        parsed = urlparse(website_url)
        domain = parsed.netloc or parsed.path

        if domain.startswith('www.'):
            domain = domain[4:]

        domain = domain.rstrip('/')

        return domain if domain else None
    except Exception as e:
        return None


async def find_decision_maker_email(
    session: aiohttp.ClientSession,
    domain: str,
    category: str = "ceo",
    timeout: int = 15,
    use_cache: bool = True
) -> Optional[Dict]:
    """
    Find decision maker email with caching.

    Args:
        session: aiohttp session
        domain: Company domain
        category: Decision maker category
        timeout: Request timeout
        use_cache: Whether to use cache

    Returns:
        Decision maker dict or None
    """
    cache = get_cache() if use_cache else None

    # Check cache first
    if cache and cache.enabled:
        cached = cache.get_decision_maker(domain)
        if cached:
            print(f"   ⚡ Cache HIT: {domain}")
            return cached

    # Cache miss - call API
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

                email = data.get('email') or data.get('valid_email')
                status = data.get('email_status')

                if email and status == 'valid':
                    result = {
                        "email": email,
                        "full_name": data.get('person_full_name'),
                        "job_title": data.get('person_job_title'),
                        "linkedin_url": data.get('person_linkedin_url'),
                        "status": status
                    }

                    # Cache the result
                    if cache and cache.enabled:
                        cache.set_decision_maker(domain, result)

                    return result

            return None

    except asyncio.TimeoutError:
        return None
    except Exception as e:
        return None


async def enrich_single_lead(
    session: aiohttp.ClientSession,
    lead: Dict,
    category: str = "ceo",
    timeout: int = 15,
    use_cache: bool = True
) -> Dict:
    """Enrich a single lead with caching."""
    business_email = lead.get('email')
    website = lead.get('website')

    if not website:
        lead['decision_maker'] = {
            "email": business_email,
            "full_name": None,
            "job_title": "Business Contact",
            "linkedin_url": None,
            "status": "no_website"
        }
        lead['anymailfinder_credits_used'] = 0
        lead['cache_hit'] = False
        return lead

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
        lead['cache_hit'] = False
        return lead

    # Find decision maker (with caching)
    decision_maker = await find_decision_maker_email(
        session, domain, category, timeout, use_cache
    )

    if decision_maker:
        # Check if it was a cache hit
        cache = get_cache() if use_cache else None
        cache_hit = cache and cache.enabled and cache.get_decision_maker(domain) is not None

        lead['decision_maker'] = decision_maker
        lead['anymailfinder_credits_used'] = 0 if cache_hit else 2
        lead['cache_hit'] = cache_hit
    else:
        lead['decision_maker'] = {
            "email": business_email,
            "full_name": None,
            "job_title": "Business Contact",
            "linkedin_url": None,
            "status": "not_found"
        }
        lead['anymailfinder_credits_used'] = 0
        lead['cache_hit'] = False

    return lead


async def enrich_leads_with_decision_makers(
    leads: List[Dict],
    category: str = "ceo",
    timeout: int = 15,
    max_concurrent: int = 10,
    use_cache: bool = True
) -> List[Dict]:
    """Enrich leads with caching + async."""
    stats = {
        "total": len(leads),
        "found": 0,
        "no_website": 0,
        "not_found": 0,
        "credits_used": 0,
        "cache_hits": 0,
        "cache_misses": 0
    }

    print(f"\n{'='*70}")
    print(f"🔍 FINDING DECISION MAKERS (CACHED + ASYNC)")
    print(f"{'='*70}")
    print(f"Processing {len(leads)} leads in parallel...")
    print(f"Max concurrent: {max_concurrent}")
    print(f"Cache enabled: {use_cache}")
    print(f"Category: {category}")
    print()

    connector = aiohttp.TCPConnector(limit=max_concurrent)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            enrich_single_lead(session, lead, category, timeout, use_cache)
            for lead in leads
        ]

        enriched_leads = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            enriched_lead = await task
            enriched_leads.append(enriched_lead)

            # Update stats
            dm = enriched_lead['decision_maker']
            cache_hit = enriched_lead.get('cache_hit', False)

            if cache_hit:
                stats['cache_hits'] += 1

            if dm['status'] == 'valid':
                stats['found'] += 1
                stats['credits_used'] += enriched_lead['anymailfinder_credits_used']
                if not cache_hit:
                    stats['cache_misses'] += 1

                cache_emoji = "⚡" if cache_hit else "🔄"
                print(f"[{i}/{len(leads)}] {enriched_lead.get('name', 'Unknown')} ✅ {dm['email']} {cache_emoji}")
            elif dm['status'] in ['no_website', 'invalid_domain']:
                stats['no_website'] += 1
                print(f"[{i}/{len(leads)}] {enriched_lead.get('name', 'Unknown')} ❌ No website")
            else:
                stats['not_found'] += 1
                if not cache_hit:
                    stats['cache_misses'] += 1
                print(f"[{i}/{len(leads)}] {enriched_lead.get('name', 'Unknown')} ⚠️  Not found")

    # Print summary
    print(f"\n{'='*70}")
    print(f"✅ ENRICHMENT COMPLETE")
    print(f"{'='*70}")
    print(f"Total leads: {stats['total']}")
    print(f"✅ Decision makers found: {stats['found']}/{stats['total']} ({100*stats['found']//max(stats['total'],1)}%)")
    print(f"❌ No website: {stats['no_website']}")
    print(f"⚠️  Not found: {stats['not_found']}")
    print()
    print(f"⚡ CACHE PERFORMANCE:")
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Cache misses: {stats['cache_misses']}")
    if stats['cache_hits'] + stats['cache_misses'] > 0:
        hit_rate = 100 * stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses'])
        print(f"   Hit rate: {hit_rate:.1f}%")
    print()
    print(f"💰 Credits used: {stats['credits_used']} (~${stats['credits_used']*0.02:.2f})")
    print()

    return enriched_leads


def main():
    parser = argparse.ArgumentParser(
        description='Find decision maker emails with caching + async'
    )
    parser.add_argument('--input', '-i', required=True, help='Input JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output JSON file')
    parser.add_argument('--category', '-c', default='ceo', help='Decision maker category')
    parser.add_argument('--timeout', '-t', type=int, default=15, help='API timeout')
    parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent requests')
    parser.add_argument('--no-cache', action='store_true', help='Disable cache')

    args = parser.parse_args()

    # Load leads
    try:
        with open(args.input, 'r') as f:
            leads = json.load(f)

        if not isinstance(leads, list):
            print(f"❌ Error: Input must be JSON array")
            sys.exit(1)

        print(f"📂 Loaded {len(leads)} leads from {args.input}")

    except FileNotFoundError:
        print(f"❌ Error: File '{args.input}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON: {e}")
        sys.exit(1)

    # Enrich leads
    enriched_leads = asyncio.run(enrich_leads_with_decision_makers(
        leads,
        category=args.category,
        timeout=args.timeout,
        max_concurrent=args.max_concurrent,
        use_cache=not args.no_cache
    ))

    # Save
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
