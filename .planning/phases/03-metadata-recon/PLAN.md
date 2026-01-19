# Phase 3 Plan: Metadata Recon

**Phase:** 3 of 7
**Goal:** Extract organization info from SSL certificates
**Output:** `execution/metadata_recon.py`

## Requirements Coverage

| Requirement | Task | Status |
|-------------|------|--------|
| META-01: SSL cert org extraction | Task 3.1 | ✓ Complete |
| META-02: Org name as business identifier | Task 3.2 | ✓ Complete |

## Implementation Plan

### Wave 1: Core Extraction

#### Task 3.1: SSL Certificate Extractor
**File:** `execution/metadata_recon.py`
**Requirement:** META-01

Create `SSLCertExtractor` class:

```python
@dataclass
class CertInfo:
    organization: Optional[str]
    organizational_unit: Optional[str]
    common_name: Optional[str]
    locality: Optional[str]
    state: Optional[str]
    country: Optional[str]
    issuer: Optional[str]
    error: Optional[str]

class SSLCertExtractor:
    async def extract(self, hostname: str) -> CertInfo
```

**Implementation:**
1. Create SSL context with default settings
2. Connect to hostname:443 with 10s timeout
3. Extract certificate via getpeercert()
4. Parse subject fields (O, OU, CN, L, ST, C)
5. Parse issuer for cert type context
6. Handle errors gracefully (timeout, DNS, SSL errors)
7. Use run_in_executor for async compatibility

**Acceptance:**
- [ ] Extracts org from OV/EV certificates
- [ ] Returns None for DV certs (no org info)
- [ ] Handles connection errors gracefully
- [ ] Works with self-signed certs (optional flag)

---

#### Task 3.2: Business Identifier & Confidence
**File:** `execution/metadata_recon.py`
**Requirement:** META-02

Add org validation and confidence scoring:

```python
def has_valid_org(cert_info: CertInfo) -> bool
def org_confidence(cert_info: CertInfo) -> str
```

**Implementation:**
1. Validate org is not empty/placeholder
2. Filter out common non-org values (unknown, none, CN duplicates)
3. Score confidence based on cert type (EV=high, OV=medium)
4. Return structured result with org + confidence

**Acceptance:**
- [ ] Identifies valid org names
- [ ] Filters placeholder values
- [ ] Returns confidence level
- [ ] Gracefully handles missing org

---

### Wave 2: Integration & Testing

#### Task 3.3: Public API
**File:** `execution/metadata_recon.py`

Create clean public API:

```python
@dataclass
class MetadataResult:
    hostname: str
    organization: Optional[str]
    confidence: str  # high, medium, low, none
    cert_info: CertInfo

async def get_metadata(hostname: str) -> MetadataResult
def get_metadata_sync(hostname: str) -> MetadataResult
```

**Implementation:**
1. Top-level function combining extractor + validator
2. Sync wrapper using asyncio.run()
3. CLI interface for testing

**Acceptance:**
- [ ] Single function returns all metadata
- [ ] Sync wrapper works from non-async code
- [ ] CLI: `python metadata_recon.py example.com`

---

#### Task 3.4: Unit Tests
**File:** `execution/test_metadata_recon.py`

**Test Cases:**
1. `test_extract_ov_cert` - Extracts org from OV certificate
2. `test_extract_ev_cert` - Extracts org from EV certificate
3. `test_extract_dv_cert` - Returns None for DV cert
4. `test_handle_timeout` - Handles connection timeout
5. `test_handle_dns_failure` - Handles DNS failure
6. `test_handle_ssl_error` - Handles SSL errors
7. `test_confidence_scoring` - Correct confidence levels
8. `test_filter_placeholders` - Filters invalid org names

**Implementation:**
- Mock ssl.SSLSocket for unit tests
- Use real connections for optional integration tests

---

## Execution Order

```
Wave 1 (Sequential):
  Task 3.1 → Task 3.2

Wave 2 (Sequential, after Wave 1):
  Task 3.3 → Task 3.4
```

## Success Criteria Verification

| Criterion | How to Verify |
|-----------|---------------|
| Extracts org from OV/EV | Test against known OV/EV domains |
| Handles DV certs | Test against Let's Encrypt domains |
| Graceful error handling | Test with invalid/unreachable hosts |
| Org name usable as identifier | Integration with lead enrichment |

## Dependencies

```
# Uses Python stdlib only
ssl
socket
asyncio
```

No external packages required.

## Risks & Mitigations

| Risk | Mitigation | Task |
|------|------------|------|
| Most certs are DV | Graceful None return, supplementary data | 3.1 |
| SSL handshake slow | 10s timeout, async wrapper | 3.1 |
| Self-signed certs | Optional verify_mode flag | 3.1 |

## Notes

This phase is lightweight (2 requirements, stdlib only) because:
1. SSL org info is supplementary, not primary discovery
2. Only 30-40% of domains have OV/EV certs
3. Simple extraction, no complex parsing needed

The extracted org name feeds into Phase 6 (Pipeline Integration) as a validation/fallback signal.

---
*Plan created: 2026-01-18*
