#!/usr/bin/env python3
"""
Unified LinkedIn Finder for LeadSnipe

FREE multi-strategy LinkedIn discovery with parallel processing:
1. HTML extraction (instant - from scraped text)
2. DuckDuckGo search (free, unlimited)
3. Google HTML search (fallback, conservative)

NO PAID APIS - All methods are free.

Usage:
    from linkedin_finder_unified import LinkedInFinder

    finder = LinkedInFinder(workers=10)
    leads = finder.find_batch(leads, progress_callback=my_callback)
"""

import re
import json
import threading
from typing import Optional, Dict, List, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus, urlparse
from dataclasses import dataclass
import requests

from rate_limiter import RateLimiter, get_limiter


# LinkedIn URL patterns
LINKEDIN_PROFILE_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?',
    re.IGNORECASE
)

LINKEDIN_COMPANY_PATTERN = re.compile(
    r'https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)/?',
    re.IGNORECASE
)

# Name extraction pattern (First Last)
NAME_PATTERN = re.compile(
    r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
)

# False positive names to filter
FALSE_POSITIVE_NAMES = {
    'United States', 'New Jersey', 'New York', 'Contact Us',
    'About Us', 'Our Team', 'Read More', 'Learn More',
    'Privacy Policy', 'Terms Service', 'All Rights', 'Cookie Policy',
    'Get Started', 'Free Estimate', 'Call Now', 'Book Now',
    'Monday Friday', 'Saturday Sunday', 'Open Hours',
    'Save Today', 'Save Now', 'Buy Now', 'Shop Now', 'Sign Up',
    'Schedule Now', 'Request Quote', 'Get Quote', 'View More',
    'Click Here', 'Submit Form', 'Send Message', 'Call Today',
    'Licensed Insured', 'Years Experience', 'Service Area',
    'Same Day', 'Next Day', 'Emergency Service', 'Quality Service',
    'First Class', 'Good Tidings', 'Rich Plumbing', 'In Line',
}


@dataclass
class LinkedInResult:
    """Result of LinkedIn discovery for a single lead."""
    linkedin_url: Optional[str] = None
    owner_name: Optional[str] = None
    owner_first_name: Optional[str] = None
    source: Optional[str] = None
    names_found: List[str] = None

    def __post_init__(self):
        if self.names_found is None:
            self.names_found = []
        if self.owner_name and not self.owner_first_name:
            self.owner_first_name = self.owner_name.split()[0]

    def to_dict(self) -> Dict:
        return {
            "linkedin_url": self.linkedin_url,
            "owner_name": self.owner_name,
            "owner_first_name": self.owner_first_name,
            "source": self.source,
            "names_found": self.names_found,
        }


class LinkedInFinder:
    """
    FREE multi-strategy LinkedIn discovery.

    Strategies (in order, stops on first success):
    1. HTML extraction - From scraped website text (instant, no network)
    2. DuckDuckGo search - Free search engine
    3. Google HTML search - Fallback search (more aggressive rate limiting)
    """

    def __init__(self, workers: int = 10, verbose: bool = True):
        """
        Initialize LinkedIn finder.

        Args:
            workers: Number of parallel workers for batch processing
            verbose: Whether to print progress messages
        """
        self.workers = workers
        self.verbose = verbose
        self.limiter = get_limiter("duckduckgo")
        self.google_limiter = get_limiter("google")

        # Stats
        self.stats = {
            "total": 0,
            "linkedin_found": 0,
            "owner_found": 0,
            "by_source": {
                "html_extract": 0,
                "duckduckgo": 0,
                "google": 0,
            }
        }
        self._stats_lock = threading.Lock()

    def _log(self, message: str):
        """Print if verbose mode enabled."""
        if self.verbose:
            print(message, flush=True)

    # =========================================================================
    # Strategy 1: HTML Extraction (instant)
    # =========================================================================

    def _extract_from_html(self, text: str) -> Optional[str]:
        """
        Extract LinkedIn URL from HTML/text content.
        This is instant - no network request needed.
        """
        if not text:
            return None

        # Look for LinkedIn profile URLs
        matches = LINKEDIN_PROFILE_PATTERN.findall(text)
        if matches:
            username = matches[0]
            # Filter out common false positives
            if username.lower() not in {'share', 'company', 'jobs', 'feed', 'in'}:
                return f"https://linkedin.com/in/{username}"

        # Also check for company pages (might have owner info)
        company_matches = LINKEDIN_COMPANY_PATTERN.findall(text)
        if company_matches:
            # Company pages are less useful but still a signal
            return f"https://linkedin.com/company/{company_matches[0]}"

        return None

    def _extract_names_from_text(self, text: str) -> List[str]:
        """Extract potential person names from text."""
        if not text:
            return []

        names = NAME_PATTERN.findall(text)
        filtered = [n for n in names if n not in FALSE_POSITIVE_NAMES]

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for name in filtered:
            if name.lower() not in seen:
                seen.add(name.lower())
                unique.append(name)

        return unique[:5]

    # =========================================================================
    # Strategy 2: DuckDuckGo Search (free)
    # =========================================================================

    def _search_duckduckgo(self, business_name: str, owner_name: Optional[str] = None,
                           location: str = "") -> Dict:
        """
        Search DuckDuckGo for LinkedIn profile.
        Uses HTML endpoint (no API needed, unlimited).
        """
        result = {"linkedin_url": None, "owner_name": owner_name}

        # Build search query
        if owner_name:
            query = f'{owner_name} {business_name} linkedin'
        else:
            query = f'{business_name} owner linkedin {location}'

        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        try:
            headers = self.limiter.acquire("duckduckgo.com")
            response = requests.get(search_url, headers=headers, timeout=15)
            self.limiter.report_response("duckduckgo.com", response.status_code)

            if response.status_code != 200:
                return result

            # Parse results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find result links
            for link in soup.find_all('a', class_='result__a'):
                href = link.get('href', '')

                linkedin_match = LINKEDIN_PROFILE_PATTERN.search(href)
                if linkedin_match:
                    username = linkedin_match.group(1)
                    if username.lower() not in {'share', 'company', 'jobs', 'feed', 'in'}:
                        result["linkedin_url"] = f"https://linkedin.com/in/{username}"

                        # Extract name from title
                        title = link.get_text(strip=True)
                        if title and '-' in title:
                            parts = title.split('-')
                            potential_name = parts[0].strip()
                            if len(potential_name.split()) >= 2:
                                result["owner_name"] = potential_name

                        return result

        except Exception as e:
            self._log(f"      DuckDuckGo error: {e}")

        return result

    # =========================================================================
    # Strategy 3: Google HTML Search (fallback)
    # =========================================================================

    def _search_google(self, business_name: str, owner_name: Optional[str] = None,
                       location: str = "") -> Dict:
        """
        Search Google for LinkedIn profile.
        More aggressive rate limiting to avoid blocks.
        """
        result = {"linkedin_url": None, "owner_name": owner_name}

        # Check if Google appears blocked
        if self.google_limiter.is_domain_blocked("google.com"):
            self._log("      Google appears blocked, skipping")
            return result

        # Build search query with site restriction
        if owner_name:
            query = f'"{owner_name}" "{business_name}" site:linkedin.com/in'
        else:
            query = f'"{business_name}" owner site:linkedin.com/in {location}'

        search_url = f"https://www.google.com/search?q={quote_plus(query)}&num=10"

        try:
            headers = self.google_limiter.acquire("google.com")
            # Add referer for Google
            headers["Referer"] = "https://www.google.com/"

            response = requests.get(search_url, headers=headers, timeout=15)
            self.google_limiter.report_response("google.com", response.status_code)

            if response.status_code != 200:
                return result

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Google wraps links in /url?q=
                if '/url?q=' in href:
                    start = href.find('/url?q=') + 7
                    end = href.find('&', start)
                    if end == -1:
                        end = len(href)
                    actual_url = href[start:end]

                    linkedin_match = LINKEDIN_PROFILE_PATTERN.search(actual_url)
                    if linkedin_match:
                        username = linkedin_match.group(1)
                        if username.lower() not in {'share', 'company', 'jobs', 'feed', 'in'}:
                            result["linkedin_url"] = f"https://linkedin.com/in/{username}"

                            # Try to extract name from link text
                            link_text = link.get_text(strip=True)
                            if link_text and '-' in link_text:
                                parts = link_text.split('-')
                                potential_name = parts[0].strip()
                                if len(potential_name.split()) >= 2:
                                    result["owner_name"] = potential_name

                            return result

                # Direct LinkedIn URL check
                elif 'linkedin.com/in/' in href:
                    linkedin_match = LINKEDIN_PROFILE_PATTERN.search(href)
                    if linkedin_match:
                        result["linkedin_url"] = f"https://linkedin.com/in/{linkedin_match.group(1)}"
                        return result

        except Exception as e:
            self._log(f"      Google error: {e}")

        return result

    # =========================================================================
    # Main Discovery Method
    # =========================================================================

    def find_single(self, business_name: str, website: Optional[str] = None,
                    address: Optional[str] = None, scraped_text: Optional[str] = None) -> LinkedInResult:
        """
        Find LinkedIn for a single business using all FREE strategies.

        Args:
            business_name: Name of the business
            website: Business website URL (optional, not used for scraping)
            address: Business address (used for location context)
            scraped_text: Pre-scraped website text (from Engine Zero)

        Returns:
            LinkedInResult with linkedin_url, owner_name, source
        """
        result = LinkedInResult()

        # Extract location from address
        location = ""
        if address:
            parts = address.split(',')
            if len(parts) >= 2:
                location = parts[-2].strip()

        # Strategy 1: Extract from scraped text (instant, no network)
        if scraped_text:
            linkedin_url = self._extract_from_html(scraped_text)
            if linkedin_url:
                result.linkedin_url = linkedin_url
                result.source = "html_extract"
                self._log(f"      [HTML] Found: {linkedin_url}")

            # Also extract potential owner names
            names = self._extract_names_from_text(scraped_text)
            if names:
                result.names_found = names
                if not result.owner_name:
                    result.owner_name = names[0]
                    result.owner_first_name = names[0].split()[0]

        # Strategy 2: DuckDuckGo search (if no LinkedIn yet)
        if not result.linkedin_url:
            self._log(f"      [DDG] Searching...")
            ddg_result = self._search_duckduckgo(business_name, result.owner_name, location)

            if ddg_result.get("linkedin_url"):
                result.linkedin_url = ddg_result["linkedin_url"]
                result.source = "duckduckgo"
                self._log(f"      [DDG] Found: {result.linkedin_url}")

                if ddg_result.get("owner_name") and not result.owner_name:
                    result.owner_name = ddg_result["owner_name"]
                    result.owner_first_name = ddg_result["owner_name"].split()[0]

        # Strategy 3: Google search (fallback, conservative)
        if not result.linkedin_url:
            self._log(f"      [Google] Fallback search...")
            google_result = self._search_google(business_name, result.owner_name, location)

            if google_result.get("linkedin_url"):
                result.linkedin_url = google_result["linkedin_url"]
                result.source = "google"
                self._log(f"      [Google] Found: {result.linkedin_url}")

                if google_result.get("owner_name") and not result.owner_name:
                    result.owner_name = google_result["owner_name"]
                    result.owner_first_name = google_result["owner_name"].split()[0]

        if not result.linkedin_url:
            self._log(f"      [!] No LinkedIn found")

        return result

    # =========================================================================
    # Batch Processing
    # =========================================================================

    def find_batch(self, leads: List[Dict], progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Find LinkedIn for all leads in parallel using FREE methods only.

        Args:
            leads: List of lead dicts with at least 'name' field
            progress_callback: Optional callback(completed, total) for progress updates

        Returns:
            Same leads list with linkedin_url, owner_name fields added
        """
        total = len(leads)
        self._log(f"\n[LinkedIn Finder] Processing {total} leads ({self.workers} workers)")

        completed = [0]  # Mutable counter for thread safety

        def process_single(idx_lead):
            idx, lead = idx_lead
            business_name = lead.get("name", "Unknown")
            website = lead.get("website")
            address = lead.get("address", "")
            scraped_text = lead.get("scraped_text")

            self._log(f"[{idx}/{total}] {business_name[:40]}")

            result = self.find_single(business_name, website, address, scraped_text)

            # Update lead in place
            lead["linkedin_url"] = result.linkedin_url
            lead["owner_name"] = result.owner_name or lead.get("owner_name")
            lead["owner_first_name"] = result.owner_first_name or lead.get("owner_first_name")
            lead["linkedin_source"] = result.source

            # Thread-safe stats update
            with self._stats_lock:
                self.stats["total"] += 1
                if result.linkedin_url:
                    self.stats["linkedin_found"] += 1
                    if result.source:
                        self.stats["by_source"][result.source] = \
                            self.stats["by_source"].get(result.source, 0) + 1
                if result.owner_name:
                    self.stats["owner_found"] += 1

                completed[0] += 1

            if progress_callback:
                progress_callback(completed[0], total)

            return lead

        # Parallel processing
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(process_single, (i, lead)): i
                       for i, lead in enumerate(leads, 1)}

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    idx = futures[future]
                    self._log(f"      Error processing lead {idx}: {e}")

        # Print summary
        self._log(f"\n[LinkedIn Finder] Summary:")
        self._log(f"   Total processed: {self.stats['total']}")
        self._log(f"   LinkedIn found: {self.stats['linkedin_found']} ({100*self.stats['linkedin_found']//max(1,total)}%)")
        self._log(f"   Owners found: {self.stats['owner_found']}")
        self._log(f"   By source: {self.stats['by_source']}")

        return leads

    def get_stats(self) -> Dict:
        """Get discovery statistics."""
        with self._stats_lock:
            return dict(self.stats)


# Convenience function
def find_linkedin_batch(leads: List[Dict], workers: int = 10,
                        progress_callback: Optional[Callable] = None) -> List[Dict]:
    """
    Find LinkedIn for all leads using FREE methods.

    Args:
        leads: List of lead dicts
        workers: Number of parallel workers
        progress_callback: Optional callback(completed, total)

    Returns:
        Leads with linkedin_url, owner_name fields added
    """
    finder = LinkedInFinder(workers=workers)
    return finder.find_batch(leads, progress_callback)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn Finder")
    parser.add_argument("--business", "-b", help="Business name")
    parser.add_argument("--file", "-f", help="JSON file with leads")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--workers", "-w", type=int, default=10, help="Parallel workers")

    args = parser.parse_args()

    if args.business:
        finder = LinkedInFinder(workers=1)
        result = finder.find_single(args.business)
        print(json.dumps(result.to_dict(), indent=2))

    elif args.file:
        with open(args.file, 'r') as f:
            leads = json.load(f)

        finder = LinkedInFinder(workers=args.workers)
        enriched = finder.find_batch(leads)

        output = args.output or args.file.replace('.json', '_linkedin.json')
        with open(output, 'w') as f:
            json.dump(enriched, f, indent=2)

        print(f"\nSaved to: {output}")

    else:
        parser.print_help()
