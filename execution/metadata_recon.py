"""
Metadata Recon - Stealth Hybrid Lead Engine

Extracts organization info from SSL certificates for business identification.
Uses Python stdlib only (ssl, socket) - no external dependencies.

Requirements covered:
- META-01: SSL cert org extraction
- META-02: Org name as business identifier
"""

import asyncio
import ssl
import socket
from dataclasses import dataclass
from typing import Optional


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class CertInfo:
    """SSL certificate information."""
    organization: Optional[str] = None
    organizational_unit: Optional[str] = None
    common_name: Optional[str] = None
    locality: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    issuer: Optional[str] = None
    issuer_org: Optional[str] = None
    error: Optional[str] = None


@dataclass
class MetadataResult:
    """Result of metadata extraction for a domain."""
    hostname: str
    organization: Optional[str] = None
    confidence: str = "none"  # high, medium, low, none
    cert_info: Optional[CertInfo] = None
    error: Optional[str] = None


# =============================================================================
# SSL Certificate Extractor (META-01)
# =============================================================================

class SSLCertExtractor:
    """
    Extracts organization info from SSL certificates.

    Uses Python's ssl module to connect and retrieve certificate data.
    Works with OV (Organization Validated) and EV (Extended Validation) certs.
    DV (Domain Validated) certs typically have no organization info.
    """

    def __init__(
        self,
        timeout: int = 10,
        verify_cert: bool = True
    ):
        self.timeout = timeout
        self.verify_cert = verify_cert

    def extract(self, hostname: str, port: int = 443) -> CertInfo:
        """
        Extract certificate info from a hostname.

        Args:
            hostname: Domain to connect to
            port: SSL port (default 443)

        Returns:
            CertInfo with extracted data or error
        """
        try:
            # Create SSL context
            if self.verify_cert:
                context = ssl.create_default_context()
            else:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            # Connect and get certificate
            with socket.create_connection(
                (hostname, port),
                timeout=self.timeout
            ) as sock:
                with context.wrap_socket(
                    sock,
                    server_hostname=hostname
                ) as ssock:
                    cert = ssock.getpeercert()

            return self._parse_cert(cert)

        except socket.timeout:
            return CertInfo(error="timeout")
        except socket.gaierror as e:
            return CertInfo(error=f"dns_failure: {e}")
        except ConnectionRefusedError:
            return CertInfo(error="connection_refused")
        except ssl.SSLCertVerificationError as e:
            # Try again without verification if it failed
            if self.verify_cert:
                return SSLCertExtractor(
                    timeout=self.timeout,
                    verify_cert=False
                ).extract(hostname, port)
            return CertInfo(error=f"ssl_verification: {e}")
        except ssl.SSLError as e:
            return CertInfo(error=f"ssl_error: {e}")
        except OSError as e:
            return CertInfo(error=f"connection_error: {e}")
        except Exception as e:
            return CertInfo(error=f"unknown_error: {e}")

    def _parse_cert(self, cert: dict) -> CertInfo:
        """Parse certificate dictionary into CertInfo."""
        info = CertInfo()

        # Parse subject fields
        if 'subject' in cert:
            for rdn in cert['subject']:
                for key, value in rdn:
                    if key == 'organizationName':
                        info.organization = value
                    elif key == 'organizationalUnitName':
                        info.organizational_unit = value
                    elif key == 'commonName':
                        info.common_name = value
                    elif key == 'localityName':
                        info.locality = value
                    elif key == 'stateOrProvinceName':
                        info.state = value
                    elif key == 'countryName':
                        info.country = value

        # Parse issuer for context (helps determine cert type)
        if 'issuer' in cert:
            issuer_parts = []
            for rdn in cert['issuer']:
                for key, value in rdn:
                    if key == 'organizationName':
                        info.issuer_org = value
                    if key in ('organizationName', 'commonName'):
                        issuer_parts.append(value)
            info.issuer = ', '.join(issuer_parts) if issuer_parts else None

        return info

    async def extract_async(self, hostname: str, port: int = 443) -> CertInfo:
        """
        Async wrapper for certificate extraction.

        Uses run_in_executor since ssl module is not truly async.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.extract,
            hostname,
            port
        )


# =============================================================================
# Business Identifier & Confidence (META-02)
# =============================================================================

# Common placeholder values to filter out
INVALID_ORG_VALUES = {
    'unknown',
    'none',
    'n/a',
    'not available',
    'domain validated',
    'domain validation',
    'dv',
    'persona not validated',
    'organization not validated',
}

# EV cert issuers (partial list of common ones)
EV_ISSUERS = {
    'digicert',
    'comodo',
    'sectigo',
    'globalsign',
    'entrust',
    'symantec',
    'geotrust',
    'thawte',
    'godaddy',
}


def has_valid_org(cert_info: CertInfo) -> bool:
    """
    Check if certificate has a valid organization name.

    Filters out:
    - Empty/None values
    - Common placeholder values
    - CN duplicated as O (common in DV certs)
    """
    if not cert_info.organization:
        return False

    org = cert_info.organization.strip()

    # Too short to be meaningful
    if len(org) < 3:
        return False

    # Check against invalid values
    if org.lower() in INVALID_ORG_VALUES:
        return False

    # Check if org is just the domain/CN (common in DV certs)
    if cert_info.common_name:
        cn_lower = cert_info.common_name.lower()
        org_lower = org.lower()
        # If org is same as CN or CN contains org, likely not real org
        if org_lower == cn_lower or org_lower in cn_lower:
            return False

    return True


def org_confidence(cert_info: CertInfo) -> str:
    """
    Score confidence in organization name.

    Returns:
        "high" - EV certificate (thorough validation)
        "medium" - OV certificate (organization validated)
        "low" - Has org but uncertain validation
        "none" - No organization info
    """
    if not has_valid_org(cert_info):
        return "none"

    # Check for EV indicators in issuer
    if cert_info.issuer:
        issuer_lower = cert_info.issuer.lower()
        # EV certs often have "extended validation" in issuer
        if 'extended validation' in issuer_lower or 'ev ' in issuer_lower:
            return "high"

    # Check for known EV issuers with EV-specific strings
    if cert_info.issuer_org:
        issuer_org_lower = cert_info.issuer_org.lower()
        for ev_issuer in EV_ISSUERS:
            if ev_issuer in issuer_org_lower:
                # Known issuer, likely OV or EV
                return "medium"

    # Has org but we can't verify cert type
    return "low"


def clean_org_name(org: str) -> str:
    """Clean up organization name for use as identifier."""
    if not org:
        return ""

    # Remove common suffixes
    suffixes = [
        ', Inc.', ', Inc', ' Inc.', ' Inc',
        ', LLC', ' LLC',
        ', Ltd.', ', Ltd', ' Ltd.', ' Ltd',
        ', Corp.', ', Corp', ' Corp.', ' Corp',
        ', Co.', ', Co', ' Co.', ' Co',
    ]

    cleaned = org
    for suffix in suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)]

    return cleaned.strip()


# =============================================================================
# Public API (Task 3.3)
# =============================================================================

async def get_metadata(hostname: str, timeout: int = 10) -> MetadataResult:
    """
    Async API: Get metadata (organization info) for a hostname.

    Args:
        hostname: Domain to check (e.g., "example.com")
        timeout: Connection timeout in seconds

    Returns:
        MetadataResult with organization and confidence
    """
    # Clean hostname
    hostname = hostname.lower().strip()
    hostname = hostname.replace("https://", "").replace("http://", "")
    hostname = hostname.split("/")[0]  # Remove path

    extractor = SSLCertExtractor(timeout=timeout)
    cert_info = await extractor.extract_async(hostname)

    if cert_info.error:
        return MetadataResult(
            hostname=hostname,
            error=cert_info.error,
            cert_info=cert_info
        )

    confidence = org_confidence(cert_info)
    org = None

    if confidence != "none":
        org = clean_org_name(cert_info.organization)

    return MetadataResult(
        hostname=hostname,
        organization=org,
        confidence=confidence,
        cert_info=cert_info
    )


def get_metadata_sync(hostname: str, timeout: int = 10) -> MetadataResult:
    """
    Sync wrapper: Get metadata for a hostname.

    Use from synchronous code.
    """
    return asyncio.run(get_metadata(hostname, timeout))


async def get_metadata_batch(
    hostnames: list[str],
    timeout: int = 10,
    max_concurrent: int = 10
) -> list[MetadataResult]:
    """
    Async API: Get metadata for multiple hostnames.

    Args:
        hostnames: List of domains to check
        timeout: Connection timeout per host
        max_concurrent: Max concurrent connections

    Returns:
        List of MetadataResult in same order as input
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_get(hostname: str) -> MetadataResult:
        async with semaphore:
            return await get_metadata(hostname, timeout)

    tasks = [limited_get(h) for h in hostnames]
    return await asyncio.gather(*tasks)


def get_metadata_batch_sync(
    hostnames: list[str],
    timeout: int = 10,
    max_concurrent: int = 10
) -> list[MetadataResult]:
    """Sync wrapper for batch metadata extraction."""
    return asyncio.run(get_metadata_batch(hostnames, timeout, max_concurrent))


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python metadata_recon.py hostname [hostname2 ...]")
        print("\nExample:")
        print("  python metadata_recon.py google.com")
        print("  python metadata_recon.py apple.com microsoft.com amazon.com")
        sys.exit(1)

    hostnames = sys.argv[1:]

    print(f"\nExtracting SSL metadata for {len(hostnames)} host(s)...\n")
    print("=" * 70)

    for hostname in hostnames:
        result = get_metadata_sync(hostname)

        print(f"\n{hostname}")
        print("-" * 40)

        if result.error:
            print(f"  Error: {result.error}")
        else:
            print(f"  Organization: {result.organization or '(none)'}")
            print(f"  Confidence:   {result.confidence}")

            if result.cert_info:
                ci = result.cert_info
                if ci.locality or ci.state or ci.country:
                    location = ", ".join(filter(None, [ci.locality, ci.state, ci.country]))
                    print(f"  Location:     {location}")
                if ci.issuer_org:
                    print(f"  Issuer:       {ci.issuer_org}")

    print("\n" + "=" * 70)

    # Summary
    with_org = sum(1 for r in [get_metadata_sync(h) for h in hostnames]
                   if r.organization)
    print(f"\nSummary: {with_org}/{len(hostnames)} hosts have organization info")
