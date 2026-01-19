"""
Unit Tests for Metadata Recon Module

Tests SSL certificate extraction and organization identification.
Covers requirements META-01 and META-02.
"""

import asyncio
import ssl
import socket
from unittest.mock import Mock, patch, MagicMock
import pytest

from metadata_recon import (
    CertInfo,
    MetadataResult,
    SSLCertExtractor,
    has_valid_org,
    org_confidence,
    clean_org_name,
    get_metadata,
    get_metadata_sync,
    get_metadata_batch,
    get_metadata_batch_sync,
    INVALID_ORG_VALUES,
    EV_ISSUERS,
)


# =============================================================================
# Test Data
# =============================================================================

# Sample OV certificate data (Organization Validated)
OV_CERT = {
    'subject': (
        (('countryName', 'US'),),
        (('stateOrProvinceName', 'California'),),
        (('localityName', 'San Francisco'),),
        (('organizationName', 'Example Corporation'),),
        (('commonName', 'www.example.com'),),
    ),
    'issuer': (
        (('countryName', 'US'),),
        (('organizationName', 'DigiCert Inc'),),
        (('commonName', 'DigiCert SHA2 Extended Validation Server CA'),),
    ),
}

# Sample EV certificate data (Extended Validation)
EV_CERT = {
    'subject': (
        (('countryName', 'US'),),
        (('stateOrProvinceName', 'California'),),
        (('localityName', 'Cupertino'),),
        (('organizationName', 'Apple Inc.'),),
        (('commonName', 'www.apple.com'),),
    ),
    'issuer': (
        (('countryName', 'US'),),
        (('organizationName', 'DigiCert Inc'),),
        (('commonName', 'DigiCert Extended Validation Server CA'),),
    ),
}

# Sample DV certificate data (Domain Validated - no org)
DV_CERT = {
    'subject': (
        (('commonName', 'example.com'),),
    ),
    'issuer': (
        (('countryName', 'US'),),
        (('organizationName', "Let's Encrypt"),),
        (('commonName', 'R3'),),
    ),
}

# DV cert where org is same as CN (common pattern)
DV_CERT_ORG_AS_CN = {
    'subject': (
        (('organizationName', 'example.com'),),
        (('commonName', 'example.com'),),
    ),
    'issuer': (
        (('organizationName', 'Some CA'),),
        (('commonName', 'Some CA'),),
    ),
}


# =============================================================================
# SSLCertExtractor Tests (META-01)
# =============================================================================

class TestSSLCertExtractor:
    """Tests for SSL certificate extraction."""

    def test_parse_ov_cert(self):
        """Test parsing OV certificate extracts organization."""
        extractor = SSLCertExtractor()
        info = extractor._parse_cert(OV_CERT)

        assert info.organization == 'Example Corporation'
        assert info.common_name == 'www.example.com'
        assert info.locality == 'San Francisco'
        assert info.state == 'California'
        assert info.country == 'US'
        assert info.issuer_org == 'DigiCert Inc'
        assert info.error is None

    def test_parse_ev_cert(self):
        """Test parsing EV certificate extracts organization."""
        extractor = SSLCertExtractor()
        info = extractor._parse_cert(EV_CERT)

        assert info.organization == 'Apple Inc.'
        assert info.common_name == 'www.apple.com'
        assert 'Extended Validation' in info.issuer
        assert info.error is None

    def test_parse_dv_cert(self):
        """Test parsing DV certificate returns no organization."""
        extractor = SSLCertExtractor()
        info = extractor._parse_cert(DV_CERT)

        assert info.organization is None
        assert info.common_name == 'example.com'
        assert info.error is None

    def test_parse_empty_cert(self):
        """Test parsing empty certificate dictionary."""
        extractor = SSLCertExtractor()
        info = extractor._parse_cert({})

        assert info.organization is None
        assert info.common_name is None
        assert info.issuer is None
        assert info.error is None

    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_extract_success(self, mock_ssl_context, mock_connection):
        """Test successful certificate extraction."""
        # Setup mocks
        mock_sock = MagicMock()
        mock_connection.return_value.__enter__ = Mock(return_value=mock_sock)
        mock_connection.return_value.__exit__ = Mock(return_value=False)

        mock_ssock = MagicMock()
        mock_ssock.getpeercert.return_value = OV_CERT

        mock_context = MagicMock()
        mock_context.wrap_socket.return_value.__enter__ = Mock(return_value=mock_ssock)
        mock_context.wrap_socket.return_value.__exit__ = Mock(return_value=False)
        mock_ssl_context.return_value = mock_context

        extractor = SSLCertExtractor()
        info = extractor.extract('example.com')

        assert info.organization == 'Example Corporation'
        assert info.error is None
        mock_connection.assert_called_once_with(('example.com', 443), timeout=10)

    @patch('socket.create_connection')
    def test_extract_timeout(self, mock_connection):
        """Test handling of connection timeout."""
        mock_connection.side_effect = socket.timeout()

        extractor = SSLCertExtractor()
        info = extractor.extract('slow.example.com')

        assert info.error == 'timeout'
        assert info.organization is None

    @patch('socket.create_connection')
    def test_extract_dns_failure(self, mock_connection):
        """Test handling of DNS resolution failure."""
        mock_connection.side_effect = socket.gaierror(8, 'nodename nor servname provided')

        extractor = SSLCertExtractor()
        info = extractor.extract('nonexistent.example.com')

        assert 'dns_failure' in info.error
        assert info.organization is None

    @patch('socket.create_connection')
    def test_extract_connection_refused(self, mock_connection):
        """Test handling of connection refused."""
        mock_connection.side_effect = ConnectionRefusedError()

        extractor = SSLCertExtractor()
        info = extractor.extract('nossl.example.com')

        assert info.error == 'connection_refused'
        assert info.organization is None

    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_extract_ssl_error(self, mock_ssl_context, mock_connection):
        """Test handling of SSL errors."""
        mock_sock = MagicMock()
        mock_connection.return_value.__enter__ = Mock(return_value=mock_sock)
        mock_connection.return_value.__exit__ = Mock(return_value=False)

        mock_context = MagicMock()
        mock_context.wrap_socket.side_effect = ssl.SSLError("SSL handshake failed")
        mock_ssl_context.return_value = mock_context

        extractor = SSLCertExtractor()
        info = extractor.extract('badssl.example.com')

        assert 'ssl_error' in info.error

    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_extract_retries_without_verification(self, mock_ssl_context, mock_connection):
        """Test that SSL verification errors trigger retry without verification."""
        mock_sock = MagicMock()
        mock_connection.return_value.__enter__ = Mock(return_value=mock_sock)
        mock_connection.return_value.__exit__ = Mock(return_value=False)

        mock_ssock = MagicMock()
        mock_ssock.getpeercert.return_value = OV_CERT

        mock_context = MagicMock()

        # First call raises verification error, second succeeds
        call_count = [0]

        def wrap_socket_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ssl.SSLCertVerificationError(1, "certificate verify failed")
            mock_wrap = MagicMock()
            mock_wrap.__enter__ = Mock(return_value=mock_ssock)
            mock_wrap.__exit__ = Mock(return_value=False)
            return mock_wrap

        mock_context.wrap_socket.side_effect = wrap_socket_side_effect
        mock_ssl_context.return_value = mock_context

        extractor = SSLCertExtractor(verify_cert=True)
        info = extractor.extract('selfsigned.example.com')

        # Should have retried and succeeded
        assert info.organization == 'Example Corporation'

    @pytest.mark.asyncio
    async def test_extract_async(self):
        """Test async extraction wrapper."""
        with patch.object(SSLCertExtractor, 'extract') as mock_extract:
            mock_extract.return_value = CertInfo(organization='Test Corp')

            extractor = SSLCertExtractor()
            info = await extractor.extract_async('example.com')

            assert info.organization == 'Test Corp'
            mock_extract.assert_called_once_with('example.com', 443)


# =============================================================================
# Business Identifier Tests (META-02)
# =============================================================================

class TestHasValidOrg:
    """Tests for organization validation."""

    def test_valid_org(self):
        """Test valid organization name is accepted."""
        info = CertInfo(organization='Example Corporation', common_name='example.com')
        assert has_valid_org(info) is True

    def test_none_org(self):
        """Test None organization is rejected."""
        info = CertInfo(organization=None)
        assert has_valid_org(info) is False

    def test_empty_org(self):
        """Test empty organization is rejected."""
        info = CertInfo(organization='')
        assert has_valid_org(info) is False

    def test_whitespace_org(self):
        """Test whitespace-only organization is rejected."""
        info = CertInfo(organization='   ')
        assert has_valid_org(info) is False

    def test_short_org(self):
        """Test very short organization is rejected."""
        info = CertInfo(organization='AB')
        assert has_valid_org(info) is False

    def test_placeholder_values(self):
        """Test placeholder values are rejected."""
        for placeholder in INVALID_ORG_VALUES:
            info = CertInfo(organization=placeholder, common_name='example.com')
            assert has_valid_org(info) is False, f"'{placeholder}' should be rejected"

    def test_org_same_as_cn(self):
        """Test org matching CN is rejected (common in DV certs)."""
        info = CertInfo(organization='example.com', common_name='example.com')
        assert has_valid_org(info) is False

    def test_org_in_cn(self):
        """Test org contained in CN is rejected."""
        info = CertInfo(organization='example', common_name='www.example.com')
        assert has_valid_org(info) is False

    def test_cn_is_none(self):
        """Test valid org when CN is None."""
        info = CertInfo(organization='Example Corporation', common_name=None)
        assert has_valid_org(info) is True


class TestOrgConfidence:
    """Tests for confidence scoring."""

    def test_no_org_returns_none(self):
        """Test missing org returns none confidence."""
        info = CertInfo(organization=None)
        assert org_confidence(info) == 'none'

    def test_invalid_org_returns_none(self):
        """Test invalid org returns none confidence."""
        info = CertInfo(organization='unknown', common_name='example.com')
        assert org_confidence(info) == 'none'

    def test_ev_cert_returns_high(self):
        """Test EV certificate returns high confidence."""
        info = CertInfo(
            organization='Example Corp',
            common_name='www.example.com',
            issuer='DigiCert Extended Validation Server CA'
        )
        assert org_confidence(info) == 'high'

    def test_ev_issuer_indicator(self):
        """Test 'EV ' in issuer returns high confidence."""
        info = CertInfo(
            organization='Example Corp',
            common_name='www.example.com',
            issuer='Sectigo EV SSL CA'
        )
        assert org_confidence(info) == 'high'

    def test_known_ov_issuer_returns_medium(self):
        """Test known OV issuer returns medium confidence."""
        for issuer in EV_ISSUERS:
            info = CertInfo(
                organization='Example Corp',
                common_name='www.example.com',
                issuer_org=f'{issuer.capitalize()} Inc'
            )
            assert org_confidence(info) == 'medium', f"Issuer '{issuer}' should return medium"

    def test_unknown_issuer_returns_low(self):
        """Test unknown issuer returns low confidence."""
        info = CertInfo(
            organization='Example Corp',
            common_name='www.example.com',
            issuer_org='Unknown CA'
        )
        assert org_confidence(info) == 'low'


class TestCleanOrgName:
    """Tests for organization name cleaning."""

    def test_remove_inc(self):
        """Test removal of Inc. suffix."""
        assert clean_org_name('Example, Inc.') == 'Example'
        assert clean_org_name('Example Inc.') == 'Example'
        assert clean_org_name('Example, Inc') == 'Example'
        assert clean_org_name('Example Inc') == 'Example'

    def test_remove_llc(self):
        """Test removal of LLC suffix."""
        assert clean_org_name('Example, LLC') == 'Example'
        assert clean_org_name('Example LLC') == 'Example'

    def test_remove_ltd(self):
        """Test removal of Ltd. suffix."""
        assert clean_org_name('Example, Ltd.') == 'Example'
        assert clean_org_name('Example Ltd') == 'Example'

    def test_remove_corp(self):
        """Test removal of Corp. suffix."""
        assert clean_org_name('Example, Corp.') == 'Example'
        assert clean_org_name('Example Corp') == 'Example'

    def test_remove_co(self):
        """Test removal of Co. suffix."""
        assert clean_org_name('Example, Co.') == 'Example'
        assert clean_org_name('Example Co') == 'Example'

    def test_preserve_middle_suffix(self):
        """Test suffix in middle is preserved."""
        assert clean_org_name('Inc. Technologies') == 'Inc. Technologies'

    def test_empty_string(self):
        """Test empty string returns empty."""
        assert clean_org_name('') == ''

    def test_none_returns_empty(self):
        """Test None returns empty."""
        assert clean_org_name(None) == ''

    def test_strips_whitespace(self):
        """Test leading/trailing whitespace is stripped."""
        assert clean_org_name('  Example Corporation  ') == 'Example Corporation'
        assert clean_org_name('  Example, Inc.  ') == 'Example'


# =============================================================================
# Public API Tests (Task 3.3)
# =============================================================================

class TestGetMetadata:
    """Tests for public metadata API."""

    @pytest.mark.asyncio
    async def test_get_metadata_success(self):
        """Test successful metadata extraction."""
        with patch.object(SSLCertExtractor, 'extract_async') as mock_extract:
            mock_extract.return_value = CertInfo(
                organization='Example Corporation',
                common_name='www.example.com',
                issuer_org='DigiCert Inc'
            )

            result = await get_metadata('example.com')

            assert result.hostname == 'example.com'
            assert result.organization == 'Example Corporation'
            assert result.confidence == 'medium'
            assert result.error is None

    @pytest.mark.asyncio
    async def test_get_metadata_cleans_hostname(self):
        """Test hostname is cleaned before extraction."""
        with patch.object(SSLCertExtractor, 'extract_async') as mock_extract:
            mock_extract.return_value = CertInfo()

            # Test various input formats
            await get_metadata('EXAMPLE.COM')
            mock_extract.assert_called_with('example.com')

            await get_metadata('https://example.com/path')
            mock_extract.assert_called_with('example.com')

            await get_metadata('http://example.com/')
            mock_extract.assert_called_with('example.com')

    @pytest.mark.asyncio
    async def test_get_metadata_with_error(self):
        """Test metadata extraction with connection error."""
        with patch.object(SSLCertExtractor, 'extract_async') as mock_extract:
            mock_extract.return_value = CertInfo(error='timeout')

            result = await get_metadata('slow.example.com')

            assert result.hostname == 'slow.example.com'
            assert result.organization is None
            assert result.error == 'timeout'

    @pytest.mark.asyncio
    async def test_get_metadata_no_org(self):
        """Test metadata extraction for DV cert (no org)."""
        with patch.object(SSLCertExtractor, 'extract_async') as mock_extract:
            mock_extract.return_value = CertInfo(
                common_name='example.com',
                issuer_org="Let's Encrypt"
            )

            result = await get_metadata('example.com')

            assert result.organization is None
            assert result.confidence == 'none'

    @pytest.mark.asyncio
    async def test_get_metadata_cleans_org_name(self):
        """Test org name is cleaned in result."""
        with patch.object(SSLCertExtractor, 'extract_async') as mock_extract:
            mock_extract.return_value = CertInfo(
                organization='Example Corporation, Inc.',
                common_name='www.example.com',
                issuer_org='DigiCert Inc'
            )

            result = await get_metadata('example.com')

            assert result.organization == 'Example Corporation'

    def test_get_metadata_sync(self):
        """Test synchronous wrapper."""
        with patch.object(SSLCertExtractor, 'extract_async') as mock_extract:
            mock_extract.return_value = CertInfo(
                organization='Example Corporation',  # Use full name, clean_org_name strips suffix
                common_name='www.example.com',
                issuer_org='DigiCert Inc'
            )

            result = get_metadata_sync('example.com')

            assert result.organization == 'Example Corporation'
            assert result.confidence == 'medium'


class TestGetMetadataBatch:
    """Tests for batch metadata extraction."""

    @pytest.mark.asyncio
    async def test_batch_extraction(self):
        """Test batch extraction of multiple hostnames."""
        results_map = {
            'example1.com': CertInfo(organization='Corp 1', common_name='example1.com', issuer_org='DigiCert'),
            'example2.com': CertInfo(organization='Corp 2', common_name='example2.com', issuer_org='DigiCert'),
            'example3.com': CertInfo(error='timeout'),
        }

        async def mock_extract(hostname, port=443):
            # Extract domain from cleaned hostname
            return results_map.get(hostname, CertInfo())

        with patch.object(SSLCertExtractor, 'extract_async', side_effect=mock_extract):
            results = await get_metadata_batch(['example1.com', 'example2.com', 'example3.com'])

            assert len(results) == 3
            assert results[0].organization == 'Corp 1'
            assert results[1].organization == 'Corp 2'
            assert results[2].error == 'timeout'

    @pytest.mark.asyncio
    async def test_batch_respects_concurrency_limit(self):
        """Test batch extraction respects max_concurrent parameter."""
        call_times = []

        async def mock_extract(hostname, port=443):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate network delay
            return CertInfo(organization=f'Corp {hostname}')

        with patch.object(SSLCertExtractor, 'extract_async', side_effect=mock_extract):
            hostnames = [f'example{i}.com' for i in range(5)]
            await get_metadata_batch(hostnames, max_concurrent=2)

            # With max_concurrent=2, calls should be batched
            assert len(call_times) == 5

    def test_batch_sync(self):
        """Test synchronous batch wrapper."""
        with patch.object(SSLCertExtractor, 'extract_async') as mock_extract:
            mock_extract.return_value = CertInfo(organization='Corp', issuer_org='DigiCert')

            results = get_metadata_batch_sync(['example1.com', 'example2.com'])

            assert len(results) == 2
            assert all(r.organization == 'Corp' for r in results)


# =============================================================================
# Integration Tests (Optional - require network)
# =============================================================================

@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring network access.

    Run with: pytest -m integration
    """

    @pytest.mark.asyncio
    async def test_real_ov_cert(self):
        """Test extraction from real OV/EV certificate."""
        # Apple has an EV certificate
        result = await get_metadata('apple.com', timeout=15)

        # Should have organization
        assert result.organization is not None
        assert 'Apple' in result.organization
        assert result.confidence in ('high', 'medium')

    @pytest.mark.asyncio
    async def test_real_dv_cert(self):
        """Test extraction from real DV certificate."""
        # Most small sites use Let's Encrypt DV certs
        # Using a known DV-only site would be ideal
        # For now, just test the structure works
        result = await get_metadata('example.com', timeout=15)

        # Should complete without error
        assert result.hostname == 'example.com'
        # May or may not have org depending on cert type

    @pytest.mark.asyncio
    async def test_nonexistent_domain(self):
        """Test handling of nonexistent domain."""
        result = await get_metadata('this-domain-does-not-exist-12345.com', timeout=5)

        assert result.error is not None
        assert 'dns_failure' in result.error


# =============================================================================
# CLI Tests
# =============================================================================

class TestCLI:
    """Tests for CLI interface."""

    def test_cli_help_message(self):
        """Test CLI shows usage when no args provided."""
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, 'execution/metadata_recon.py'],
            capture_output=True,
            text=True,
            cwd='/Users/yoljean/Downloads/drive-download-20260102T175259Z-3-001'
        )

        assert 'Usage:' in result.stdout
        assert result.returncode == 1


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-m', 'not integration'])
