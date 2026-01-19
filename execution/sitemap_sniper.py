"""
Sitemap Sniper - Stealth Hybrid Lead Engine

Discovers and scrapes contact/team pages from XML sitemaps.
Extracts emails and staff names for lead enrichment.

Requirements covered:
- SITEMAP-01: Sitemap URL discovery
- SITEMAP-02: Recursive sitemap parsing
- SITEMAP-03: Contact page identification
- SITEMAP-04: Email extraction from pages
- SITEMAP-05: Staff name extraction
"""

import asyncio
import re
import json
import gzip
from io import BytesIO
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from urllib.parse import urlparse, urljoin

import httpx
from lxml import etree
from bs4 import BeautifulSoup


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class StaffMember:
    """Extracted staff member info."""
    name: str
    title: Optional[str] = None
    email: Optional[str] = None


@dataclass
class SitemapResult:
    """Result of sitemap sniping for a domain."""
    domain: str
    sitemap_urls: List[str] = field(default_factory=list)
    all_urls: List[str] = field(default_factory=list)
    contact_pages: List[str] = field(default_factory=list)
    team_pages: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    staff: List[StaffMember] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


# =============================================================================
# Sitemap Discovery (SITEMAP-01)
# =============================================================================

class SitemapDiscovery:
    """
    Discovers sitemap URLs for a domain.

    Tries multiple methods:
    1. robots.txt Sitemap: directives
    2. Common sitemap paths
    3. HTML <link rel="sitemap"> tags
    """

    COMMON_PATHS = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap/sitemap.xml",
        "/sitemaps/sitemap.xml",
        "/wp-sitemap.xml",
        "/sitemap.xml.gz",
        "/sitemap1.xml",
        "/sitemap-index.xml",
    ]

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def discover(self, domain: str) -> List[str]:
        """
        Discover sitemap URLs for a domain.

        Returns list of sitemap URLs found.
        """
        sitemaps = []
        base_url = f"https://{domain}"

        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "LeadSnipe/1.0 (sitemap crawler)"}
        ) as client:
            # Method 1: Check robots.txt
            robots_sitemaps = await self._from_robots(client, base_url)
            sitemaps.extend(robots_sitemaps)

            # Method 2: Try common paths if robots.txt didn't work
            if not sitemaps:
                common_sitemaps = await self._from_common_paths(client, base_url)
                sitemaps.extend(common_sitemaps)

            # Method 3: Check homepage for link tag
            if not sitemaps:
                link_sitemaps = await self._from_html_link(client, base_url)
                sitemaps.extend(link_sitemaps)

        return list(set(sitemaps))  # Dedupe

    async def _from_robots(self, client: httpx.AsyncClient, base_url: str) -> List[str]:
        """Extract Sitemap: directives from robots.txt."""
        try:
            response = await client.get(f"{base_url}/robots.txt")
            if response.status_code != 200:
                return []

            sitemaps = []
            for line in response.text.split("\n"):
                line = line.strip()
                if line.lower().startswith("sitemap:"):
                    url = line.split(":", 1)[1].strip()
                    sitemaps.append(url)
            return sitemaps
        except Exception:
            return []

    async def _from_common_paths(self, client: httpx.AsyncClient, base_url: str) -> List[str]:
        """Try common sitemap paths."""
        sitemaps = []
        for path in self.COMMON_PATHS:
            try:
                url = f"{base_url}{path}"
                response = await client.head(url)
                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "")
                    if "xml" in content_type or path.endswith(".xml") or path.endswith(".gz"):
                        sitemaps.append(url)
                        break  # Found one, stop trying
            except Exception:
                continue
        return sitemaps

    async def _from_html_link(self, client: httpx.AsyncClient, base_url: str) -> List[str]:
        """Look for <link rel="sitemap"> in homepage."""
        try:
            response = await client.get(base_url)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            sitemaps = []
            for link in soup.find_all("link", rel="sitemap"):
                href = link.get("href")
                if href:
                    sitemaps.append(urljoin(base_url, href))
            return sitemaps
        except Exception:
            return []


# =============================================================================
# Sitemap Parser (SITEMAP-02)
# =============================================================================

class SitemapParser:
    """
    Parses XML sitemaps recursively.

    Handles both urlset (regular) and sitemapindex formats.
    Supports compressed .gz sitemaps.
    """

    SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    def __init__(self, timeout: int = 15, max_depth: int = 3):
        self.timeout = timeout
        self.max_depth = max_depth

    async def parse(self, sitemap_url: str, depth: int = 0) -> List[str]:
        """
        Parse sitemap and return all page URLs.

        Recursively follows sitemap index references.
        """
        if depth >= self.max_depth:
            return []

        urls = []

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "LeadSnipe/1.0 (sitemap crawler)"}
            ) as client:
                response = await client.get(sitemap_url)
                if response.status_code != 200:
                    return []

                content = response.content

                # Handle gzip compressed sitemaps
                if sitemap_url.endswith(".gz") or response.headers.get("content-encoding") == "gzip":
                    try:
                        content = gzip.decompress(content)
                    except Exception:
                        pass

                # Parse XML
                try:
                    root = etree.fromstring(content)
                except etree.XMLSyntaxError:
                    # Try to clean up malformed XML
                    try:
                        parser = etree.XMLParser(recover=True)
                        root = etree.fromstring(content, parser)
                    except Exception:
                        return []

                # Check if this is a sitemap index
                sitemap_refs = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=self.SITEMAP_NS)

                if sitemap_refs:
                    # Recursively parse referenced sitemaps
                    for ref in sitemap_refs:
                        child_urls = await self.parse(ref.strip(), depth + 1)
                        urls.extend(child_urls)
                else:
                    # Regular sitemap - extract URLs
                    page_urls = root.xpath("//sm:url/sm:loc/text()", namespaces=self.SITEMAP_NS)
                    urls.extend([u.strip() for u in page_urls])

        except Exception:
            pass

        return urls


# =============================================================================
# URL Classification (SITEMAP-03)
# =============================================================================

class URLClassifier:
    """Classifies URLs into contact, team, or other categories."""

    CONTACT_PATTERNS = [
        r"/contact(?:-us)?/?$",
        r"/reach-us/?$",
        r"/get-in-touch/?$",
        r"/kontakt/?$",  # German
        r"/contacto/?$",  # Spanish
        r"/contact-info/?$",
        r"/connect/?$",
    ]

    TEAM_PATTERNS = [
        r"/team/?$",
        r"/our-team/?$",
        r"/the-team/?$",
        r"/leadership/?$",
        r"/staff/?$",
        r"/people/?$",
        r"/about/?$",
        r"/about-us/?$",
        r"/who-we-are/?$",
        r"/management/?$",
        r"/founders/?$",
        r"/executives/?$",
        r"/company/?$",
    ]

    def classify(self, urls: List[str]) -> Dict[str, List[str]]:
        """
        Classify URLs into categories.

        Returns dict with 'contact', 'team', 'other' keys.
        """
        result = {"contact": [], "team": [], "other": []}

        for url in urls:
            category = self._classify_single(url)
            result[category].append(url)

        return result

    def _classify_single(self, url: str) -> str:
        """Classify a single URL."""
        try:
            path = urlparse(url).path.lower()
        except Exception:
            return "other"

        # Check contact patterns first (more specific)
        for pattern in self.CONTACT_PATTERNS:
            if re.search(pattern, path):
                return "contact"

        # Check team patterns
        for pattern in self.TEAM_PATTERNS:
            if re.search(pattern, path):
                return "team"

        return "other"


# =============================================================================
# Email Extraction (SITEMAP-04)
# =============================================================================

class EmailExtractor:
    """Extracts email addresses from web pages."""

    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE
    )

    # Common false positives to filter
    BLACKLIST_PATTERNS = [
        r"\.png$", r"\.jpg$", r"\.gif$", r"\.css$", r"\.js$",
        r"@example\.com$", r"@sentry", r"@placeholder",
        r"@domain\.com$", r"@email\.com$", r"@company\.com$",
        r"wixpress\.com$", r"@2x\.", r"@3x\.",
    ]

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def extract(self, url: str) -> List[str]:
        """Extract email addresses from a URL."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "LeadSnipe/1.0 (email extractor)"}
            ) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return []

                html = response.text

                # Decode common obfuscation
                html = self._decode_obfuscation(html)

                # Extract from text
                text_emails = self.EMAIL_PATTERN.findall(html)

                # Extract from mailto: links
                mailto_emails = self._extract_mailto(html)

                # Combine and filter
                all_emails = list(set(text_emails + mailto_emails))
                filtered = self._filter_emails(all_emails)

                return filtered

        except Exception:
            return []

    def _decode_obfuscation(self, html: str) -> str:
        """Decode common email obfuscation patterns."""
        replacements = [
            (" [at] ", "@"), ("[at]", "@"), ("(at)", "@"),
            (" [dot] ", "."), ("[dot]", "."), ("(dot)", "."),
            (" at ", "@"), (" dot ", "."),
            ("&#64;", "@"), ("&#46;", "."),
        ]
        for old, new in replacements:
            html = html.replace(old, new)
        return html

    def _extract_mailto(self, html: str) -> List[str]:
        """Extract emails from mailto: links."""
        soup = BeautifulSoup(html, "html.parser")
        emails = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email:
                    emails.append(email)
        return emails

    def _filter_emails(self, emails: List[str]) -> List[str]:
        """Filter out false positives."""
        filtered = []
        for email in emails:
            email_lower = email.lower()
            is_blacklisted = any(
                re.search(pattern, email_lower)
                for pattern in self.BLACKLIST_PATTERNS
            )
            if not is_blacklisted and len(email) > 5:
                filtered.append(email)
        return filtered


# =============================================================================
# Staff Extraction (SITEMAP-05)
# =============================================================================

class StaffExtractor:
    """Extracts staff names and titles from team pages."""

    # CSS class patterns that often contain team members
    CARD_PATTERNS = [
        r"team", r"staff", r"member", r"person", r"employee",
        r"leadership", r"bio", r"profile", r"founder", r"executive"
    ]

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def extract(self, url: str) -> List[StaffMember]:
        """Extract staff members from a team page."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "LeadSnipe/1.0 (staff extractor)"}
            ) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return []

                html = response.text

                # Try multiple extraction methods
                staff = []

                # Method 1: Schema.org JSON-LD
                jsonld_staff = self._extract_jsonld(html)
                staff.extend(jsonld_staff)

                # Method 2: HTML card patterns
                if not staff:
                    card_staff = self._extract_from_cards(html)
                    staff.extend(card_staff)

                return staff

        except Exception:
            return []

    def _extract_jsonld(self, html: str) -> List[StaffMember]:
        """Extract Person data from JSON-LD structured data."""
        soup = BeautifulSoup(html, "html.parser")
        staff = []

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                staff.extend(self._parse_jsonld_item(data))
            except (json.JSONDecodeError, TypeError):
                continue

        return staff

    def _parse_jsonld_item(self, data) -> List[StaffMember]:
        """Parse a JSON-LD item or list."""
        staff = []

        if isinstance(data, list):
            for item in data:
                staff.extend(self._parse_jsonld_item(item))
        elif isinstance(data, dict):
            item_type = data.get("@type", "")

            # Direct Person
            if item_type == "Person" or item_type == ["Person"]:
                staff.append(StaffMember(
                    name=data.get("name", ""),
                    title=data.get("jobTitle"),
                    email=data.get("email")
                ))

            # Organization with employees
            if "employee" in data:
                employees = data["employee"]
                if isinstance(employees, list):
                    for emp in employees:
                        staff.extend(self._parse_jsonld_item(emp))
                else:
                    staff.extend(self._parse_jsonld_item(employees))

            # Check @graph
            if "@graph" in data:
                staff.extend(self._parse_jsonld_item(data["@graph"]))

        return [s for s in staff if s.name]  # Filter empty names

    def _extract_from_cards(self, html: str) -> List[StaffMember]:
        """Extract staff from common HTML card patterns."""
        soup = BeautifulSoup(html, "html.parser")
        staff = []

        # Find elements with team/staff related classes
        pattern = re.compile("|".join(self.CARD_PATTERNS), re.IGNORECASE)

        # Look for cards/containers
        cards = soup.find_all(class_=pattern)

        for card in cards:
            member = self._extract_from_card(card)
            if member:
                staff.append(member)

        # Dedupe by name
        seen_names = set()
        unique_staff = []
        for member in staff:
            if member.name.lower() not in seen_names:
                seen_names.add(member.name.lower())
                unique_staff.append(member)

        return unique_staff

    def _extract_from_card(self, card) -> Optional[StaffMember]:
        """Extract a single staff member from a card element."""
        name = None
        title = None
        email = None

        # Find name - usually in heading or strong
        for tag in ["h2", "h3", "h4", "h5", "strong", "b"]:
            elem = card.find(tag)
            if elem:
                text = elem.get_text(strip=True)
                # Basic name validation (has space, not too long)
                if " " in text and len(text) < 50 and not text.startswith("http"):
                    name = text
                    break

        # Find title - usually in element with title/role/position class
        title_pattern = re.compile(r"title|role|position|job|designation", re.IGNORECASE)
        title_elem = card.find(class_=title_pattern)
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Find email from mailto
        email_link = card.find("a", href=re.compile(r"^mailto:"))
        if email_link:
            email = email_link["href"].replace("mailto:", "").split("?")[0]

        if name:
            return StaffMember(name=name, title=title, email=email)
        return None


# =============================================================================
# Main Sniper Class (Task 2.6)
# =============================================================================

class SitemapSniper:
    """
    Main class to snipe sitemaps for lead data.

    Orchestrates discovery, parsing, classification, and extraction.
    """

    def __init__(
        self,
        timeout: int = 10,
        max_sitemap_depth: int = 3,
        request_delay: float = 0.5
    ):
        self.discovery = SitemapDiscovery(timeout=timeout)
        self.parser = SitemapParser(timeout=timeout, max_depth=max_sitemap_depth)
        self.classifier = URLClassifier()
        self.email_extractor = EmailExtractor(timeout=timeout)
        self.staff_extractor = StaffExtractor(timeout=timeout)
        self.request_delay = request_delay

    async def snipe(self, domain: str) -> SitemapResult:
        """
        Snipe a domain for lead data via sitemap.

        Steps:
        1. Discover sitemap URLs
        2. Parse sitemaps for all page URLs
        3. Classify URLs into contact/team pages
        4. Extract emails from contact pages
        5. Extract staff from team pages
        """
        result = SitemapResult(domain=domain)

        # Step 1: Discover sitemaps
        try:
            sitemap_urls = await self.discovery.discover(domain)
            result.sitemap_urls = sitemap_urls
        except Exception as e:
            result.errors.append(f"Discovery failed: {e}")
            return result

        if not sitemap_urls:
            result.errors.append("No sitemap found")
            # Still try fallback contact pages
            result = await self._fallback_scrape(domain, result)
            return result

        # Step 2: Parse sitemaps
        all_urls = []
        for sitemap_url in sitemap_urls:
            try:
                urls = await self.parser.parse(sitemap_url)
                all_urls.extend(urls)
            except Exception as e:
                result.errors.append(f"Parse failed for {sitemap_url}: {e}")

        result.all_urls = list(set(all_urls))

        # Step 3: Classify URLs
        classified = self.classifier.classify(result.all_urls)
        result.contact_pages = classified["contact"]
        result.team_pages = classified["team"]

        # Step 4: Extract emails from contact pages
        for url in result.contact_pages[:5]:  # Limit to avoid overload
            try:
                emails = await self.email_extractor.extract(url)
                result.emails.extend(emails)
                await asyncio.sleep(self.request_delay)
            except Exception:
                pass
        result.emails = list(set(result.emails))

        # Step 5: Extract staff from team pages
        for url in result.team_pages[:5]:
            try:
                staff = await self.staff_extractor.extract(url)
                result.staff.extend(staff)
                await asyncio.sleep(self.request_delay)
            except Exception:
                pass

        return result

    async def _fallback_scrape(self, domain: str, result: SitemapResult) -> SitemapResult:
        """Try common contact/team URLs directly when no sitemap found."""
        base_url = f"https://{domain}"

        contact_paths = ["/contact", "/contact-us", "/about/contact"]
        team_paths = ["/about", "/about-us", "/team", "/our-team"]

        async with httpx.AsyncClient(
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "LeadSnipe/1.0"}
        ) as client:
            # Try contact pages
            for path in contact_paths:
                try:
                    url = f"{base_url}{path}"
                    response = await client.head(url)
                    if response.status_code == 200:
                        result.contact_pages.append(url)
                        emails = await self.email_extractor.extract(url)
                        result.emails.extend(emails)
                        break
                except Exception:
                    pass

            # Try team pages
            for path in team_paths:
                try:
                    url = f"{base_url}{path}"
                    response = await client.head(url)
                    if response.status_code == 200:
                        result.team_pages.append(url)
                        staff = await self.staff_extractor.extract(url)
                        result.staff.extend(staff)
                        break
                except Exception:
                    pass

        result.emails = list(set(result.emails))
        return result


# =============================================================================
# Public API
# =============================================================================

async def snipe_sitemap(domain: str) -> SitemapResult:
    """
    Async API: Snipe a domain's sitemap for lead data.

    Args:
        domain: Domain to snipe (e.g., "example.com")

    Returns:
        SitemapResult with discovered data
    """
    sniper = SitemapSniper()
    return await sniper.snipe(domain)


def snipe_sitemap_sync(domain: str) -> SitemapResult:
    """
    Sync wrapper: Snipe a domain's sitemap.

    Use from synchronous code.
    """
    return asyncio.run(snipe_sitemap(domain))


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sitemap_sniper.py domain.com")
        print("\nExample:")
        print("  python sitemap_sniper.py example.com")
        sys.exit(1)

    domain = sys.argv[1].replace("https://", "").replace("http://", "").rstrip("/")

    print(f"\nSniping sitemap for: {domain}\n")
    print("=" * 60)

    result = snipe_sitemap_sync(domain)

    print(f"Sitemap URLs found: {len(result.sitemap_urls)}")
    for url in result.sitemap_urls:
        print(f"  - {url}")

    print(f"\nTotal URLs in sitemap: {len(result.all_urls)}")
    print(f"Contact pages: {len(result.contact_pages)}")
    for url in result.contact_pages[:5]:
        print(f"  - {url}")

    print(f"\nTeam pages: {len(result.team_pages)}")
    for url in result.team_pages[:5]:
        print(f"  - {url}")

    print(f"\nEmails extracted: {len(result.emails)}")
    for email in result.emails:
        print(f"  - {email}")

    print(f"\nStaff members: {len(result.staff)}")
    for staff in result.staff[:10]:
        title_str = f" ({staff.title})" if staff.title else ""
        email_str = f" <{staff.email}>" if staff.email else ""
        print(f"  - {staff.name}{title_str}{email_str}")

    if result.errors:
        print(f"\nErrors: {len(result.errors)}")
        for error in result.errors:
            print(f"  - {error}")

    print("\n" + "=" * 60)
