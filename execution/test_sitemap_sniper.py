"""
Unit Tests for Sitemap Sniper

Tests cover all SITEMAP requirements:
- SITEMAP-01: Sitemap URL discovery
- SITEMAP-02: Recursive sitemap parsing
- SITEMAP-03: Contact page identification
- SITEMAP-04: Email extraction from pages
- SITEMAP-05: Staff name extraction
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from sitemap_sniper import (
    SitemapDiscovery,
    SitemapParser,
    URLClassifier,
    EmailExtractor,
    StaffExtractor,
    SitemapSniper,
    snipe_sitemap,
    snipe_sitemap_sync,
    StaffMember,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def discovery():
    return SitemapDiscovery(timeout=5)


@pytest.fixture
def parser():
    return SitemapParser(timeout=5, max_depth=3)


@pytest.fixture
def classifier():
    return URLClassifier()


@pytest.fixture
def email_extractor():
    return EmailExtractor(timeout=5)


@pytest.fixture
def staff_extractor():
    return StaffExtractor(timeout=5)


# =============================================================================
# Sitemap Discovery Tests (SITEMAP-01)
# =============================================================================

class TestSitemapDiscovery:
    """Tests for sitemap discovery."""

    @pytest.mark.asyncio
    async def test_discover_from_robots(self, discovery):
        """Finds sitemap from robots.txt."""
        robots_content = """
User-agent: *
Disallow: /admin

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-posts.xml
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = robots_content
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            sitemaps = await discovery.discover("example.com")

            assert len(sitemaps) == 2
            assert "https://example.com/sitemap.xml" in sitemaps
            assert "https://example.com/sitemap-posts.xml" in sitemaps

    @pytest.mark.asyncio
    async def test_discover_fallback_paths(self, discovery):
        """Uses common paths when robots.txt has no sitemap."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            # robots.txt returns 404
            robots_response = MagicMock()
            robots_response.status_code = 404

            # /sitemap.xml returns 200
            sitemap_response = MagicMock()
            sitemap_response.status_code = 200
            sitemap_response.headers = {"content-type": "application/xml"}

            mock_client.get = AsyncMock(return_value=robots_response)
            mock_client.head = AsyncMock(return_value=sitemap_response)

            mock_client_class.return_value = mock_client

            sitemaps = await discovery.discover("example.com")

            assert len(sitemaps) >= 1

    @pytest.mark.asyncio
    async def test_discover_returns_empty_on_failure(self, discovery):
        """Returns empty list when all methods fail."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            # All requests fail
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.head = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            sitemaps = await discovery.discover("nonexistent.invalid")

            assert sitemaps == []


# =============================================================================
# Sitemap Parser Tests (SITEMAP-02)
# =============================================================================

class TestSitemapParser:
    """Tests for sitemap parsing."""

    @pytest.mark.asyncio
    async def test_parse_simple_sitemap(self, parser):
        """Parses simple urlset sitemap correctly."""
        sitemap_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/about</loc></url>
  <url><loc>https://example.com/contact</loc></url>
  <url><loc>https://example.com/team</loc></url>
</urlset>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = sitemap_xml
            mock_response.headers = {}
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            urls = await parser.parse("https://example.com/sitemap.xml")

            assert len(urls) == 3
            assert "https://example.com/about" in urls
            assert "https://example.com/contact" in urls
            assert "https://example.com/team" in urls

    @pytest.mark.asyncio
    async def test_parse_sitemap_index(self, parser):
        """Recursively parses sitemap index."""
        index_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
</sitemapindex>
"""
        pages_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/page1</loc></url>
</urlset>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            call_count = 0

            async def mock_get(url):
                nonlocal call_count
                call_count += 1
                response = MagicMock()
                response.status_code = 200
                response.headers = {}
                if "index" in url or call_count == 1:
                    response.content = index_xml
                else:
                    response.content = pages_xml
                return response

            mock_client.get = mock_get
            mock_client_class.return_value = mock_client

            urls = await parser.parse("https://example.com/sitemap-index.xml")

            assert "https://example.com/page1" in urls

    @pytest.mark.asyncio
    async def test_parse_respects_max_depth(self, parser):
        """Stops recursion at max depth."""
        parser.max_depth = 1

        index_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-deep.xml</loc></sitemap>
</sitemapindex>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = index_xml
            mock_response.headers = {}
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            # Should not recurse past depth 1
            urls = await parser.parse("https://example.com/sitemap.xml", depth=1)

            assert urls == []  # Max depth reached, no URLs extracted


# =============================================================================
# URL Classifier Tests (SITEMAP-03)
# =============================================================================

class TestURLClassifier:
    """Tests for URL classification."""

    def test_classify_contact_pages(self, classifier):
        """Identifies contact pages correctly."""
        urls = [
            "https://example.com/contact",
            "https://example.com/contact-us",
            "https://example.com/reach-us/",
            "https://example.com/get-in-touch",
        ]

        result = classifier.classify(urls)

        assert len(result["contact"]) == 4
        assert len(result["team"]) == 0

    def test_classify_team_pages(self, classifier):
        """Identifies team pages correctly."""
        urls = [
            "https://example.com/team",
            "https://example.com/about",
            "https://example.com/about-us/",
            "https://example.com/leadership",
            "https://example.com/our-team",
        ]

        result = classifier.classify(urls)

        assert len(result["team"]) == 5
        assert len(result["contact"]) == 0

    def test_classify_other_pages(self, classifier):
        """Classifies non-contact/team pages as other."""
        urls = [
            "https://example.com/blog",
            "https://example.com/products",
            "https://example.com/pricing",
        ]

        result = classifier.classify(urls)

        assert len(result["other"]) == 3
        assert len(result["contact"]) == 0
        assert len(result["team"]) == 0

    def test_classify_handles_query_params(self, classifier):
        """Handles URLs with query parameters."""
        urls = [
            "https://example.com/contact?ref=footer",
            "https://example.com/team?lang=en",
        ]

        result = classifier.classify(urls)

        # Should still classify based on path
        assert len(result["contact"]) == 1
        assert len(result["team"]) == 1


# =============================================================================
# Email Extraction Tests (SITEMAP-04)
# =============================================================================

class TestEmailExtractor:
    """Tests for email extraction."""

    @pytest.mark.asyncio
    async def test_extract_plain_emails(self, email_extractor):
        """Extracts plain text emails."""
        html = """
<html>
<body>
Contact us at sales@example.com or support@example.com
</body>
</html>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            emails = await email_extractor.extract("https://example.com/contact")

            assert "sales@example.com" in emails
            assert "support@example.com" in emails

    @pytest.mark.asyncio
    async def test_extract_mailto_emails(self, email_extractor):
        """Extracts emails from mailto: links."""
        html = """
<html>
<body>
<a href="mailto:info@example.com">Email us</a>
<a href="mailto:john@example.com?subject=Hello">Contact John</a>
</body>
</html>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            emails = await email_extractor.extract("https://example.com/contact")

            assert "info@example.com" in emails
            assert "john@example.com" in emails

    @pytest.mark.asyncio
    async def test_extract_obfuscated_emails(self, email_extractor):
        """Decodes obfuscated emails."""
        html = """
<html>
<body>
Email: sales [at] example [dot] com
Also: support(at)example(dot)com
</body>
</html>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            emails = await email_extractor.extract("https://example.com/contact")

            assert "sales@example.com" in emails
            assert "support@example.com" in emails

    @pytest.mark.asyncio
    async def test_filters_false_positives(self, email_extractor):
        """Filters out false positive emails."""
        html = """
<html>
<body>
<img src="icon@2x.png">
Contact: real@example.com
Ignore: test@example.com.jpg
</body>
</html>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            emails = await email_extractor.extract("https://example.com/contact")

            assert "real@example.com" in emails
            # False positives should be filtered
            assert not any("@2x" in e for e in emails)


# =============================================================================
# Staff Extraction Tests (SITEMAP-05)
# =============================================================================

class TestStaffExtractor:
    """Tests for staff extraction."""

    @pytest.mark.asyncio
    async def test_extract_from_cards(self, staff_extractor):
        """Extracts staff from HTML card elements."""
        html = """
<html>
<body>
<div class="team-member">
  <h3>John Smith</h3>
  <p class="title">CEO</p>
  <a href="mailto:john@example.com">Email</a>
</div>
<div class="team-member">
  <h3>Jane Doe</h3>
  <p class="job-title">CTO</p>
</div>
</body>
</html>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            staff = await staff_extractor.extract("https://example.com/team")

            assert len(staff) >= 2
            names = [s.name for s in staff]
            assert "John Smith" in names
            assert "Jane Doe" in names

    @pytest.mark.asyncio
    async def test_extract_jsonld(self, staff_extractor):
        """Extracts staff from JSON-LD structured data."""
        html = """
<html>
<head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "employee": [
    {"@type": "Person", "name": "Alice Brown", "jobTitle": "Founder"},
    {"@type": "Person", "name": "Bob Green", "jobTitle": "Developer"}
  ]
}
</script>
</head>
<body></body>
</html>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            staff = await staff_extractor.extract("https://example.com/about")

            assert len(staff) == 2
            names = [s.name for s in staff]
            assert "Alice Brown" in names
            assert "Bob Green" in names

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_staff(self, staff_extractor):
        """Returns empty list when no staff found."""
        html = """
<html>
<body>
<p>Just regular content here.</p>
</body>
</html>
"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = html
            mock_client.get = AsyncMock(return_value=mock_response)

            mock_client_class.return_value = mock_client

            staff = await staff_extractor.extract("https://example.com/about")

            assert staff == []


# =============================================================================
# Integration Tests
# =============================================================================

class TestSitemapSniperIntegration:
    """Integration tests for SitemapSniper."""

    def test_sync_wrapper_works(self):
        """Sync wrapper can be called from non-async code."""
        with patch('sitemap_sniper.SitemapSniper.snipe') as mock_snipe:
            from sitemap_sniper import SitemapResult
            mock_snipe.return_value = SitemapResult(domain="example.com")

            # This should not raise
            result = snipe_sitemap_sync("example.com")

            assert result.domain == "example.com"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
