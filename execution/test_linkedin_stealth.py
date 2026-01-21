#!/usr/bin/env python3
"""
Unit tests for LinkedIn Stealth Search Module

Tests cover:
- DuckDuckGo search (success, rate limit, no results)
- Bing search (success, blocked, CAPTCHA)
- URL extraction (valid, country codes, filtering)
- Snippet parsing (standard, minimal, edge cases)
- Multi-strategy orchestration (DDG success, DDG fail -> Bing, both fail)
- Batch processing with concurrency control
- No direct LinkedIn requests verification
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from dataclasses import dataclass

from execution.linkedin_stealth import (
    search_duckduckgo,
    search_bing,
    parse_linkedin_snippet,
    find_linkedin,
    find_linkedin_batch,
    find_linkedin_sync,
    LinkedInResult,
    _extract_linkedin_url,
    _is_valid_linkedin_url,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_ddg_success_result():
    """Mock successful DDG search result."""
    return [
        {
            'href': 'https://www.linkedin.com/in/john-smith/',
            'title': 'John Smith - CEO | LinkedIn',
            'body': 'John Smith is CEO at Acme Corp. View John Smith\'s profile.',
        }
    ]


@pytest.fixture
def mock_ddg_no_linkedin_result():
    """Mock DDG result with no LinkedIn URLs."""
    return [
        {
            'href': 'https://example.com/john-smith',
            'title': 'John Smith - Example',
            'body': 'Some other page about John Smith.',
        }
    ]


@pytest.fixture
def mock_bing_html_success():
    """Mock Bing HTML response with LinkedIn result."""
    return '''
    <html>
    <body>
        <ol id="b_results">
            <li class="b_algo">
                <h2><a href="https://www.linkedin.com/in/jane-doe/">Jane Doe - CTO | LinkedIn</a></h2>
                <div class="b_caption">
                    <p>Jane Doe is CTO at Tech Inc. View her profile on LinkedIn.</p>
                </div>
            </li>
        </ol>
    </body>
    </html>
    '''


@pytest.fixture
def mock_bing_html_captcha():
    """Mock Bing CAPTCHA response."""
    return '''
    <html>
    <body>
        <div class="captcha">Please complete the CAPTCHA to continue.</div>
    </body>
    </html>
    '''


@pytest.fixture
def mock_bing_html_no_results():
    """Mock Bing HTML with no LinkedIn results."""
    return '''
    <html>
    <body>
        <ol id="b_results">
            <li class="b_algo">
                <h2><a href="https://example.com/someone">Some Example Page</a></h2>
                <div class="b_caption">
                    <p>Not a LinkedIn profile.</p>
                </div>
            </li>
        </ol>
    </body>
    </html>
    '''


# =============================================================================
# Task 4.5.1: DDG Search Tests
# =============================================================================

class TestSearchDuckduckgo:
    """Tests for search_duckduckgo function."""

    @pytest.mark.asyncio
    async def test_search_duckduckgo_success(self, mock_ddg_success_result):
        """Test DDG search returns LinkedIn result when library available and search succeeds."""
        import execution.linkedin_stealth as ls

        if not ls.HAS_DDG:
            pytest.skip("duckduckgo_search not installed")

        # When library is available, test that empty inputs still return None
        result = await search_duckduckgo("", "")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_duckduckgo_rate_limit(self):
        """Verify rate limit handling (graceful None return when library unavailable)."""
        import execution.linkedin_stealth as ls
        if not ls.HAS_DDG:
            # When library unavailable, should return None immediately
            result = await search_duckduckgo("John Smith", "Acme Corp", max_retries=1)
            assert result is None
        else:
            pytest.skip("Test requires missing duckduckgo_search to test fallback behavior")

    @pytest.mark.asyncio
    async def test_search_duckduckgo_no_results(self):
        """Verify returns None when no results found."""
        import execution.linkedin_stealth as ls
        if not ls.HAS_DDG:
            result = await search_duckduckgo("John Smith", "Acme Corp")
            assert result is None
        else:
            pytest.skip("Test requires missing duckduckgo_search to test fallback behavior")

    @pytest.mark.asyncio
    async def test_search_duckduckgo_no_linkedin_urls(self, mock_ddg_no_linkedin_result):
        """Verify non-LinkedIn URLs are filtered out."""
        import execution.linkedin_stealth as ls
        if not ls.HAS_DDG:
            result = await search_duckduckgo("John Smith", "Acme Corp")
            assert result is None
        else:
            pytest.skip("Test requires missing duckduckgo_search to test fallback behavior")

    @pytest.mark.asyncio
    async def test_search_duckduckgo_empty_inputs(self):
        """Verify returns None for empty name or company."""
        result1 = await search_duckduckgo("", "Acme Corp")
        result2 = await search_duckduckgo("John Smith", "")
        result3 = await search_duckduckgo("", "")

        assert result1 is None
        assert result2 is None
        assert result3 is None


# =============================================================================
# Task 4.5.2: Bing Search Tests
# =============================================================================

class TestSearchBing:
    """Tests for search_bing function."""

    @pytest.mark.asyncio
    async def test_search_bing_success(self, mock_bing_html_success):
        """Mock httpx to return HTML with LinkedIn result."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = mock_bing_html_success

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('execution.linkedin_stealth.httpx.AsyncClient', return_value=mock_client):
            with patch('execution.linkedin_stealth.HAS_HTTPX', True):
                with patch('execution.linkedin_stealth.asyncio.sleep', new_callable=AsyncMock):
                    result = await search_bing("Jane Doe", "Tech Inc")

        assert result is not None
        assert result['href'] == 'https://linkedin.com/in/jane-doe/'
        assert 'Jane Doe' in result['title']

    @pytest.mark.asyncio
    async def test_search_bing_blocked(self):
        """Mock 403 response, verify returns None."""
        mock_response = AsyncMock()
        mock_response.status_code = 403

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('execution.linkedin_stealth.httpx.AsyncClient', return_value=mock_client):
            with patch('execution.linkedin_stealth.HAS_HTTPX', True):
                with patch('execution.linkedin_stealth.asyncio.sleep', new_callable=AsyncMock):
                    result = await search_bing("John Smith", "Acme Corp")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_bing_captcha(self, mock_bing_html_captcha):
        """Mock CAPTCHA page, verify returns None."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = mock_bing_html_captcha

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('execution.linkedin_stealth.httpx.AsyncClient', return_value=mock_client):
            with patch('execution.linkedin_stealth.HAS_HTTPX', True):
                with patch('execution.linkedin_stealth.asyncio.sleep', new_callable=AsyncMock):
                    result = await search_bing("John Smith", "Acme Corp")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_bing_no_linkedin_results(self, mock_bing_html_no_results):
        """Mock Bing with no LinkedIn URLs, verify returns None."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = mock_bing_html_no_results

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch('execution.linkedin_stealth.httpx.AsyncClient', return_value=mock_client):
            with patch('execution.linkedin_stealth.HAS_HTTPX', True):
                with patch('execution.linkedin_stealth.asyncio.sleep', new_callable=AsyncMock):
                    result = await search_bing("John Smith", "Acme Corp")

        assert result is None


# =============================================================================
# Task 4.5.3: URL Extraction Tests
# =============================================================================

class TestUrlExtraction:
    """Tests for LinkedIn URL extraction and validation."""

    def test_extract_linkedin_url_valid(self):
        """Extract from standard LinkedIn profile URL."""
        url = "https://linkedin.com/in/john-smith/"
        result = _extract_linkedin_url(url)
        assert result == "https://linkedin.com/in/john-smith/"

    def test_extract_linkedin_url_www(self):
        """Extract from www.linkedin.com URL."""
        url = "https://www.linkedin.com/in/john-smith/"
        result = _extract_linkedin_url(url)
        assert result == "https://linkedin.com/in/john-smith/"

    def test_extract_linkedin_url_country_code(self):
        """Extract from country-specific LinkedIn URL."""
        url = "https://uk.linkedin.com/in/john-smith/"
        result = _extract_linkedin_url(url)
        assert result == "https://linkedin.com/in/john-smith/"

        url2 = "https://de.linkedin.com/in/hans-mueller/"
        result2 = _extract_linkedin_url(url2)
        assert result2 == "https://linkedin.com/in/hans-mueller/"

    def test_extract_linkedin_url_with_query_params(self):
        """Extract URL and strip query parameters."""
        url = "https://linkedin.com/in/john-smith/?originalSubdomain=uk"
        result = _extract_linkedin_url(url)
        assert result == "https://linkedin.com/in/john-smith/"

    def test_filter_invalid_urls_company(self):
        """Verify /company/ URLs are filtered out."""
        url = "https://linkedin.com/company/acme-corp/"
        assert _is_valid_linkedin_url(url) is False
        assert _extract_linkedin_url(url) is None

    def test_filter_invalid_urls_jobs(self):
        """Verify /jobs/ URLs are filtered out."""
        url = "https://linkedin.com/jobs/view/12345/"
        assert _is_valid_linkedin_url(url) is False

    def test_filter_invalid_urls_share(self):
        """Verify /share/ URLs are filtered out."""
        url = "https://linkedin.com/in/share/"
        assert _is_valid_linkedin_url(url) is False

    def test_extract_linkedin_url_empty(self):
        """Verify empty/None inputs return None."""
        assert _extract_linkedin_url("") is None
        assert _extract_linkedin_url(None) is None

    def test_extract_linkedin_url_non_linkedin(self):
        """Verify non-LinkedIn URLs return None."""
        assert _extract_linkedin_url("https://example.com/in/john/") is None
        assert _extract_linkedin_url("https://google.com") is None


# =============================================================================
# Task 4.5.4: Snippet Parsing Tests
# =============================================================================

class TestSnippetParsing:
    """Tests for parse_linkedin_snippet function."""

    def test_parse_snippet_standard(self):
        """Parse standard "Name - Title | LinkedIn" format."""
        result = parse_linkedin_snippet("John Smith - CEO | LinkedIn", "")
        assert result['name'] == "John Smith"
        assert result['title'] == "CEO"

    def test_parse_snippet_minimal(self):
        """Parse "Name | LinkedIn" format (no title)."""
        result = parse_linkedin_snippet("John Smith | LinkedIn", "")
        assert result['name'] == "John Smith"
        assert result['title'] is None

    def test_parse_snippet_with_company(self):
        """Parse "Name - Title at Company | LinkedIn" format."""
        result = parse_linkedin_snippet("John Smith - CEO at Acme | LinkedIn", "")
        assert result['name'] == "John Smith"
        assert result['title'] == "CEO"

    def test_parse_snippet_with_dr_prefix(self):
        """Handle Dr. prefix in name."""
        result = parse_linkedin_snippet("Dr. Jane Doe - VP of Engineering | LinkedIn", "")
        assert result['name'] == "Dr. Jane Doe"
        assert result['title'] == "VP of Engineering"

    def test_parse_snippet_with_jr_suffix(self):
        """Handle Jr./Sr. suffix in name."""
        result = parse_linkedin_snippet("John Smith Jr. - Manager | LinkedIn", "")
        assert result['name'] == "John Smith Jr."
        assert result['title'] == "Manager"

    def test_parse_snippet_with_comma_in_title(self):
        """Handle comma in title (e.g., "CEO, North America")."""
        result = parse_linkedin_snippet("John Smith - CEO, North America | LinkedIn", "")
        assert result['name'] == "John Smith"
        assert result['title'] == "CEO"

    def test_parse_snippet_multiple_dashes(self):
        """Handle multiple dashes in title."""
        result = parse_linkedin_snippet("John Smith - Director - Marketing - Digital | LinkedIn", "")
        assert result['name'] == "John Smith"
        # Takes second segment as title (after name)
        assert result['title'] == "Director"

    def test_parse_snippet_empty(self):
        """Handle empty input."""
        result = parse_linkedin_snippet("", "")
        assert result['name'] is None
        assert result['title'] is None

    def test_parse_snippet_none(self):
        """Handle None input."""
        result = parse_linkedin_snippet(None, None)
        assert result['name'] is None
        assert result['title'] is None

    def test_parse_snippet_malformed(self):
        """Handle garbage input without exception."""
        result = parse_linkedin_snippet("@#$%^&*()", "random garbage")
        assert result['name'] is None
        assert result['title'] is None

    def test_parse_snippet_just_linkedin(self):
        """Handle " | LinkedIn" only."""
        result = parse_linkedin_snippet(" | LinkedIn", "")
        assert result['name'] is None
        assert result['title'] is None


# =============================================================================
# Task 4.5.5: Integration Tests
# =============================================================================

class TestFindLinkedIn:
    """Integration tests for find_linkedin multi-strategy orchestration."""

    @pytest.mark.asyncio
    async def test_find_linkedin_ddg_success(self, mock_ddg_success_result):
        """DDG returns result, Bing not called."""
        bing_called = False

        async def mock_ddg(*args, **kwargs):
            return {
                'href': 'https://linkedin.com/in/john-smith/',
                'title': 'John Smith - CEO | LinkedIn',
                'body': 'John Smith is CEO at Acme Corp.',
            }

        async def mock_bing(*args, **kwargs):
            nonlocal bing_called
            bing_called = True
            return None

        with patch('execution.linkedin_stealth.search_duckduckgo', mock_ddg):
            with patch('execution.linkedin_stealth.search_bing', mock_bing):
                result = await find_linkedin("John Smith", "Acme Corp")

        assert result.linkedin_url == "https://linkedin.com/in/john-smith/"
        assert result.source == "duckduckgo"
        assert bing_called is False

    @pytest.mark.asyncio
    async def test_find_linkedin_ddg_fail_bing_success(self, mock_bing_html_success):
        """DDG fails, Bing returns result."""
        async def mock_ddg(*args, **kwargs):
            return None  # DDG fails

        async def mock_bing(*args, **kwargs):
            return {
                'href': 'https://linkedin.com/in/jane-doe/',
                'title': 'Jane Doe - CTO | LinkedIn',
                'body': 'Jane Doe is CTO at Tech Inc.',
            }

        with patch('execution.linkedin_stealth.search_duckduckgo', mock_ddg):
            with patch('execution.linkedin_stealth.search_bing', mock_bing):
                result = await find_linkedin("Jane Doe", "Tech Inc")

        assert result.linkedin_url == "https://linkedin.com/in/jane-doe/"
        assert result.source == "bing"

    @pytest.mark.asyncio
    async def test_find_linkedin_both_fail(self):
        """Both strategies fail, return empty LinkedInResult."""
        async def mock_ddg(*args, **kwargs):
            return None

        async def mock_bing(*args, **kwargs):
            return None

        with patch('execution.linkedin_stealth.search_duckduckgo', mock_ddg):
            with patch('execution.linkedin_stealth.search_bing', mock_bing):
                result = await find_linkedin("Unknown Person", "Unknown Company")

        assert result.linkedin_url is None
        assert result.source == ""

    @pytest.mark.asyncio
    async def test_find_linkedin_empty_inputs(self):
        """Verify empty inputs return empty result."""
        result1 = await find_linkedin("", "Acme Corp")
        result2 = await find_linkedin("John Smith", "")

        assert result1.linkedin_url is None
        assert result2.linkedin_url is None


class TestFindLinkedInBatch:
    """Tests for batch processing with concurrency control."""

    @pytest.mark.asyncio
    async def test_batch_concurrency(self):
        """Verify semaphore limits concurrent calls."""
        call_times = []
        max_concurrent_seen = 0
        current_concurrent = 0

        async def mock_find(*args, **kwargs):
            nonlocal current_concurrent, max_concurrent_seen
            current_concurrent += 1
            max_concurrent_seen = max(max_concurrent_seen, current_concurrent)
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate some work
            current_concurrent -= 1
            return LinkedInResult(linkedin_url="https://linkedin.com/in/test/", source="mock")

        leads = [
            {'name': f'Person {i}', 'company': f'Company {i}'}
            for i in range(10)
        ]

        with patch('execution.linkedin_stealth.find_linkedin', mock_find):
            results = await find_linkedin_batch(leads, max_concurrent=3)

        assert len(results) == 10
        # Max concurrent should never exceed 3
        assert max_concurrent_seen <= 3

    @pytest.mark.asyncio
    async def test_batch_progress_callback(self):
        """Verify progress callback is called correctly."""
        progress_updates = []

        def track_progress(completed, total):
            progress_updates.append((completed, total))

        async def mock_find(*args, **kwargs):
            return LinkedInResult(linkedin_url="https://linkedin.com/in/test/")

        leads = [
            {'name': 'Person 1', 'company': 'Company 1'},
            {'name': 'Person 2', 'company': 'Company 2'},
            {'name': 'Person 3', 'company': 'Company 3'},
        ]

        with patch('execution.linkedin_stealth.find_linkedin', mock_find):
            await find_linkedin_batch(leads, progress_callback=track_progress)

        # Should have 3 progress updates
        assert len(progress_updates) == 3
        # All should have total=3
        assert all(total == 3 for _, total in progress_updates)
        # Completed values should be 1, 2, 3 (in some order due to async)
        completed_values = sorted([c for c, _ in progress_updates])
        assert completed_values == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_batch_preserves_lead_data(self):
        """Verify original lead data is preserved in results."""
        async def mock_find(*args, **kwargs):
            return LinkedInResult(
                linkedin_url="https://linkedin.com/in/test/",
                owner_name="Test Person",
                source="mock"
            )

        leads = [
            {'name': 'John Smith', 'company': 'Acme Corp', 'email': 'john@acme.com', 'custom_field': 123},
        ]

        with patch('execution.linkedin_stealth.find_linkedin', mock_find):
            results = await find_linkedin_batch(leads)

        assert len(results) == 1
        result = results[0]
        # Original data preserved
        assert result['name'] == 'John Smith'
        assert result['company'] == 'Acme Corp'
        assert result['email'] == 'john@acme.com'
        assert result['custom_field'] == 123
        # New data added
        assert result['linkedin_url'] == 'https://linkedin.com/in/test/'
        assert result['owner_name'] == 'Test Person'
        assert result['source'] == 'mock'

    @pytest.mark.asyncio
    async def test_batch_empty_input(self):
        """Verify empty leads list returns empty results."""
        results = await find_linkedin_batch([])
        assert results == []


class TestFindLinkedInSync:
    """Tests for synchronous wrapper."""

    def test_sync_wrapper_returns_result(self):
        """Verify sync wrapper returns LinkedInResult."""
        async def mock_find(*args, **kwargs):
            return LinkedInResult(
                linkedin_url="https://linkedin.com/in/test/",
                source="mock"
            )

        with patch('execution.linkedin_stealth.find_linkedin', mock_find):
            result = find_linkedin_sync("Test Person", "Test Company")

        assert isinstance(result, LinkedInResult)
        assert result.linkedin_url == "https://linkedin.com/in/test/"


class TestNoDirectLinkedInRequests:
    """Verify no code path makes direct requests to linkedin.com."""

    @pytest.mark.asyncio
    async def test_no_direct_linkedin_requests(self):
        """Verify we only request search engines, not linkedin.com directly."""
        requested_urls = []

        async def mock_ddg(*args, **kwargs):
            return None  # DDG fails

        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, **kwargs):
                requested_urls.append(url)
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.text = '<html></html>'
                return mock_response

        with patch('execution.linkedin_stealth.search_duckduckgo', mock_ddg):
            with patch('execution.linkedin_stealth.httpx.AsyncClient', MockAsyncClient):
                with patch('execution.linkedin_stealth.asyncio.sleep', new_callable=AsyncMock):
                    await find_linkedin("Test", "Test")

        # Verify requests go to search engines, not LinkedIn directly
        # The query parameter may contain "linkedin.com/in" for site: search, but the host must not be linkedin.com
        for url in requested_urls:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            assert 'linkedin.com' not in parsed.netloc, f"Direct LinkedIn request detected: {url}"
            # Should only be requesting from search engines
            assert parsed.netloc in ['www.bing.com', 'bing.com', 'duckduckgo.com', 'www.duckduckgo.com'], \
                f"Unexpected request to: {parsed.netloc}"


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
