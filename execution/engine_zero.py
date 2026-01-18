#!/usr/bin/env python3
"""
Engine Zero: High-Performance Lead Generation Engine

Features:
- SerpAPI Google Maps provider
- 50 parallel web scraping workers
- Auto-expand to 10-15 nearest cities
- Real-time progress hooks for frontend
- onError: continue (never fails on single site)

Usage:
    python3 execution/engine_zero.py --industry "Dentist" --location "Union, NJ" --target 200
"""

import os
import sys
import json
import re
import math
import hashlib
import argparse
import requests
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# Email Regex (from N8N Blueprint)
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+-]+@(?![a-zA-Z0-9.-]*\.(?:png|jpg|jpeg|gif|svg|webp|js|css|pdf))\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    re.IGNORECASE
)

# Junk email filter
JUNK_EMAILS = {
    'example@email.com', 'info@example.com', 'contact@example.com',
    'support@example.com', 'admin@example.com', 'test@test.com',
    'email@example.com', 'name@email.com', 'your@email.com'
}

# Regional expansions
REGION_EXPANSION = {
    "north new jersey": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack", "Fort Lee", "Hoboken", "Montclair", "West Orange"],
    "northern nj": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack", "Fort Lee", "Hoboken", "Montclair", "West Orange"],
    "north nj": ["Newark", "Jersey City", "Paterson", "Elizabeth", "Clifton", "Passaic", "Union City", "Bayonne", "East Orange", "Hackensack", "Fort Lee", "Hoboken", "Montclair", "West Orange"],
    "central new jersey": ["Edison", "Woodbridge", "New Brunswick", "Perth Amboy", "Sayreville", "East Brunswick", "Old Bridge", "Piscataway", "Plainfield", "South Brunswick", "North Brunswick", "Monroe"],
    "central nj": ["Edison", "Woodbridge", "New Brunswick", "Perth Amboy", "Sayreville", "East Brunswick", "Old Bridge", "Piscataway", "Plainfield", "South Brunswick", "North Brunswick", "Monroe"],
    "south new jersey": ["Camden", "Cherry Hill", "Trenton", "Atlantic City", "Vineland", "Gloucester", "Pennsauken", "Marlton", "Deptford", "Voorhees", "Evesham", "Mount Laurel"],
    "southern nj": ["Camden", "Cherry Hill", "Trenton", "Atlantic City", "Vineland", "Gloucester", "Pennsauken", "Marlton", "Deptford", "Voorhees", "Evesham", "Mount Laurel"],
}


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class EngineConfig:
    """Configuration for Engine Zero."""
    target_leads: int = 200
    max_cities: int = 15
    radius_miles: int = 20
    discovery_workers: int = 5
    scraping_workers: int = 50
    scrape_timeout: int = 10
    max_retries: int = 2
    hunt_id: Optional[str] = None
    add_log: Optional[Callable] = None
    update_status: Optional[Callable] = None


@dataclass
class Lead:
    """Output lead schema."""
    id: str
    name: str
    address: Optional[str] = None
    place_id: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    types: Optional[str] = None
    scraped_text: Optional[str] = None
    scraped_meta: Optional[str] = None
    search_query: Optional[str] = None
    scraped_at: Optional[str] = None
    icebreaker: Optional[str] = None
    # Enrichment fields (set by unified pipeline)
    owner_name: Optional[str] = None
    owner_first_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_source: Optional[str] = None
    email_verified: bool = False
    email_verification: Optional[dict] = None
    email_verification_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================================
# Providers
# ============================================================================

class GoogleMapsProvider(ABC):
    """Abstract base for Google Maps data providers."""

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class SerpAPIProvider(GoogleMapsProvider):
    """Primary provider: SerpAPI Google Maps endpoint."""

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Search Google Maps via SerpAPI."""
        results = []
        start = 0

        while len(results) < limit:
            params = {
                "engine": "google_maps",
                "q": query,
                "api_key": self.api_key,
                "type": "search",
                "start": start,
            }

            try:
                resp = requests.get(self.base_url, params=params, timeout=30)
                data = resp.json()

                if "error" in data:
                    break

                local_results = data.get("local_results", [])
                if not local_results:
                    break

                for item in local_results:
                    results.append({
                        "place_id": item.get("place_id"),
                        "name": item.get("title"),
                        "address": item.get("address"),
                        "phone": item.get("phone"),
                        "website": item.get("website"),
                        "rating": item.get("rating"),
                        "reviews": item.get("reviews"),
                        "type": item.get("type"),
                        "thumbnail": item.get("thumbnail"),
                    })

                    if len(results) >= limit:
                        break

                # SerpAPI pagination
                if len(local_results) < 20:
                    break
                start += 20

            except Exception as e:
                print(f"SerpAPI error: {e}")
                break

        return results[:limit]


# ============================================================================
# Engine Zero
# ============================================================================

class EngineZero:
    """
    High-performance lead generation engine.

    Features:
    - SerpAPI Google Maps sourcing
    - Parallel web scraping (50 concurrent workers)
    - Proximity-based city expansion
    - Real-time progress hooks
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.city_db = self._load_city_database()
        self.provider = self._select_provider()

        # Thread pools
        self.discovery_pool = ThreadPoolExecutor(max_workers=self.config.discovery_workers)
        self.scraping_pool = ThreadPoolExecutor(max_workers=self.config.scraping_workers)

        # Stats
        self.stats = {
            "cities_searched": 0,
            "raw_leads": 0,
            "sites_scraped": 0,
            "emails_found": 0
        }

    def _log(self, message: str, level: str = "INFO"):
        """Log via hook if configured, else print."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        print(formatted, flush=True)

        if self.config.add_log and self.config.hunt_id:
            try:
                self.config.add_log(self.config.hunt_id, message, level)
            except Exception:
                pass

    def _update_progress(self, stage: str, progress: int, message: str, **kwargs):
        """Update progress via hook if configured."""
        if self.config.update_status and self.config.hunt_id:
            try:
                # Import HuntStage enum from leadsnipe_api
                from leadsnipe_api import HuntStage
                self.config.update_status(
                    self.config.hunt_id,
                    HuntStage(stage),
                    progress,
                    message,
                    **kwargs
                )
            except Exception as e:
                print(f"Progress update error: {e}")

    def _load_city_database(self) -> Dict:
        """Load US cities database."""
        paths = [
            'execution/us_cities.json',
            'us_cities.json',
            os.path.join(os.path.dirname(__file__), 'us_cities.json')
        ]
        for path in paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        return {}

    def _select_provider(self) -> GoogleMapsProvider:
        """Initialize SerpAPI provider."""
        provider = SerpAPIProvider()
        if not provider.is_available():
            raise RuntimeError("SERPAPI_API_KEY not set. Add it to your .env file.")
        self._log("Using provider: SerpAPI")
        return provider

    # ========================================================================
    # Stage 0: Location Expansion
    # ========================================================================

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula for distance in miles."""
        R = 3959  # Earth radius in miles
        lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def expand_location(self, location: str) -> List[str]:
        """
        Expand location to list of nearby cities.

        Returns up to max_cities nearest cities within radius_miles.
        """
        location_lower = location.lower().strip()

        # Check regional shortcuts first
        for region, cities in REGION_EXPANSION.items():
            if region in location_lower:
                return [f"{c}, NJ" for c in cities[:self.config.max_cities]]

        # Parse City, State format
        if "," in location:
            parts = location.split(",")
            city = parts[0].strip()
            state = parts[1].strip().upper()

            # Look up in city database
            lookup_key = f"{city}, {state}"

            if lookup_key in self.city_db:
                target = self.city_db[lookup_key]

                # Find nearby cities
                distances = []
                for c_name, coords in self.city_db.items():
                    dist = self._calculate_distance(
                        target['lat'], target['lon'],
                        coords['lat'], coords['lon']
                    )
                    if dist <= self.config.radius_miles:
                        distances.append((c_name, dist))

                # Sort by distance
                distances.sort(key=lambda x: x[1])
                return [c[0] for c in distances[:self.config.max_cities]]

            # If city not in DB, try to find cities in same state
            state_cities = [c for c, coords in self.city_db.items() if coords['state'] == state]
            if state_cities:
                return state_cities[:self.config.max_cities]

        # Fallback: return original location
        return [location]

    # ========================================================================
    # Stage 1: Discovery
    # ========================================================================

    def _search_city(self, industry: str, city: str, limit: int) -> List[Dict]:
        """Search a single city."""
        query = f"{industry} in {city}"
        try:
            results = self.provider.search(query, limit=limit)
            return [(r, city, query) for r in results]
        except Exception as e:
            self._log(f"Search failed for {city}: {e}", "WARN")
            return []

    def discover_leads(self, industry: str, cities: List[str], target: int) -> List[Dict]:
        """
        Search Google Maps for businesses across all cities in parallel.
        """
        all_leads = []
        seen_ids = set()

        # Calculate limit per city
        limit_per_city = max(30, (target // len(cities)) + 20)

        # Parallel search across cities
        futures = []
        for city in cities:
            future = self.discovery_pool.submit(self._search_city, industry, city, limit_per_city)
            futures.append((future, city))

        for i, (future, city) in enumerate(futures):
            try:
                results = future.result(timeout=60)
                new_count = 0

                for item, search_city, query in results:
                    place_id = item.get('place_id') or self._generate_id(item)
                    if place_id not in seen_ids:
                        seen_ids.add(place_id)
                        item['_search_city'] = search_city
                        item['_search_query'] = query
                        all_leads.append(item)
                        new_count += 1

                self.stats['cities_searched'] += 1
                progress = 10 + int((i + 1) / len(futures) * 30)
                self._log(f"Searched {city}: +{new_count} leads (Total: {len(all_leads)})")
                self._update_progress("scraping", progress,
                                     f"Searching {city}... ({i+1}/{len(cities)} cities)",
                                     leads_found=len(all_leads))

                # Early exit if we have enough
                if len(all_leads) >= target * 1.5:
                    break

            except Exception as e:
                self._log(f"City search error: {e}", "WARN")

        self.stats['raw_leads'] = len(all_leads)
        return all_leads

    # ========================================================================
    # Stage 2: Web Scraping
    # ========================================================================

    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and validate URL."""
        if not url:
            return None
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')

    def _scrape_website(self, url: str) -> Dict:
        """
        Scrape single website for emails and metadata.
        Never raises - returns empty dict on failure.
        """
        if not url:
            return {"email": None, "scraped_text": "", "scraped_meta": ""}

        url = self._clean_url(url)
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        for attempt in range(self.config.max_retries):
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=self.config.scrape_timeout,
                    allow_redirects=True
                )

                if resp.status_code != 200:
                    continue

                html = resp.text
                soup = BeautifulSoup(html, 'html.parser')

                # Extract meta description
                meta_desc = ""
                meta_tag = soup.find('meta', attrs={'name': 'description'}) or \
                          soup.find('meta', attrs={'property': 'og:description'})
                if meta_tag:
                    meta_desc = meta_tag.get('content', '')

                # Extract text
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()
                scraped_text = soup.get_text(separator=' ', strip=True)

                # Extract emails
                emails = EMAIL_REGEX.findall(html)

                # Also check mailto: links
                mailto_matches = re.findall(
                    r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    html, re.I
                )
                emails.extend(mailto_matches)

                # Filter junk
                valid_emails = []
                seen = set()
                for e in emails:
                    e_low = e.lower()
                    if e_low not in JUNK_EMAILS and e_low not in seen:
                        valid_emails.append(e)
                        seen.add(e_low)

                return {
                    "email": valid_emails[0] if valid_emails else None,
                    "scraped_text": scraped_text[:2000],
                    "scraped_meta": meta_desc[:500]
                }

            except Exception:
                # Try with different user agent
                headers = {"User-Agent": random.choice(USER_AGENTS)}
                continue

        # Always return valid dict (onError: continue)
        return {"email": None, "scraped_text": "", "scraped_meta": ""}

    def _generate_id(self, item: Dict) -> str:
        """Generate unique ID from name + address."""
        unique_str = f"{item.get('name', '')}|{item.get('address', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def scrape_websites_parallel(self, raw_leads: List[Dict]) -> List[Lead]:
        """
        Scrape all websites in parallel with 50 workers.
        """
        self._log(f"Swarming {len(raw_leads)} websites ({self.config.scraping_workers} parallel workers)...")

        leads = []
        futures = {}

        # Submit all scrape jobs
        for item in raw_leads:
            future = self.scraping_pool.submit(self._scrape_website, item.get('website'))
            futures[future] = item

        # Process as completed
        completed = 0
        for future in as_completed(futures):
            item = futures[future]
            completed += 1

            try:
                enrichment = future.result()

                lead = Lead(
                    id=item.get('place_id') or self._generate_id(item),
                    name=item.get('name', item.get('title', '')),
                    address=item.get('address'),
                    place_id=item.get('place_id'),
                    phone=item.get('phone'),
                    website=item.get('website'),
                    email=enrichment.get('email'),
                    rating=item.get('rating'),
                    user_ratings_total=item.get('reviews'),
                    types=item.get('type'),
                    scraped_text=enrichment.get('scraped_text'),
                    scraped_meta=enrichment.get('scraped_meta'),
                    search_query=item.get('_search_query'),
                    scraped_at=datetime.now().isoformat()
                )
                leads.append(lead)

                if enrichment.get('email'):
                    self.stats['emails_found'] += 1

            except Exception as e:
                # onError: continue - still add lead without email
                lead = Lead(
                    id=item.get('place_id') or self._generate_id(item),
                    name=item.get('name', item.get('title', '')),
                    address=item.get('address'),
                    place_id=item.get('place_id'),
                    phone=item.get('phone'),
                    website=item.get('website'),
                    rating=item.get('rating'),
                    user_ratings_total=item.get('reviews'),
                    types=item.get('type'),
                    scraped_at=datetime.now().isoformat()
                )
                leads.append(lead)

            # Progress updates every 10 leads
            if completed % 10 == 0 or completed == len(raw_leads):
                progress = 40 + int((completed / len(raw_leads)) * 35)
                self._log(f"Scraped {completed}/{len(raw_leads)} sites ({self.stats['emails_found']} emails)")
                self._update_progress("getting_emails", progress,
                                     f"Scraping websites... ({completed}/{len(raw_leads)})",
                                     leads_found=len(leads),
                                     emails_found=self.stats['emails_found'])

        self.stats['sites_scraped'] = completed
        return leads

    # ========================================================================
    # Stage 3: Finalization
    # ========================================================================

    def deduplicate(self, leads: List[Lead]) -> List[Lead]:
        """Remove duplicates based on place_id or name+address hash."""
        seen = set()
        unique = []

        for lead in leads:
            key = lead.place_id or lead.id
            if key not in seen:
                seen.add(key)
                unique.append(lead)

        return unique

    # ========================================================================
    # Main Entry Point
    # ========================================================================

    def run(self, industry: str, location: str, target: Optional[int] = None) -> List[Lead]:
        """
        Execute full lead generation pipeline.

        Args:
            industry: Business type (e.g., "Dentist", "HVAC")
            location: Target location (e.g., "Union, NJ")
            target: Target lead count (default: config.target_leads)

        Returns:
            List of Lead objects
        """
        target = target or self.config.target_leads
        start_time = datetime.now()

        self._log("=" * 60)
        self._log("  ENGINE ZERO - High Performance Lead Generation")
        self._log("=" * 60)
        self._log(f"Industry: {industry}")
        self._log(f"Location: {location}")
        self._log(f"Target: {target} leads")
        self._log(f"Workers: {self.config.scraping_workers} parallel")

        # Stage 0: Expansion (5-10%)
        self._update_progress("queued", 5, "Expanding location...")
        cities = self.expand_location(location)
        self._log(f"Expanded to {len(cities)} cities: {cities[:5]}{'...' if len(cities) > 5 else ''}")
        self._update_progress("scraping", 10, f"Expanded to {len(cities)} nearby cities")

        # Stage 1: Discovery (10-40%)
        self._log(f"Searching Google Maps for '{industry}'...")
        raw_leads = self.discover_leads(industry, cities, target)

        if not raw_leads:
            self._log("No leads found!", "ERROR")
            self._update_progress("failed", 0, "No leads found")
            return []

        self._log(f"Discovery complete: {len(raw_leads)} raw leads")
        self._update_progress("scraping", 40, f"Found {len(raw_leads)} businesses",
                            leads_found=len(raw_leads))

        # Stage 2: Scraping (40-75%)
        enriched = self.scrape_websites_parallel(raw_leads)

        # Stage 3: Deduplicate (75-90%)
        self._update_progress("getting_emails", 85, "Deduplicating...")
        final = self.deduplicate(enriched)[:target]

        # Complete
        duration = (datetime.now() - start_time).total_seconds()
        emails_found = sum(1 for l in final if l.email)

        self._log("=" * 60)
        self._log(f"COMPLETE: {len(final)} leads in {duration:.1f}s")
        self._log(f"Email coverage: {emails_found}/{len(final)} ({100*emails_found//len(final) if final else 0}%)")
        self._log("=" * 60)

        self._update_progress("completed", 100,
                            f"Hunt complete! {len(final)} leads, {emails_found} emails",
                            leads_found=len(final),
                            emails_found=emails_found)

        return final

    def shutdown(self):
        """Clean up thread pools."""
        self.discovery_pool.shutdown(wait=False)
        self.scraping_pool.shutdown(wait=False)


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Engine Zero: High-Performance Lead Generation")
    parser.add_argument("--industry", "-i", required=True, help="Business type (e.g., Dentist)")
    parser.add_argument("--location", "-l", required=True, help="Target location (e.g., Union, NJ)")
    parser.add_argument("--target", "-t", type=int, default=200, help="Target lead count")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--workers", "-w", type=int, default=50, help="Parallel scraping workers")

    args = parser.parse_args()

    config = EngineConfig(
        target_leads=args.target,
        scraping_workers=args.workers
    )

    engine = EngineZero(config)

    try:
        leads = engine.run(args.industry, args.location, args.target)

        # Save output
        output_path = args.output or f".tmp/engine_zero_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(output_path) or ".tmp", exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump([l.to_dict() for l in leads], f, indent=2)

        print(f"\nSaved {len(leads)} leads to: {output_path}")

    finally:
        engine.shutdown()


if __name__ == "__main__":
    main()
