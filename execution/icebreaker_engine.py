#!/usr/bin/env python3
"""
Icebreaker Engine - Strategic Personalization for LeadSnipe

Generates human-like opening lines for emails by:
1. Fast Async Scraping (httpx)
2. Regex Sniper (Zero-cost pattern matching for "Since 19XX", etc.)
3. AI Compliment (Low-cost gpt-4o-mini/haiku for nuanced hooks)

Returns a highly specific <15 word "Icebreaker".
"""

import os
import re
import json
import asyncio
import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from typing import Optional, Dict, Tuple

# Load environment
load_dotenv()

# Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Cost Tracking
COST_PER_1M_INPUT = 0.15  # gpt-4o-mini
COST_PER_1M_OUTPUT = 0.60

class IcebreakerEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        self.total_cost = 0.0

    async def get_icebreaker(self, lead: Dict) -> Dict:
        """
        Main entry point for generating an icebreaker.
        
        Args:
            lead: Dictionary containing 'name', 'website', 'city', 'type'
            
        Returns:
            Dict: {'icebreaker': str, 'method': str, 'cost': float}
        """
        website = lead.get("website")
        company_name = lead.get("name", "your business")
        city = lead.get("city", lead.get("address", ""))
        
        if not website:
            return self._fallback(lead, "missing_website")

        # 1. Scraping (Async)
        html_content = await self._scrape_site(website)
        if not html_content:
            return self._fallback(lead, "scraping_failed")

        # Clean text
        text_content = self._clean_html(html_content)
        
        # 2. Regex Sniper (Zero Cost)
        regex_hook = self._regex_sniper(text_content)
        if regex_hook:
            return {
                "icebreaker": regex_hook,
                "method": "regex_sniper",
                "cost": 0.0
            }

        # 3. AI Compliment (Low Cost)
        ai_hook, cost = await self._ai_personalization(company_name, text_content, lead.get("type", "business"))
        if ai_hook:
            self.total_cost += cost
            return {
                "icebreaker": ai_hook,
                "method": "ai_engine",
                "cost": cost
            }

        return self._fallback(lead, "ai_failed")

    async def _scrape_site(self, url: str) -> Optional[str]:
        """Fetch website content quickly."""
        if not url.startswith("http"):
            url = "https://" + url
            
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    return response.text
        except Exception:
            # Try http if https fails
            if url.startswith("https"):
                try:
                    url = url.replace("https", "http", 1)
                    async with httpx.AsyncClient(follow_redirects=True, timeout=7.0) as client:
                        response = await client.get(url, headers=self.headers)
                        if response.status_code == 200:
                            return response.text
                except Exception:
                    pass
        return None

    def _clean_html(self, html: str) -> str:
        """Strip HTML to bare essentials for regex and AI."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove junk
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
            
        text = soup.get_text(separator=" ")
        # Basic cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:3000] # Limit context for speed/cost

    def _regex_sniper(self, text: str) -> Optional[str]:
        """Detect high-value facts using patterns."""
        # Pattern 1: Longevity/Years
        since_match = re.search(r'(?i)(?:since|established in|est\.|serving\s\w+\ssince)\s?(\d{4})', text)
        if since_match:
            year = since_match.group(1)
            # Basic sanity check
            if 1850 < int(year) < 2024:
                return f"I noticed you guys have been serving the community since {year}—that's incredible longevity."

        # Pattern 2: Family Owned
        if re.search(r'(?i)family[ -]owned|owned[ -]and[ -]operated', text):
            return "I love that you're a family-owned and operated business—those local roots really matter."

        # Pattern 3: Awards/Best of
        award_match = re.search(r'(?i)(?:voted|awarded|winner of)\s+(?:best|#1|top)', text)
        if award_match:
            return "Congrats on being recognized as one of the best in your industry—well deserved."

        return None

    async def _ai_personalization(self, name: str, text: str, btype: str) -> Tuple[Optional[str], float]:
        """Use AI to find a specific hook if regex fails."""
        if not OPENROUTER_API_KEY:
            return None, 0.0

        prompt = f"""Write a specific, human-like compliment (<15 words) for this {btype}.
CONTEXT: {text[:1500]}
NAME: {name}

RULES:
- Be specific (mention a service, a project, or a detail from the text).
- NO fluff ("I saw your website", "You do great work").
- Tone: Friendly but professional.
- Output ONLY the sentence.

Example: "I noticed you specialize in high-efficiency heat pumps—rare to find that expertise locally."
"""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "google/gemini-2.0-flash-exp:free", # Using a fast, free/cheap model
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 50,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"].strip().strip('"')
                    
                    # Estimate cost (OpenRouter free models are 0, but good to keep structure)
                    tokens_in = len(prompt) // 4
                    tokens_out = len(content) // 4
                    cost = ((tokens_in / 1_000_000) * COST_PER_1M_INPUT) + ((tokens_out / 1_000_000) * COST_PER_1M_OUTPUT)
                    
                    return content, cost
        except Exception as e:
            print(f"AI Error: {e}")
            
        return None, 0.0

    def _fallback(self, lead: Dict, reason: str) -> Dict:
        """Generic location-based icebreaker if all else fails."""
        city = lead.get("city", lead.get("address", ""))
        name = lead.get("name", "your business")
        
        if city:
            # Extract city from address if needed
            if "," in city:
                city = city.split(",")[0].strip()
            hook = f"I was doing some research on local businesses in {city} and {name} stood out."
        else:
            hook = f"I've been following {name} for a bit and really respect what you guys are doing."
            
        return {
            "icebreaker": hook,
            "method": f"fallback_{reason}",
            "cost": 0.0
        }

# --- Test Suite ---
async def test_engine():
    engine = IcebreakerEngine()
    
    test_leads = [
        {
            "name": "The Plumbing Experts",
            "website": "example.com", # Replace with real one for testing
            "city": "Austin",
            "type": "Plumber"
        },
        {
            "name": "Classic Cafe",
            "website": "http://example.com/about",
            "city": "Miami",
            "type": "Restaurant"
        }
    ]
    
    for lead in test_leads:
        print(f"\nProcessing: {lead['name']}")
        result = await engine.get_icebreaker(lead)
        print(f"Icebreaker: {result['icebreaker']}")
        print(f"Method: {result['method']}")

if __name__ == "__main__":
    asyncio.run(test_engine())
