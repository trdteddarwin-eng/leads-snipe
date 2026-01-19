# Phase 3 Research: Metadata Recon

## Objective

Extract organization info from SSL certificates to identify business names.

## SSL Certificate Organization Field

### What's in an SSL Cert

SSL certificates (especially OV and EV certs) contain organization info in the Subject field:

```
Subject: C=US, ST=California, L=San Francisco, O=Example Corp, CN=example.com
```

Key fields:
- **O** (Organization): Company legal name
- **OU** (Organizational Unit): Department (often missing)
- **L** (Locality): City
- **ST** (State): State/Province
- **C** (Country): 2-letter country code

### Certificate Types and Organization Data

| Type | Has Org | Validation |
|------|---------|------------|
| DV (Domain Validation) | ❌ No | Just proves domain ownership |
| OV (Organization Validation) | ✓ Yes | Verifies company exists |
| EV (Extended Validation) | ✓ Yes | Thorough company verification |

**Reality:** Most small business sites use DV certs (Let's Encrypt, etc.) which have NO organization info. OV/EV certs are more common for larger companies, banks, and e-commerce sites.

## Python SSL Certificate Extraction

### Using stdlib ssl + socket

```python
import ssl
import socket
from dataclasses import dataclass
from typing import Optional

@dataclass
class CertInfo:
    organization: Optional[str] = None
    organizational_unit: Optional[str] = None
    common_name: Optional[str] = None
    locality: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    issuer: Optional[str] = None

def get_ssl_cert_info(hostname: str, port: int = 443) -> CertInfo:
    """Extract organization info from SSL certificate."""
    context = ssl.create_default_context()

    with socket.create_connection((hostname, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()

    info = CertInfo()

    # Parse subject
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

    # Parse issuer for additional context
    if 'issuer' in cert:
        for rdn in cert['issuer']:
            for key, value in rdn:
                if key == 'organizationName':
                    info.issuer = value
                    break

    return info
```

### Async Version

```python
import asyncio
import ssl
import socket

async def get_ssl_cert_async(hostname: str, port: int = 443) -> CertInfo:
    """Async wrapper for SSL cert extraction."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_ssl_cert_info, hostname, port)
```

Note: Python's ssl module doesn't have true async support. We use run_in_executor to avoid blocking the event loop.

## Handling Edge Cases

### No Organization (DV Certs)

```python
def has_organization(cert_info: CertInfo) -> bool:
    """Check if cert has meaningful org info."""
    return bool(cert_info.organization and
                cert_info.organization not in [
                    'unknown',
                    'none',
                    cert_info.common_name  # Sometimes CN is duplicated as O
                ])
```

### Self-Signed Certificates

```python
def extract_safe(hostname: str) -> CertInfo:
    """Extract cert info, handling self-signed certs."""
    try:
        # First try with verification
        return get_ssl_cert_info(hostname)
    except ssl.SSLCertVerificationError:
        # Try without verification for self-signed
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # ... extract anyway
```

### Connection Failures

```python
def extract_with_fallback(hostname: str) -> CertInfo:
    """Extract with graceful fallback."""
    try:
        return get_ssl_cert_info(hostname)
    except socket.timeout:
        return CertInfo(error="timeout")
    except socket.gaierror:
        return CertInfo(error="dns_failure")
    except ConnectionRefusedError:
        return CertInfo(error="connection_refused")
    except ssl.SSLError as e:
        return CertInfo(error=f"ssl_error: {e}")
```

## Use as Business Identifier

### Confidence Scoring

```python
def org_confidence(cert_info: CertInfo) -> str:
    """Score confidence in organization name."""
    if not cert_info.organization:
        return "none"

    # EV certs usually have full legal name
    if cert_info.issuer and "extended" in cert_info.issuer.lower():
        return "high"

    # OV certs are generally reliable
    if cert_info.organization and len(cert_info.organization) > 3:
        return "medium"

    return "low"
```

### Matching to Lead Data

Use org name to:
1. Validate company name from other sources
2. Fill in missing company name
3. Build email patterns (e.g., john@{org-derived-domain}.com)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   MetadataRecon                          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐                   │
│  │    SSL       │    │   CertInfo   │                   │
│  │  Extractor   │───▶│   Parser     │                   │
│  └──────────────┘    └──────────────┘                   │
│          │                   │                          │
│          ▼                   ▼                          │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │   Async      │    │  Confidence  │                   │
│  │   Wrapper    │    │   Scoring    │                   │
│  └──────────────┘    └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## Expected Results

Based on research:
- **30-40%** of business domains have OV/EV certs with org info
- **60-70%** use DV certs (no org info)
- Larger companies more likely to have org info

This is a **supplementary** discovery method, not primary.

## Dependencies

Uses Python stdlib only:
- `ssl`
- `socket`
- `asyncio`

No external packages needed.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Most certs are DV (no org) | Return gracefully, use as supplementary data |
| SSL handshake timeouts | Set 10s timeout, return error gracefully |
| Self-signed certs | Option to skip verification |
| IPv6-only hosts | Try IPv4 first, fallback to IPv6 |

---
*Research completed: 2026-01-18*
