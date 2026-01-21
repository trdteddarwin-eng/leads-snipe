# Email Verification System

## Purpose
Verify email addresses BEFORE sending outreach to avoid bounces, protect sender reputation, and save time on invalid leads.

## Tool
**Script:** `execution/verify_email.py`

## 3-Layer Verification (All FREE)

### Layer 1: Syntax Check
- Valid email format (RFC 5322)
- Filters out image files (.png, .jpg, .webp)
- Catches placeholders (example@email.com, noreply@)
- Detects disposable email domains

### Layer 2: DNS/MX Check  
- Verifies domain exists
- Checks for mail exchange (MX) records
- Identifies dead domains and typos

### Layer 3: SMTP Check
- Connects to mail server
- Asks "does this mailbox exist?"
- Returns definitive yes/no when possible

## Usage

### Single Email Verification
```bash
python3 execution/verify_email.py --email "test@example.com"
```

### Bulk Verification (Leads File)
```bash
python3 execution/verify_email.py --file .tmp/leads.json --output .tmp/verified_leads.json
```

### Skip SMTP (Faster, Less Accurate)
```bash
python3 execution/verify_email.py --file leads.json --no-smtp
```

## Output Format

### Single Email
```json
{
  "email": "test@example.com",
  "valid": true,
  "deliverable": true,
  "reason": "All verification checks passed",
  "checks": {
    "syntax": {"passed": true, "message": "Valid syntax"},
    "mx": {"passed": true, "message": "Found 2 MX record(s)", "servers": ["mx1.example.com"]},
    "smtp": {"passed": true, "message": "Mailbox exists (SMTP verified)"}
  }
}
```

### Bulk Verification
Adds `email_verification` field to each lead:
```json
{
  "name": "Business Name",
  "email": "contact@business.com",
  "email_verification": {
    "valid": true,
    "deliverable": true,
    "reason": "All verification checks passed"
  }
}
```

## What It Catches

| Issue | Detection Layer | Example |
|-------|-----------------|---------|
| Image filenames | Syntax | `logo@2x.png` |
| Placeholder emails | Syntax | `example@email.com` |
| Typos in domain | MX | `test@gmial.com` |
| Dead domains | MX | `info@closed-business.com` |
| Non-existent mailboxes | SMTP | `fake@valid-domain.com` |

## Known Limitations

### SMTP Blocking
Some mail servers (Gmail, Microsoft, 1&1) block SMTP verification:
- They don't reveal if a mailbox exists
- Verification passes but email may still bounce
- ~10-20% of emails may still bounce despite passing

**Workaround:** For critical campaigns, consider a paid verification service like:
- NeverBounce ($0.003/email)
- ZeroBounce ($0.007/email)
- Hunter.io (25 free/month)

### Catch-All Domains
Some domains accept all emails (wildcards):
- `anything@catch-all-domain.com` will pass
- But may not reach a real person

### Temporary Failures
- Server timeouts may cause false negatives
- Run verification again if many "inconclusive" results

## Dependencies

```bash
pip install dnspython
```

Optional but recommended:
```bash
pip install email-validator
```

## Integration with Email Generation

The `generate_outreach_emails.py` script can use this verifier:

```python
from verify_email import verify_email

# Check before generating
result = verify_email(lead["email"])
if not result["deliverable"]:
    print(f"Skipping invalid email: {result['reason']}")
    continue
```

## Cost

**$0** - Uses only:
- Python standard library (smtplib, socket)
- Free dnspython library
- Public DNS lookups

## Best Practices

1. **Always verify before bulk sends** - Protect your sender reputation
2. **Use SMTP check for important campaigns** - More accurate, but slower
3. **Skip SMTP for quick filtering** - Use `--no-smtp` for speed
4. **Monitor bounces anyway** - Some will slip through
5. **Track bounce rates** - If >5%, investigate data source

## Error Codes from SMTP

| Code | Meaning | Action |
|------|---------|--------|
| 250 | Valid | ✅ Send |
| 550 | Mailbox doesn't exist | ❌ Remove |
| 551 | User not local | ❌ Remove |
| 552 | Mailbox full | ⚠️ Try later |
| 553 | Invalid mailbox | ❌ Remove |
| 421 | Server busy | ⚠️ Retry |
| 450/451 | Temporary issue | ⚠️ Retry |
