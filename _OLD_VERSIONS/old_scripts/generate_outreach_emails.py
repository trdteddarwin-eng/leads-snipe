#!/usr/bin/env python3
"""
Cold Outreach Email Generator with Gmail Draft Creation

1. Scrapes each lead's website for personalization hooks
2. Generates custom cold emails using OpenRouter AI (with $1 cost cap)
3. Creates Gmail drafts

Usage:
    python3 execution/generate_outreach_emails.py --leads .tmp/hvac_plumber_electric_union_nj.json
"""

import os
import sys
import json
import re
import time
import base64
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, Dict, List
from email.mime.text import MIMEText
import requests
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()

# OpenRouter API for AI generation
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Cost tracking - $1 MAXIMUM GUARDRAIL
MAX_COST_USD = 1.00
HAIKU_INPUT_COST_PER_1M = 0.25  # $0.25 per 1M input tokens
HAIKU_OUTPUT_COST_PER_1M = 1.25  # $1.25 per 1M output tokens

# Global cost tracker
total_cost_usd = 0.0
total_input_tokens = 0
total_output_tokens = 0

# User agent for scraping
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def estimate_tokens(text: str) -> int:
    """Rough estimate of tokens (4 chars per token average)."""
    return len(text) // 4


def track_cost(input_tokens: int, output_tokens: int) -> float:
    """Track API costs and return current total."""
    global total_cost_usd, total_input_tokens, total_output_tokens
    
    input_cost = (input_tokens / 1_000_000) * HAIKU_INPUT_COST_PER_1M
    output_cost = (output_tokens / 1_000_000) * HAIKU_OUTPUT_COST_PER_1M
    
    total_input_tokens += input_tokens
    total_output_tokens += output_tokens
    total_cost_usd += input_cost + output_cost
    
    return total_cost_usd


def check_cost_guardrail() -> bool:
    """Check if we're still under the $1 cost cap."""
    if total_cost_usd >= MAX_COST_USD:
        print(f"\n⚠️  COST GUARDRAIL TRIGGERED: ${total_cost_usd:.4f} >= ${MAX_COST_USD}")
        print(f"   Input tokens used: {total_input_tokens}")
        print(f"   Output tokens used: {total_output_tokens}")
        print(f"   Stopping to prevent exceeding $1 limit.")
        return False
    return True


def get_gmail_service():
    """Get Gmail API service using saved token."""
    token_path = "token.json"
    
    if not os.path.exists(token_path):
        print("❌ token.json not found. Please add Google OAuth token.")
        return None
    
    try:
        creds = Credentials.from_authorized_user_file(token_path)
        
        # Check if token needs refresh
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            # Save refreshed token
            with open(token_path, 'w') as f:
                f.write(creds.to_json())
        
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"❌ Gmail auth error: {e}")
        return None


def create_gmail_draft(service, to_email: str, subject: str, body: str) -> Optional[str]:
    """Create a Gmail draft and return draft ID."""
    try:
        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()
        
        return draft['id']
    except Exception as e:
        print(f"      ❌ Draft creation failed: {e}")
        return None


def scrape_website(url: str, timeout: int = 15) -> Optional[str]:
    """Scrape a website and return text content."""
    if not url:
        return None
    
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            text = response.text
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:2000]  # Reduced to save tokens
        else:
            return None
            
    except Exception as e:
        return None


def extract_city_from_address(address: str) -> str:
    """Extract city from address string."""
    if not address:
        return "your area"
    parts = address.split(",")
    if len(parts) >= 2:
        city_part = parts[-2].strip()
        # Remove state/zip
        city = city_part.split()[0] if city_part else "your area"
        return city
    return "your area"


def generate_email_with_ai(
    lead: dict,
    website_content: Optional[str],
    sender_name: str = "Yolande"
) -> Optional[Dict[str, str]]:
    """Generate personalized cold email using OpenRouter AI."""
    
    # Check cost guardrail before making API call
    if not check_cost_guardrail():
        return None
    
    business_name = lead.get("name", "your company")
    city = extract_city_from_address(lead.get("address", ""))
    business_type = lead.get("type", "contractor")
    
    website_context = ""
    if website_content:
        website_context = f"\nWebsite content (use for personalization):\n{website_content[:1500]}"
    
    # Analyze website content for triggers
    trigger_analysis = ""
    if website_content:
        # Look for hiring signals
        if any(word in website_content.lower() for word in ['career', 'hiring', 'job opening', 'join our team', 'now hiring']):
            trigger_analysis = "TRIGGER FOUND: Hiring signals detected. Use 'hiring' template."
        # Look for 24/7 claims
        elif any(word in website_content.lower() for word in ['24/7', '24 hour', 'emergency', 'after hours']):
            trigger_analysis = "TRIGGER FOUND: 24/7 or emergency service claims. Use 'after-hours' template."
        # Look for expansion
        elif any(word in website_content.lower() for word in ['new location', 'expanding', 'now serving', 'opened']):
            trigger_analysis = "TRIGGER FOUND: Expansion signals. Use 'expansion' template."
        # Look for awards
        elif any(word in website_content.lower() for word in ['award', 'best of', 'voted', '#1', 'top rated']):
            trigger_analysis = "TRIGGER FOUND: Recent awards. Mention congrats on award."
        else:
            trigger_analysis = "No specific trigger found. Use 'operational reality' template (on job site, can't answer phone)."

    prompt = f"""Generate a cold email to sell AI voice receptionist to this {business_type}.

BUSINESS: {business_name}
LOCATION: {city}, NJ
TYPE: {business_type}

WEBSITE ANALYSIS:
{website_context}

{trigger_analysis}

CHOOSE THE BEST TEMPLATE BASED ON TRIGGERS:

TEMPLATE 1 - HIRING (if hiring signals found):
Subject: question about your receptionist post
Hook: "I noticed you're hiring for front desk/admin..."
Bridge: "Usually means current team is overwhelmed, response times slipping"

TEMPLATE 2 - AFTER HOURS (if 24/7 or emergency claims):
Subject: after-hours dispatch question
Hook: "I was looking at your site and noticed you offer emergency services..."
Bridge: "How do you handle calls after 5 PM?"

TEMPLATE 3 - EXPANSION (if new location/growth signals):
Subject: new [city] location
Hook: "Saw the news about expansion—congrats..."
Bridge: "Growth usually breaks manual processes"

TEMPLATE 4 - OPERATIONAL REALITY (default):
Subject: missed calls at {business_name}
Hook: "I'm guessing you often choose between answering the phone and finishing a job on-site..."
Bridge: "85% of callers hang up on voicemail"

REQUIRED ELEMENTS (include ALL):
- Subject: lowercase, 3-5 words
- One specific hook based on trigger
- Pain stat: 85% hang up, $1,200+ lost per missed call
- Solution: "AI receptionist that handles intake 24/7, indistinguishable from human"
- CTA: ONE question + BOTH links:
  * Free demo: tedca.org
  * Book a call: https://cal.com/ted-charles-enqyjn/30min
- Sign: "Best, Tedca"

RULES:
- Under 75 words (excluding links)
- NO flattery
- Diagnostic observation, not sales pitch
- If you found something specific on their website, reference it

OUTPUT JSON ONLY:
{{"subject": "the subject line", "body": "the full email body"}}"""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3.5-haiku",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Track costs
            usage = result.get("usage", {})
            input_tokens = usage.get("prompt_tokens", estimate_tokens(prompt))
            output_tokens = usage.get("completion_tokens", estimate_tokens(content))
            current_cost = track_cost(input_tokens, output_tokens)
            print(f"      💰 Cost so far: ${current_cost:.4f}")
            
            # Parse JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        else:
            print(f"      ❌ API error: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"      ❌ Generation failed: {e}")
        return None


def process_leads(
    leads: List[dict],
    sender_name: str = "Yolande",
    create_drafts: bool = True,
    concurrency: int = 10
) -> List[dict]:
    """
    Process all leads: use teleport data or scrape, generate emails in parallel, create drafts.

    Args:
        leads: List of lead dictionaries
        sender_name: Name to sign emails with
        create_drafts: Whether to create Gmail drafts
        concurrency: Number of parallel AI generation workers (default 10)
    """
    import threading

    print(f"\n📧 Generating Cold Outreach Emails (Parallel Mode)")
    print(f"   Total leads: {len(leads)}")
    print(f"   Concurrency: {concurrency} workers")
    print(f"   Sender: {sender_name}")
    print(f"   Cost cap: ${MAX_COST_USD}")
    print()

    # Get Gmail service if creating drafts
    gmail_service = None
    if create_drafts:
        gmail_service = get_gmail_service()
        if gmail_service:
            print("✅ Gmail connected - will create drafts\n")
        else:
            print("⚠️  Gmail not connected - will save to file only\n")

    drafts = []
    drafts_lock = threading.Lock()
    cost_exceeded = [False]  # Use list for mutable in closure

    def process_single_lead(idx_lead):
        """Process a single lead - designed for thread pool execution."""
        idx, lead = idx_lead
        nonlocal cost_exceeded

        # Check cost guardrail
        if cost_exceeded[0] or not check_cost_guardrail():
            cost_exceeded[0] = True
            return None

        business_name = lead.get("name", "Unknown")
        website = lead.get("website")
        email = lead.get("email") or lead.get("anymailfinder_email")

        print(f"[{idx}/{len(leads)}] {business_name}")

        if not email:
            print(f"      ⏭️  No email, skipping")
            return None

        # Use Teleport fields (scraped_meta/scraped_text) or fall back to scraping
        website_content = None
        scraped_meta = lead.get("scraped_meta")
        scraped_text = lead.get("scraped_text")

        if scraped_meta or scraped_text:
            # Teleport optimization: Use pre-scraped data from N8N
            print(f"      ⚡ Using pre-scraped data (Teleport)...")
            # Combine meta and text for best context, prioritize meta for hooks
            website_content = scraped_meta or scraped_text
            if scraped_meta and scraped_text:
                website_content = f"{scraped_meta}\n\n{scraped_text[:1500]}"
        elif website:
            print(f"      🌐 Scraping website...")
            website_content = scrape_website(website)
            if website_content:
                print(f"      ✅ Got website content")

        # Generate email
        print(f"      🤖 Generating email...")
        email_data = generate_email_with_ai(lead, website_content, sender_name)

        if email_data:
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")

            draft = {
                "to": email,
                "subject": subject,
                "body": body,
                "business_name": business_name,
                "phone": lead.get("phone", ""),
                "generated_at": datetime.now().isoformat()
            }

            # Thread-safe: add to drafts list
            with drafts_lock:
                drafts.append(draft)

            print(f"      ✅ Email generated: \"{subject}\"")
            return draft
        else:
            print(f"      ❌ Failed to generate")
            return None

    # Use ThreadPoolExecutor for parallel AI generation
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all leads for processing
        futures = {executor.submit(process_single_lead, (i, lead)): i
                   for i, lead in enumerate(leads, 1)}

        # Wait for all to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                idx = futures[future]
                print(f"      ❌ Error processing lead {idx}: {e}")

    # Create Gmail drafts sequentially (Gmail API not thread-safe)
    if gmail_service and drafts:
        print(f"\n📝 Creating {len(drafts)} Gmail drafts...")
        for draft in drafts:
            draft_id = create_gmail_draft(gmail_service, draft["to"], draft["subject"], draft["body"])
            if draft_id:
                draft["gmail_draft_id"] = draft_id

    # Save to file
    output_file = ".tmp/email_drafts.json"
    os.makedirs(".tmp", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(drafts, f, indent=2)

    print(f"\n📊 Summary:")
    print(f"   Emails generated: {len(drafts)}")
    print(f"   Total API cost: ${total_cost_usd:.4f}")
    print(f"   Saved to: {output_file}")

    return drafts


def main():
    parser = argparse.ArgumentParser(description="Generate cold outreach emails")
    parser.add_argument("--leads", "-l", required=True, help="Path to leads JSON")
    parser.add_argument("--sender", "-s", default="Yolande", help="Sender name")
    parser.add_argument("--no-drafts", action="store_true", help="Don't create Gmail drafts")
    parser.add_argument("--concurrency", "-c", type=int, default=10, help="Number of parallel AI workers (default: 10)")

    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not found in .env")
        sys.exit(1)

    with open(args.leads, "r") as f:
        leads = json.load(f)

    drafts = process_leads(leads, args.sender, not args.no_drafts, concurrency=args.concurrency)

    print(f"\n🎉 Done! {len(drafts)} emails ready")


if __name__ == "__main__":
    main()
