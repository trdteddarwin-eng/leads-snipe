#!/usr/bin/env python3
"""
Free Email Verification System

3-layer verification without paid APIs:
1. Syntax Check - Valid email format
2. DNS/MX Check - Domain has mail servers
3. SMTP Check - Mailbox exists (when possible)

Usage:
    python3 execution/verify_email.py --email "test@example.com"
    python3 execution/verify_email.py --file leads.json --output verified_leads.json
"""

import os
import re
import sys
import json
import socket
import argparse
import smtplib
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# Try to import dns.resolver, fall back to socket-based lookup
try:
    import dns.resolver
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False
    print("Note: dnspython not installed. Using socket-based MX lookup (less accurate).")


# Email regex pattern (RFC 5322 simplified)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Known invalid or technical patterns (system emails, hashes, placeholders)
INVALID_PATTERNS = [
    r'\.(png|jpg|jpeg|gif|svg|webp|pdf|doc|docx|xls|xlsx)$',  # Files
    r'^example@', r'@example\.', r'@test\.', r'@sample\.',        # Placeholders
    r'^info@example', r'^test@test', r'^user@domain',
    r'^noreply@', r'^no-reply@', r'^donotreply@', r'^do-not-reply@',
    r'^mailer-daemon@', r'^postmaster@', r'^abuse@', r'^webmaster@',
    r'sentry', r'wixpress', r'aws', r'amazon', r'notification', r'alert',
    r'bounce', r'replies', r'autosave',
    r'[a-f0-9]{20,}', # Catch long hex hashes (common in technical emails)
    r'\+.*@', # Catch sub-addressing/aliases if we want clean emails
]

# Common disposable email domains
DISPOSABLE_DOMAINS = [
    'tempmail.com', 'throwaway.email', 'guerrillamail.com',
    'mailinator.com', '10minutemail.com', 'temp-mail.org'
]


def check_syntax(email: str) -> Tuple[bool, str]:
    """
    Layer 1: Check if email has valid syntax.
    
    Returns: (is_valid, reason)
    """
    if not email or not isinstance(email, str):
        return False, "Empty or invalid input"
    
    email = email.strip().lower()
    
    # Check basic format
    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format"
    
    # Check for known invalid patterns (images, placeholders)
    for pattern in INVALID_PATTERNS:
        if re.search(pattern, email, re.IGNORECASE):
            return False, f"Matches invalid pattern: {pattern}"
    
    # Check for disposable domains
    domain = email.split('@')[1]
    if domain in DISPOSABLE_DOMAINS:
        return False, "Disposable email domain"
    
    return True, "Valid syntax"


def get_mx_records(domain: str) -> List[str]:
    """
    Get MX (mail exchange) records for a domain.
    
    Returns list of mail server hostnames, sorted by priority.
    """
    mx_records = []
    
    if HAS_DNSPYTHON:
        try:
            answers = dns.resolver.resolve(domain, 'MX')
            mx_records = sorted(
                [(r.preference, str(r.exchange).rstrip('.')) for r in answers],
                key=lambda x: x[0]
            )
            return [mx[1] for mx in mx_records]
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return []
        except Exception:
            return []
    else:
        # Fallback: try to get MX via socket (less reliable)
        try:
            # Try common mail server prefixes
            for prefix in ['mail', 'smtp', 'mx', 'mx1']:
                try:
                    socket.gethostbyname(f'{prefix}.{domain}')
                    mx_records.append(f'{prefix}.{domain}')
                except socket.gaierror:
                    continue
            
            # If no MX found, try the domain itself (might accept mail)
            if not mx_records:
                try:
                    socket.gethostbyname(domain)
                    mx_records.append(domain)
                except socket.gaierror:
                    pass
                    
            return mx_records
        except Exception:
            return []


def check_mx(email: str) -> Tuple[bool, str, List[str]]:
    """
    Layer 2: Check if domain has valid MX records.
    
    Returns: (has_mx, reason, mx_servers)
    """
    try:
        domain = email.split('@')[1]
    except IndexError:
        return False, "Invalid email format", []
    
    mx_records = get_mx_records(domain)
    
    if mx_records:
        return True, f"Found {len(mx_records)} MX record(s)", mx_records
    else:
        # Try A record as fallback (some domains accept mail without MX)
        try:
            socket.gethostbyname(domain)
            return True, "No MX records, but domain resolves (may accept mail)", [domain]
        except socket.gaierror:
            return False, "Domain has no MX records and doesn't resolve", []


def check_smtp(email: str, mx_servers: List[str], timeout: int = 10) -> Tuple[bool, str]:
    """
    Layer 3: Verify email exists via SMTP handshake.
    
    This connects to the mail server and asks if the mailbox exists.
    Some servers block this (always return OK or always reject).
    
    Returns: (is_valid, reason)
    """
    if not mx_servers:
        return False, "No mail servers to check"
    
    # Use a fake sender address for verification
    sender_address = "verify@gmail.com"
    
    for mx_server in mx_servers[:2]:  # Try first 2 MX servers
        try:
            # Connect to SMTP server
            smtp = smtplib.SMTP(timeout=timeout)
            smtp.set_debuglevel(0)  # Suppress debug output
            
            try:
                smtp.connect(mx_server, 25)
            except (socket.timeout, socket.error, smtplib.SMTPException):
                # Try port 587 as fallback
                try:
                    smtp.connect(mx_server, 587)
                except:
                    continue
            
            # Send HELO
            smtp.helo('gmail.com')
            
            # Try MAIL FROM
            code, _ = smtp.mail(sender_address)
            if code != 250:
                smtp.quit()
                continue
            
            # Try RCPT TO (this is where we verify the email)
            code, message = smtp.rcpt(email)
            smtp.quit()
            
            if code == 250:
                return True, "Mailbox exists (SMTP verified)"
            elif code == 550:
                return False, "Mailbox does not exist (550 rejection)"
            elif code == 551:
                return False, "User not local (551)"
            elif code == 552:
                return False, "Mailbox full (552)"
            elif code == 553:
                return False, "Mailbox name invalid (553)"
            elif code == 450 or code == 451:
                return True, "Temporary issue, but mailbox likely exists"
            else:
                # 421, 452, etc. - server issues, assume valid
                return True, f"Inconclusive (code {code}), assuming valid"
                
        except smtplib.SMTPServerDisconnected:
            continue
        except smtplib.SMTPConnectError:
            continue
        except socket.timeout:
            continue
        except Exception as e:
            continue
    
    # If SMTP check failed on all servers, assume valid (some servers block this)
    return True, "SMTP check blocked/failed, assuming valid based on MX"


def verify_email(email: str, do_smtp_check: bool = True) -> Dict:
    """
    Full email verification using all 3 layers.
    
    Args:
        email: Email address to verify
        do_smtp_check: Whether to perform SMTP verification (slower but more accurate)
        
    Returns:
        {
            "email": str,
            "valid": bool,
            "deliverable": bool,
            "reason": str,
            "checks": {
                "syntax": {"passed": bool, "message": str},
                "mx": {"passed": bool, "message": str, "servers": list},
                "smtp": {"passed": bool, "message": str}
            }
        }
    """
    email = email.strip().lower() if email else ""
    
    result = {
        "email": email,
        "valid": False,
        "deliverable": False,
        "reason": "",
        "checks": {
            "syntax": {"passed": False, "message": ""},
            "mx": {"passed": False, "message": "", "servers": []},
            "smtp": {"passed": False, "message": ""}
        }
    }
    
    # Layer 1: Syntax
    syntax_valid, syntax_msg = check_syntax(email)
    result["checks"]["syntax"] = {"passed": syntax_valid, "message": syntax_msg}
    
    if not syntax_valid:
        result["reason"] = f"Syntax error: {syntax_msg}"
        return result
    
    # Layer 2: MX Records
    has_mx, mx_msg, mx_servers = check_mx(email)
    result["checks"]["mx"] = {"passed": has_mx, "message": mx_msg, "servers": mx_servers}
    
    if not has_mx:
        result["reason"] = f"MX error: {mx_msg}"
        return result
    
    # Layer 3: SMTP (optional)
    if do_smtp_check:
        smtp_valid, smtp_msg = check_smtp(email, mx_servers)
        result["checks"]["smtp"] = {"passed": smtp_valid, "message": smtp_msg}
        
        if not smtp_valid:
            result["reason"] = f"SMTP error: {smtp_msg}"
            result["valid"] = True  # Syntax and MX are valid
            result["deliverable"] = False  # But mailbox doesn't exist
            return result
    else:
        result["checks"]["smtp"] = {"passed": True, "message": "Skipped"}
    
    # All checks passed
    result["valid"] = True
    result["deliverable"] = True
    result["reason"] = "All verification checks passed"
    
    return result


def verify_leads_file(input_file: str, output_file: str = None, do_smtp: bool = True) -> Dict:
    """
    Verify all emails in a leads JSON file.
    
    Returns summary statistics.
    """
    # Load leads
    with open(input_file, 'r') as f:
        leads = json.load(f)
    
    print(f"\n📧 Email Verification")
    print(f"   Total leads: {len(leads)}")
    print(f"   SMTP check: {'Enabled' if do_smtp else 'Disabled'}")
    print()
    
    verified_leads = []
    stats = {
        "total": len(leads),
        "valid": 0,
        "deliverable": 0,
        "invalid_syntax": 0,
        "no_mx": 0,
        "smtp_failed": 0,
        "no_email": 0
    }
    
    for i, lead in enumerate(leads, 1):
        email = lead.get("email", "")
        name = lead.get("name", "Unknown")
        
        print(f"[{i}/{len(leads)}] {name[:40]}")
        
        if not email:
            print(f"      ⏭️  No email")
            stats["no_email"] += 1
            verified_leads.append(lead)
            continue
        
        result = verify_email(email, do_smtp_check=do_smtp)
        
        # Add verification result to lead
        lead["email_verification"] = {
            "valid": result["valid"],
            "deliverable": result["deliverable"],
            "reason": result["reason"]
        }
        
        if result["deliverable"]:
            print(f"      ✅ {email} - Deliverable")
            stats["valid"] += 1
            stats["deliverable"] += 1
        elif result["valid"]:
            print(f"      ⚠️  {email} - Valid but not deliverable: {result['reason']}")
            stats["valid"] += 1
        else:
            reason = result["reason"]
            print(f"      ❌ {email} - Invalid: {reason}")
            
            if "Syntax" in reason:
                stats["invalid_syntax"] += 1
            elif "MX" in reason:
                stats["no_mx"] += 1
            else:
                stats["smtp_failed"] += 1
        
        # Always preserve the lead in the output
        verified_leads.append(lead)
    
    # Save verified leads
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(verified_leads, f, indent=2)
        print(f"\n💾 Saved {len(verified_leads)} verified leads to: {output_file}")
    
    # Print summary
    print(f"\n📊 Verification Summary:")
    print(f"   Total checked: {stats['total']}")
    print(f"   No email: {stats['no_email']}")
    print(f"   Valid emails: {stats['valid']}")
    print(f"   Deliverable: {stats['deliverable']}")
    print(f"   Invalid syntax: {stats['invalid_syntax']}")
    print(f"   No MX records: {stats['no_mx']}")
    print(f"   SMTP failed: {stats['smtp_failed']}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Free email verification")
    parser.add_argument("--email", "-e", help="Single email to verify")
    parser.add_argument("--file", "-f", help="JSON file with leads to verify")
    parser.add_argument("--output", "-o", help="Output file for verified leads")
    parser.add_argument("--no-smtp", action="store_true", help="Skip SMTP verification (faster)")
    
    args = parser.parse_args()
    
    if args.email:
        # Single email verification
        print(f"\n🔍 Verifying: {args.email}")
        result = verify_email(args.email, do_smtp_check=not args.no_smtp)
        
        print(f"\n📋 Results:")
        print(f"   Email: {result['email']}")
        print(f"   Valid: {result['valid']}")
        print(f"   Deliverable: {result['deliverable']}")
        print(f"   Reason: {result['reason']}")
        print(f"\n   Checks:")
        for check_name, check_data in result['checks'].items():
            status = "✅" if check_data['passed'] else "❌"
            print(f"      {status} {check_name}: {check_data['message']}")
        
        # Return JSON for programmatic use
        print(f"\n📝 JSON:")
        print(json.dumps(result, indent=2))
        
    elif args.file:
        # File verification
        output = args.output or args.file.replace('.json', '_verified.json')
        verify_leads_file(args.file, output, do_smtp=not args.no_smtp)
    else:
        parser.print_help()
        print("\n❌ Please provide --email or --file argument")
        sys.exit(1)


if __name__ == "__main__":
    main()
