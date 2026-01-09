#!/usr/bin/env python3
"""
Free Owner & LinkedIn Finder

Finds business owner name and LinkedIn profile without paid APIs:
1. Scrape company website (About page, Team page)
2. Search Google for owner + LinkedIn
3. Extract LinkedIn URL from results

Usage:
    python3 execution/find_owner_linkedin.py --business "First Class Electric" --website "https://firstclasselectricnj.com"
    python3 execution/find_owner_linkedin.py --file leads.json --output enriched_leads.json
"""

import os
import re
import sys
import json
import random
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Tuple
from urllib.parse import quote_plus, urlparse
import requests
from bs4 import BeautifulSoup

# User agents rotation for avoiding blocks
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

# Common owner-related keywords
OWNER_KEYWORDS = [
    'owner', 'founder', 'president', 'ceo', 'proprietor', 
    'principal', 'managing', 'director', 'about me', 'my story',
    'meet the owner', 'about us', 'our team', 'leadership'
]

# Name patterns (First Last, or First M. Last)
NAME_PATTERN = re.compile(
    r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
)

# LinkedIn URL pattern
LINKEDIN_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?'
)


def get_random_headers() -> Dict:
    """Get random headers to avoid blocking."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def clean_url(url: str) -> str:
    """Ensure URL has proper scheme."""
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def extract_names_from_text(text: str) -> List[str]:
    """Extract potential person names from text."""
    if not text:
        return []
    
    # Find all potential names
    names = NAME_PATTERN.findall(text)
    
    # Filter out common false positives
    false_positives = {
        'United States', 'New Jersey', 'New York', 'Contact Us', 
        'About Us', 'Our Team', 'Read More', 'Learn More',
        'Privacy Policy', 'Terms Service', 'All Rights', 'Cookie Policy',
        'Get Started', 'Free Estimate', 'Call Now', 'Book Now',
        'Monday Friday', 'Saturday Sunday', 'Open Hours',
        'Save Today', 'Save Now', 'Buy Now', 'Shop Now', 'Sign Up',
        'First Class', 'Good Tidings', 'Pipe Fitters', 'Reynolds Plumbing',
        'Russo Bros', 'Jason Klein', 'In Line', 'Rich Plumbing',
        'Schedule Now', 'Request Quote', 'Get Quote', 'View More',
        'Click Here', 'Submit Form', 'Send Message', 'Call Today',
        'Licensed Insured', 'Years Experience', 'Service Area',
        'Same Day', 'Next Day', 'Emergency Service', 'Quality Service'
    }
    
    filtered = [name for name in names if name not in false_positives]
    
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for name in filtered:
        if name.lower() not in seen:
            seen.add(name.lower())
            unique.append(name)
    
    return unique[:5]  # Return top 5 candidates


def scrape_website_for_owner(website: str, timeout: int = 15) -> Dict:
    """
    Scrape company website for owner information and social links.
    """
    result = {"name": None, "title": None, "source": None, "linkedin_url": None, "names_found": []}
    
    if not website:
        return result
    
    website = clean_url(website)
    parsed = urlparse(website)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    # Pages to check (in order of priority)
    pages_to_check = [
        website,  # Homepage first (often has social links in footer)
        f"{base_url}/about",
        f"{base_url}/about-us",
        f"{base_url}/team",
        f"{base_url}/our-team",
        f"{base_url}/meet-the-team",
        f"{base_url}/leadership",
    ]
    
    all_names = []
    
    for page_url in pages_to_check:
        try:
            response = requests.get(
                page_url,
                headers=get_random_headers(),
                timeout=timeout,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Look for LinkedIn links anywhere on the page
            if not result["linkedin_url"]:
                for link in soup.find_all('a', href=True):
                    href = link['href'].lower()
                    if 'linkedin.com/in/' in href or 'linkedin.com/company/' in href:
                        # Clean the URL
                        clean_link = link['href'].split('?')[0].rstrip('/')
                        result["linkedin_url"] = clean_link
                        print(f"      🔗 Found LinkedIn on site: {clean_link}")
            
            # 2. Look for owner names
            # Remove script and style elements for name extraction
            temp_soup = BeautifulSoup(response.text, 'html.parser')
            for element in temp_soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            text = temp_soup.get_text(separator=' ', strip=True)
            text_lower = text.lower()
            
            for keyword in OWNER_KEYWORDS:
                if keyword in text_lower:
                    pos = text_lower.find(keyword)
                    context = text[max(0, pos-100):pos+400]
                    names = extract_names_from_text(context)
                    
                    if names and not result["name"]:
                        result["name"] = names[0]
                        result["title"] = keyword.title()
                        result["source"] = page_url
                    
                    all_names.extend(names)
            
            # If we found both a name and a LinkedIn link, we can stop early
            if result["name"] and result["linkedin_url"]:
                break
                
        except Exception:
            continue
    
    result["names_found"] = list(set(all_names))[:5]
    return result


def search_google_for_linkedin(
    business_name: str,
    owner_name: Optional[str] = None,
    location: str = "",
    timeout: int = 10
) -> Dict:
    """
    Search Google for LinkedIn profile.
    
    Returns: {linkedin_url: str, owner_name: str, source: str}
    """
    result = {"linkedin_url": None, "owner_name": owner_name, "source": "google_search"}
    
    # Build search query
    if owner_name:
        query = f'"{owner_name}" "{business_name}" site:linkedin.com/in'
    else:
        query = f'"{business_name}" owner site:linkedin.com/in {location}'
    
    # Use Google search
    search_url = f"https://www.google.com/search?q={quote_plus(query)}&num=10"
    
    try:
        response = requests.get(
            search_url,
            headers=get_random_headers(),
            timeout=timeout
        )
        
        if response.status_code != 200:
            return result
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Google wraps links in /url?q=
            if '/url?q=' in href:
                # Extract actual URL
                start = href.find('/url?q=') + 7
                end = href.find('&', start)
                if end == -1:
                    end = len(href)
                actual_url = href[start:end]
                
                # Check if it's a LinkedIn profile URL
                linkedin_match = LINKEDIN_PATTERN.search(actual_url)
                if linkedin_match:
                    result["linkedin_url"] = actual_url.split('&')[0]
                    
                    # Try to extract name from link text
                    link_text = link.get_text(strip=True)
                    if link_text and '-' in link_text:
                        # LinkedIn titles are usually "Name - Title | LinkedIn"
                        parts = link_text.split('-')
                        if parts:
                            potential_name = parts[0].strip()
                            if len(potential_name.split()) >= 2:
                                result["owner_name"] = potential_name
                    
                    return result
            
            # Direct LinkedIn URL check
            elif 'linkedin.com/in/' in href:
                result["linkedin_url"] = href
                return result
        
    except Exception as e:
        pass
    
    return result


def search_duckduckgo_for_linkedin(
    business_name: str,
    owner_name: Optional[str] = None,
    location: str = "",
    timeout: int = 10
) -> Dict:
    """
    Search DuckDuckGo for LinkedIn profile (backup if Google blocks).
    
    Returns: {linkedin_url: str, owner_name: str, source: str}
    """
    result = {"linkedin_url": None, "owner_name": owner_name, "source": "duckduckgo_search"}
    
    # Build search query
    if owner_name:
        query = f'{owner_name} {business_name} linkedin'
    else:
        query = f'{business_name} owner linkedin {location}'
    
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    
    try:
        response = requests.get(
            search_url,
            headers=get_random_headers(),
            timeout=timeout
        )
        
        if response.status_code != 200:
            return result
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find result links
        for link in soup.find_all('a', class_='result__a'):
            href = link.get('href', '')
            
            linkedin_match = LINKEDIN_PATTERN.search(href)
            if linkedin_match:
                result["linkedin_url"] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
                
                # Extract name from title
                title = link.get_text(strip=True)
                if title and '-' in title:
                    parts = title.split('-')
                    potential_name = parts[0].strip()
                    if len(potential_name.split()) >= 2:
                        result["owner_name"] = potential_name
                
                return result
        
    except Exception as e:
        pass
    
    return result


def extract_location_from_address(address: str) -> str:
    """Extract city/state from address."""
    if not address:
        return ""
    
    # Try to extract NJ location
    parts = address.split(',')
    if len(parts) >= 2:
        # Usually format is "Street, City, State ZIP"
        city_state = parts[-2].strip() if len(parts) >= 2 else ""
        return city_state
    
    return ""


def find_owner_linkedin(
    business_name: str,
    website: Optional[str] = None,
    address: Optional[str] = None,
    scraped_text: Optional[str] = None
) -> Dict:
    """
    Full owner/LinkedIn discovery.

    1. Use pre-scraped text if available (Teleport optimization)
    2. Otherwise scrape website for owner name
    3. Search Google/DuckDuckGo for LinkedIn

    Returns:
    {
        "owner_name": str or None,
        "owner_first_name": str or None,
        "linkedin_url": str or None,
        "source": str,
        "names_found": list
    }
    """
    result = {
        "owner_name": None,
        "owner_first_name": None,
        "linkedin_url": None,
        "source": None,
        "names_found": []
    }

    # Step 1: Use pre-scraped text (Teleport) OR scrape website for owner name AND LinkedIn links
    owner_info = {"name": None, "linkedin_url": None, "names_found": []}

    if scraped_text:
        # Teleport optimization: Use pre-scraped text from N8N, skip network request
        print(f"      ⚡ Using pre-scraped text (Teleport)...")

        # Extract names from scraped text
        names = extract_names_from_text(scraped_text)
        if names:
            owner_info["name"] = names[0]
            owner_info["names_found"] = names
            owner_info["source"] = "teleport_scraped"

        # Also scan scraped_text for LinkedIn URLs (instant local extraction)
        linkedin_matches = LINKEDIN_PATTERN.findall(scraped_text)
        if linkedin_matches:
            # Found LinkedIn URL in scraped text - no network needed!
            linkedin_username = linkedin_matches[0]
            owner_info["linkedin_url"] = f"https://linkedin.com/in/{linkedin_username}"
            print(f"      ⚡ Found LinkedIn in scraped text: {owner_info['linkedin_url']}")
    elif website:
        print(f"      🌐 Scraping website for owner & links...")
        owner_info = scrape_website_for_owner(website)

    # Process owner_info (applies to both teleport and website scrape)
    if owner_info.get("name"):
        result["owner_name"] = owner_info["name"]
        result["owner_first_name"] = owner_info["name"].split()[0]
        result["source"] = owner_info.get("source", "website")
        print(f"      ✅ Found owner: {owner_info['name']}")

    if owner_info.get("linkedin_url"):
        result["linkedin_url"] = owner_info["linkedin_url"]
        result["source"] = result["source"] or "website"
        print(f"      ✅ Found LinkedIn link on website: {result['linkedin_url']}")

    if not result["owner_name"] and owner_info.get("names_found"):
        result["names_found"] = owner_info["names_found"]
        print(f"      ⚠️  Found potential names: {owner_info['names_found'][:3]}")
    
    # Step 2: Search for LinkedIn if not found on website
    if not result["linkedin_url"]:
        location = extract_location_from_address(address) if address else ""
        
        print(f"      🔍 Searching Google for LinkedIn...")
        linkedin_info = search_google_for_linkedin(
            business_name,
            owner_name=result.get("owner_name"),
            location=location
        )
        
        if linkedin_info.get("linkedin_url"):
            result["linkedin_url"] = linkedin_info["linkedin_url"]
            if linkedin_info.get("owner_name") and not result.get("owner_name"):
                result["owner_name"] = linkedin_info["owner_name"]
                result["owner_first_name"] = linkedin_info["owner_name"].split()[0]
            result["source"] = linkedin_info.get("source", "google_search")
            print(f"      ✅ Found LinkedIn: {result['linkedin_url'][:50]}...")
        else:
            # Fallback to DuckDuckGo
            print(f"      🔍 Trying DuckDuckGo...")
            linkedin_info = search_duckduckgo_for_linkedin(
                business_name,
                owner_name=result.get("owner_name"),
                location=location
            )
            
            if linkedin_info.get("linkedin_url"):
                result["linkedin_url"] = linkedin_info["linkedin_url"]
                if linkedin_info.get("owner_name") and not result.get("owner_name"):
                    result["owner_name"] = linkedin_info["owner_name"]
                    result["owner_first_name"] = linkedin_info["owner_name"].split()[0]
                result["source"] = "duckduckgo_search"
                print(f"      ✅ Found LinkedIn: {result['linkedin_url'][:50]}...")
            else:
                print(f"      ❌ No LinkedIn found")
    
    return result


def enrich_leads_file(input_file: str, output_file: str = None, concurrency: int = 10) -> Dict:
    """
    Enrich all leads in a JSON file with owner/LinkedIn info.
    Uses ThreadPoolExecutor for parallel LinkedIn searches.

    Args:
        input_file: Path to JSON file with leads
        output_file: Path to save enriched leads
        concurrency: Number of parallel workers (default 8)

    Returns summary statistics.
    """
    import threading

    # Load leads
    with open(input_file, 'r') as f:
        leads = json.load(f)

    print(f"\n🔍 Owner & LinkedIn Discovery (Parallel Mode)")
    print(f"   Total leads: {len(leads)}")
    print(f"   Concurrency: {concurrency} workers")
    print()

    stats = {
        "total": len(leads),
        "owners_found": 0,
        "linkedin_found": 0,
        "both_found": 0
    }
    stats_lock = threading.Lock()
    processed_count = [0]  # Use list for mutable counter in closure

    def process_single_lead(idx_lead):
        """Process a single lead - designed for thread pool execution."""
        idx, lead = idx_lead
        business_name = lead.get("name", "Unknown")
        website = lead.get("website")
        address = lead.get("address", "")
        scraped_text = lead.get("scraped_text")  # Teleport field from N8N

        print(f"[{idx}/{len(leads)}] {business_name[:40]}")

        result = find_owner_linkedin(business_name, website, address, scraped_text=scraped_text)

        # Add to lead
        lead["owner_name"] = result.get("owner_name")
        lead["owner_first_name"] = result.get("owner_first_name")
        lead["linkedin_url"] = result.get("linkedin_url")
        lead["owner_source"] = result.get("source")

        # Thread-safe stats update
        with stats_lock:
            if result.get("owner_name"):
                stats["owners_found"] += 1
            if result.get("linkedin_url"):
                stats["linkedin_found"] += 1
            if result.get("owner_name") and result.get("linkedin_url"):
                stats["both_found"] += 1
            processed_count[0] += 1

        return lead

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all leads for processing
        futures = {executor.submit(process_single_lead, (i, lead)): i
                   for i, lead in enumerate(leads, 1)}

        # Wait for all to complete (results are stored in-place in leads)
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
        print(f"\n💾 Saved enriched leads to: {output_file}")
    
    # Print summary
    print(f"\n📊 Enrichment Summary:")
    print(f"   Total processed: {stats['total']}")
    print(f"   Owners found: {stats['owners_found']}")
    print(f"   LinkedIn found: {stats['linkedin_found']}")
    print(f"   Both found: {stats['both_found']}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Find owner and LinkedIn info")
    parser.add_argument("--business", "-b", help="Business name to search")
    parser.add_argument("--website", "-w", help="Business website URL")
    parser.add_argument("--file", "-f", help="JSON file with leads to enrich")
    parser.add_argument("--output", "-o", help="Output file for enriched leads")
    parser.add_argument("--delay", "-d", type=float, default=2.0, help="Delay between searches (legacy, ignored)")
    parser.add_argument("--concurrency", "-c", type=int, default=10, help="Number of parallel workers (default: 10)")

    args = parser.parse_args()

    if args.business:
        # Single business lookup
        print(f"\n🔍 Finding owner/LinkedIn for: {args.business}")
        result = find_owner_linkedin(args.business, args.website)

        print(f"\n📋 Results:")
        print(f"   Owner Name: {result.get('owner_name', 'Not found')}")
        print(f"   First Name: {result.get('owner_first_name', 'Not found')}")
        print(f"   LinkedIn: {result.get('linkedin_url', 'Not found')}")
        print(f"   Source: {result.get('source', 'N/A')}")

        if result.get('names_found'):
            print(f"   Other names found: {result['names_found']}")

        print(f"\n📝 JSON:")
        print(json.dumps(result, indent=2))

    elif args.file:
        # File enrichment with parallel processing
        output = args.output or args.file.replace('.json', '_enriched.json')
        enrich_leads_file(args.file, output, concurrency=args.concurrency)
    else:
        parser.print_help()
        print("\n❌ Please provide --business or --file argument")
        sys.exit(1)


if __name__ == "__main__":
    main()
