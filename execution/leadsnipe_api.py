#!/usr/bin/env python3
"""
LeadSnipe API Server v2.0

FastAPI server that bridges the frontend to the backend lead pipeline.
Features:
- SQLite persistence for hunt history
- Real-time log streaming via Server-Sent Events (SSE)
- Gmail OAuth flow for token.json generation

Usage:
    python3 execution/leadsnipe_api.py
    # Or with uvicorn:
    uvicorn execution.leadsnipe_api:app --reload --host 127.0.0.1 --port 8000
"""

import os
import sys
import json
import uuid
import subprocess
import threading
import sqlite3
import asyncio
import time
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel, Field
import requests
import re
import random
from urllib.parse import urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure we can find execution scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

# ============================================================================
# Data Models
# ============================================================================

class HuntStage(str, Enum):
    QUEUED = "queued"
    SCRAPING = "scraping"
    FINDING_OWNERS = "finding_owners"
    GETTING_EMAILS = "getting_emails"
    GENERATING_OUTREACH = "generating_outreach"
    COMPLETED = "completed"
    FAILED = "failed"


class HuntRequest(BaseModel):
    niche: str = Field(..., example="Dentists")
    location: str = Field(..., example="Union, NJ")
    limit: int = Field(default=50, ge=5, le=500)
    user_id: Optional[str] = Field(None, description="Firebase User UID")


class HuntResponse(BaseModel):
    hunt_id: str
    message: str


class HuntStatus(BaseModel):
    hunt_id: str
    niche: str
    location: str
    limit: int
    status: HuntStage
    progress_percent: int
    stage_message: str
    leads_found: int
    owners_found: int
    emails_found: int
    started_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class Lead(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    owner_name: Optional[str] = None
    owner_first_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    email_verified: bool = False
    has_direct_contact: bool = False
    email_draft: Optional[dict] = None
    scraped_at: Optional[str] = None
    user_ratings_total: Optional[int] = 0


class LeadListResponse(BaseModel):
    leads: List[Lead]
    total: int
    hunt_id: Optional[str] = None


# ============================================================================
# SQLite Database Layer
# ============================================================================

DB_PATH = ".tmp/leadsnipe.db"

def init_database():
    """Initialize SQLite database with required tables."""
    os.makedirs(".tmp", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Hunts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hunts (
            hunt_id TEXT PRIMARY KEY,
            user_id TEXT,
            niche TEXT NOT NULL,
            location TEXT NOT NULL,
            city TEXT,
            state TEXT,
            limit_count INTEGER,
            status TEXT DEFAULT 'queued',
            progress_percent INTEGER DEFAULT 0,
            stage_message TEXT DEFAULT 'Preparing hunt...',
            leads_found INTEGER DEFAULT 0,
            owners_found INTEGER DEFAULT 0,
            emails_found INTEGER DEFAULT 0,
            started_at TEXT,
            completed_at TEXT,
            error TEXT,
            leads_json TEXT
        )
    ''')

    # Ensure user_id column exists (migration)
    try:
        cursor.execute("ALTER TABLE hunts ADD COLUMN user_id TEXT")
    except sqlite3.OperationalError:
        pass # Already exists

    # Logs table for streaming
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hunt_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hunt_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            level TEXT DEFAULT 'INFO',
            message TEXT NOT NULL,
            FOREIGN KEY (hunt_id) REFERENCES hunts(hunt_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("[DB] Database initialized")


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def db_save_hunt(hunt_data: dict):
    """Save or update hunt in database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO hunts
            (hunt_id, user_id, niche, location, city, state, limit_count, status,
             progress_percent, stage_message, leads_found, owners_found,
             emails_found, started_at, completed_at, error, leads_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            hunt_data.get("hunt_id"),
            hunt_data.get("user_id"),
            hunt_data.get("niche"),
            hunt_data.get("location"),
            hunt_data.get("city"),
            hunt_data.get("state"),
            hunt_data.get("limit"),
            hunt_data.get("status"),
            hunt_data.get("progress_percent", 0),
            hunt_data.get("stage_message"),
            hunt_data.get("leads_found", 0),
            hunt_data.get("owners_found", 0),
            hunt_data.get("emails_found", 0),
            hunt_data.get("started_at"),
            hunt_data.get("completed_at"),
            hunt_data.get("error"),
            json.dumps(hunt_data.get("leads", [])) if hunt_data.get("leads") else None
        ))
        conn.commit()


def db_get_hunt(hunt_id: str) -> Optional[dict]:
    """Get hunt from database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hunts WHERE hunt_id = ?', (hunt_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def db_get_all_hunts() -> List[dict]:
    """Get all hunts from database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM hunts ORDER BY started_at DESC')
        return [dict(row) for row in cursor.fetchall()]


def db_add_log(hunt_id: str, message: str, level: str = "INFO"):
    """Add log entry for a hunt."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO hunt_logs (hunt_id, timestamp, level, message)
            VALUES (?, ?, ?, ?)
        ''', (hunt_id, datetime.now().isoformat(), level, message))
        conn.commit()


def db_get_logs(hunt_id: str, since_id: int = 0) -> List[dict]:
    """Get logs for a hunt since a given ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, timestamp, level, message
            FROM hunt_logs
            WHERE hunt_id = ? AND id > ?
            ORDER BY id ASC
        ''', (hunt_id, since_id))
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# In-Memory State (for active hunts + real-time)
# ============================================================================

hunts: Dict[str, dict] = {}
leads_store: Dict[str, list] = {}
log_queues: Dict[str, deque] = {}  # hunt_id -> deque of log messages

# ============================================================================
# Location Parser
# ============================================================================

STATE_ABBREV = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC"
}


def parse_location(location: str) -> tuple:
    """Parse location flexibly: 'City, State', 'City, ST', 'State', or 'ST'."""
    location = location.strip()

    # Check if entire input is a 2-letter state abbreviation
    if len(location) == 2 and location.upper() in STATE_ABBREV.values():
        return "", location.upper()

    # Check if entire input is a full state name (e.g., "New Jersey")
    location_lower = location.lower()
    if location_lower in STATE_ABBREV:
        return "", STATE_ABBREV[location_lower]

    # Check for "X area" pattern (e.g., "Phoenix area", "Los Angeles area")
    if location_lower.endswith(" area"):
        city = location[:-5].strip()  # Remove " area"
        return city, ""

    # Standard "City, State" format
    parts = location.split(",")
    if len(parts) >= 2:
        city = parts[0].strip()
        state_raw = parts[1].strip().lower()

        # 2-letter abbreviation
        if len(state_raw) == 2:
            return city, state_raw.upper()

        # Full state name
        state = STATE_ABBREV.get(state_raw)
        if state:
            return city, state

        raise ValueError(f"Unknown state: {state_raw}")

    # No comma - try "City ST" format (e.g., "Union NJ")
    words = location.strip().split()
    if len(words) >= 2:
        potential_state = words[-1].strip()
        city = " ".join(words[:-1])

        # Check if last word is 2-letter abbreviation
        if len(potential_state) == 2 and potential_state.upper() in STATE_ABBREV.values():
            return city, potential_state.upper()

        # Check if last 2 words form a state name (e.g., "New Jersey")
        if len(words) >= 2:
            potential_state_name = " ".join(words[-2:]).lower()
            if potential_state_name in STATE_ABBREV:
                city = " ".join(words[:-2]) if len(words) > 2 else ""
                return city, STATE_ABBREV[potential_state_name]

    # Single word that's not a state - use as city with empty state
    if len(words) == 1:
        return location, ""

    raise ValueError(f"Invalid location format: {location}. Try 'City, State' or just 'State'")


# ============================================================================
# Perpetual Discovery Loop - "Troy" Logic
# ============================================================================

# API Keys
ANYMAILFINDER_API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

# User agents for web scraping
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

# Owner-related keywords
OWNER_KEYWORDS = ['owner', 'founder', 'president', 'ceo', 'proprietor', 'principal', 'managing director']

# Name pattern
NAME_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b')

# Common email patterns
EMAIL_PATTERNS = [
    "{first}@{domain}",
    "{last}@{domain}",
    "{first}.{last}@{domain}",
    "{f}{last}@{domain}",
    "{first}{l}@{domain}",
    "{first}_{last}@{domain}",
    "info@{domain}",
    "contact@{domain}",
    "admin@{domain}",
]


def extract_domain(url: str) -> Optional[str]:
    """Extract clean domain from URL."""
    if not url:
        return None
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.rstrip('/') if domain else None
    except:
        return None


def layer1_database_match(domain: str, hunt_id: str = None) -> Dict:
    """
    Layer 1: Database Match - Apollo + Anymailfinder decision maker lookup.
    """
    result = {"email": None, "name": None, "title": None, "source": None, "linkedin_url": None}

    if not domain:
        return result

    # Try Anymailfinder Decision Maker API first
    if ANYMAILFINDER_API_KEY:
        try:
            resp = requests.post(
                "https://api.anymailfinder.com/v5.1/find-email/decision-maker",
                json={"domain": domain, "decision_maker_category": ["ceo", "owner", "founder"]},
                headers={"Authorization": f"Bearer {ANYMAILFINDER_API_KEY}"},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("email"):
                    result["email"] = data.get("email")
                    result["name"] = data.get("full_name")
                    result["title"] = data.get("job_title", "CEO/Owner")
                    result["linkedin_url"] = data.get("linkedin_url")
                    result["source"] = "anymailfinder_decision_maker"
                    if hunt_id:
                        add_log(hunt_id, f"  ✓ Layer 1 (AMF): Found {result['name']} - {result['email']}", "SUCCESS")
                    return result
        except Exception as e:
            if hunt_id:
                add_log(hunt_id, f"  Layer 1 (AMF) error: {str(e)[:50]}", "WARN")

    # Try Apollo.io
    if APOLLO_API_KEY:
        try:
            resp = requests.post(
                "https://api.apollo.io/v1/mixed_people/search",
                headers={"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY},
                json={
                    "q_organization_domains": domain,
                    "person_titles": ["owner", "ceo", "founder", "president", "principal"],
                    "per_page": 3
                },
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                people = data.get("people", [])
                if people:
                    person = people[0]
                    result["email"] = person.get("email")
                    result["name"] = person.get("name")
                    result["title"] = person.get("title", "CEO/Owner")
                    result["linkedin_url"] = person.get("linkedin_url")
                    result["source"] = "apollo"
                    if hunt_id and result["email"]:
                        add_log(hunt_id, f"  ✓ Layer 1 (Apollo): Found {result['name']} - {result['email']}", "SUCCESS")
                    return result
        except Exception as e:
            if hunt_id:
                add_log(hunt_id, f"  Layer 1 (Apollo) error: {str(e)[:50]}", "WARN")

    return result


def layer2_web_sniffing(website: str, hunt_id: str = None) -> Dict:
    """
    Layer 2: Web Sniffing - Scrape About Us, Team, Contact pages for owner names.
    """
    result = {"names": [], "title": None, "linkedin_url": None, "source": None}

    if not website:
        return result

    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website

    parsed = urlparse(website)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    pages = [
        website,
        f"{base_url}/about",
        f"{base_url}/about-us",
        f"{base_url}/team",
        f"{base_url}/our-team",
        f"{base_url}/meet-the-team",
        f"{base_url}/leadership",
        f"{base_url}/contact",
    ]

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    all_names = []

    for page_url in pages[:5]:  # Limit to 5 pages
        try:
            resp = requests.get(page_url, headers=headers, timeout=10, allow_redirects=True)
            if resp.status_code != 200:
                continue

            text = resp.text.lower()

            # Check if page has owner-related content
            has_owner_content = any(kw in text for kw in OWNER_KEYWORDS)
            if not has_owner_content and page_url != website:
                continue

            # Extract names
            names = NAME_PATTERN.findall(resp.text)

            # Filter false positives
            false_positives = {
                'united states', 'new jersey', 'new york', 'contact us', 'about us',
                'our team', 'read more', 'learn more', 'privacy policy', 'terms service',
                'all rights', 'get started', 'free estimate', 'call now', 'book now'
            }

            for name in names:
                if name.lower() not in false_positives and len(name) > 5:
                    all_names.append(name)

            # Check for LinkedIn URL
            linkedin_match = re.search(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?', resp.text)
            if linkedin_match and not result["linkedin_url"]:
                result["linkedin_url"] = linkedin_match.group(0)
                result["source"] = page_url

        except Exception as e:
            continue

    # Deduplicate names
    seen = set()
    unique_names = []
    for name in all_names:
        if name.lower() not in seen:
            seen.add(name.lower())
            unique_names.append(name)

    result["names"] = unique_names[:5]

    if hunt_id and result["names"]:
        add_log(hunt_id, f"  ✓ Layer 2 (Web): Found names: {', '.join(result['names'][:3])}", "SUCCESS")

    return result


def layer3_recursive_search(business_name: str, city: str, owner_name: str = None, hunt_id: str = None) -> Dict:
    """
    Layer 3: Recursive Search - DuckDuckGo search with multiple variations.
    """
    result = {"names": [], "linkedin_url": None, "source": None}

    if not business_name:
        return result

    # Build search queries
    queries = [
        f'"{business_name}" owner',
        f'"{business_name}" CEO',
        f'"{business_name}" founder',
    ]

    if city:
        queries.insert(0, f'"{business_name}" owner "{city}"')

    if owner_name:
        queries.append(f'"{owner_name}" LinkedIn')

    headers = {"User-Agent": random.choice(USER_AGENTS)}

    for query in queries[:4]:  # Limit queries
        try:
            # DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            resp = requests.get(search_url, headers=headers, timeout=10)

            if resp.status_code != 200:
                continue

            text = resp.text

            # Extract names from results
            names = NAME_PATTERN.findall(text)
            for name in names[:3]:
                if name.lower() not in ['duck duck', 'duckduckgo']:
                    result["names"].append(name)

            # Look for LinkedIn URLs
            linkedin_match = re.search(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)', text)
            if linkedin_match and not result["linkedin_url"]:
                result["linkedin_url"] = linkedin_match.group(0)
                result["source"] = f"duckduckgo:{query[:30]}"

            # Small delay between searches
            import time
            time.sleep(0.5)

        except Exception as e:
            continue

    # Deduplicate
    result["names"] = list(set(result["names"]))[:5]

    if hunt_id and (result["names"] or result["linkedin_url"]):
        add_log(hunt_id, f"  ✓ Layer 3 (Search): Found {len(result['names'])} names, LinkedIn: {'Yes' if result['linkedin_url'] else 'No'}", "SUCCESS")

    return result


def layer4_pattern_guess(domain: str, first_name: str, last_name: str, hunt_id: str = None) -> Optional[str]:
    """
    Layer 4: Pattern Guessing - Try common email patterns and verify.
    """
    if not domain or not first_name:
        return None

    first = first_name.lower().strip()
    last = last_name.lower().strip() if last_name else ""
    f = first[0] if first else ""
    l = last[0] if last else ""

    # Generate email candidates
    candidates = []
    for pattern in EMAIL_PATTERNS:
        try:
            email = pattern.format(first=first, last=last, f=f, l=l, domain=domain)
            if "@" in email and "." in email:
                candidates.append(email)
        except:
            continue

    # Quick DNS/MX check for domain
    try:
        import socket
        socket.getaddrinfo(domain, 80, socket.AF_INET, socket.SOCK_STREAM, 0, socket.AI_PASSIVE)
    except:
        if hunt_id:
            add_log(hunt_id, f"  Layer 4: Domain {domain} unreachable", "WARN")
        return None

    # Simple validation - check if domain accepts mail
    # For now, return the most likely pattern
    if first and last:
        best_guess = f"{first}.{last}@{domain}"
    elif first:
        best_guess = f"{first}@{domain}"
    else:
        best_guess = f"info@{domain}"

    if hunt_id:
        add_log(hunt_id, f"  ✓ Layer 4 (Pattern): Best guess: {best_guess}", "INFO")

    return best_guess


def perpetual_discovery_loop(lead: Dict, hunt_id: str = None) -> Dict:
    """
    Perpetual Discovery Loop - Never give up finding CEO contact info.

    Layers:
    1. Database Match (Apollo + Anymailfinder)
    2. Web Sniffing (scrape team pages)
    3. Recursive Search (DuckDuckGo)
    4. Pattern Guessing + Verification

    Fail-Safe: Always output business_email as fallback.
    Loop: If name found, retry email finding with that name.
    """
    # Preserve original business email as fallback
    business_email = lead.get("email")
    website = lead.get("website", "")
    business_name = lead.get("name", "")
    address = lead.get("address", "")

    # Extract city from address
    city = ""
    if address:
        parts = address.split(",")
        if len(parts) >= 2:
            city = parts[-2].strip()

    domain = extract_domain(website)

    result = {
        "owner_name": lead.get("owner_name"),
        "owner_email": None,
        "owner_title": lead.get("owner_title", "CEO/Owner"),
        "linkedin_url": lead.get("linkedin_url"),
        "email_source": None,
        "discovery_layers_tried": []
    }

    if hunt_id:
        add_log(hunt_id, f"🔍 Troy Loop: {business_name} ({domain or 'no domain'})", "INFO")

    # ========== LAYER 1: Database Match ==========
    result["discovery_layers_tried"].append("L1_database")

    if domain:
        l1_result = layer1_database_match(domain, hunt_id)
        if l1_result.get("email"):
            result["owner_email"] = l1_result["email"]
            result["owner_name"] = l1_result.get("name") or result["owner_name"]
            result["owner_title"] = l1_result.get("title") or result["owner_title"]
            result["linkedin_url"] = l1_result.get("linkedin_url") or result["linkedin_url"]
            result["email_source"] = l1_result.get("source")
            # Success! But continue to get more info if missing name
            if result["owner_name"] and result["owner_email"]:
                return result

    # ========== LAYER 2: Web Sniffing ==========
    result["discovery_layers_tried"].append("L2_web")

    l2_result = layer2_web_sniffing(website, hunt_id)
    discovered_names = l2_result.get("names", [])

    if l2_result.get("linkedin_url") and not result["linkedin_url"]:
        result["linkedin_url"] = l2_result["linkedin_url"]

    # If we found names but no email yet, try Layer 1 again with name
    if discovered_names and not result["owner_email"] and domain:
        for name in discovered_names[:2]:  # Try top 2 names
            name_parts = name.split()
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]

                # Try Anymailfinder with name
                if ANYMAILFINDER_API_KEY:
                    try:
                        resp = requests.post(
                            "https://api.anymailfinder.com/v5.1/find-email/name-domain",
                            json={"domain": domain, "first_name": first_name, "last_name": last_name},
                            headers={"Authorization": f"Bearer {ANYMAILFINDER_API_KEY}"},
                            timeout=15
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("email"):
                                result["owner_email"] = data["email"]
                                result["owner_name"] = name
                                result["email_source"] = "anymailfinder_name"
                                if hunt_id:
                                    add_log(hunt_id, f"  ✓ Loop: Found email for {name}: {data['email']}", "SUCCESS")
                                return result
                    except:
                        pass

    # Use first discovered name if we don't have one
    if discovered_names and not result["owner_name"]:
        result["owner_name"] = discovered_names[0]

    # ========== LAYER 3: Recursive Search ==========
    result["discovery_layers_tried"].append("L3_search")

    l3_result = layer3_recursive_search(business_name, city, result.get("owner_name"), hunt_id)

    if l3_result.get("linkedin_url") and not result["linkedin_url"]:
        result["linkedin_url"] = l3_result["linkedin_url"]

    # Merge found names
    if l3_result.get("names"):
        if not result["owner_name"]:
            result["owner_name"] = l3_result["names"][0]

        # Try email finding again with search-discovered names
        if not result["owner_email"] and domain:
            for name in l3_result["names"][:2]:
                name_parts = name.split()
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]

                    if ANYMAILFINDER_API_KEY:
                        try:
                            resp = requests.post(
                                "https://api.anymailfinder.com/v5.1/find-email/name-domain",
                                json={"domain": domain, "first_name": first_name, "last_name": last_name},
                                headers={"Authorization": f"Bearer {ANYMAILFINDER_API_KEY}"},
                                timeout=15
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                if data.get("email"):
                                    result["owner_email"] = data["email"]
                                    result["owner_name"] = name
                                    result["email_source"] = "anymailfinder_search_loop"
                                    if hunt_id:
                                        add_log(hunt_id, f"  ✓ Loop: Found email for {name}: {data['email']}", "SUCCESS")
                                    return result
                        except:
                            pass

    # ========== LAYER 4: Pattern Guessing ==========
    result["discovery_layers_tried"].append("L4_pattern")

    if not result["owner_email"] and domain and result["owner_name"]:
        name_parts = result["owner_name"].split()
        first_name = name_parts[0] if name_parts else None
        last_name = name_parts[-1] if len(name_parts) > 1 else None

        guessed_email = layer4_pattern_guess(domain, first_name, last_name, hunt_id)
        if guessed_email:
            result["owner_email"] = guessed_email
            result["email_source"] = "pattern_guess"

    # ========== FAIL-SAFE: Business Email Fallback ==========
    if not result["owner_email"] and business_email:
        result["owner_email"] = business_email
        result["email_source"] = "business_email_fallback"
        if hunt_id:
            add_log(hunt_id, f"  ⚠ Fail-safe: Using business email {business_email}", "WARN")

    # Final status
    if hunt_id:
        if result["owner_email"]:
            add_log(hunt_id, f"  ✓ Troy Complete: {result['owner_name'] or 'Unknown'} - {result['owner_email']} (via {result['email_source']})", "SUCCESS")
        else:
            add_log(hunt_id, f"  ✗ Troy: No email found for {business_name}", "WARN")

    return result


def enrich_leads_with_troy(leads: List[Dict], hunt_id: str = None, max_workers: int = 5) -> List[Dict]:
    """
    Run Perpetual Discovery Loop on all leads in parallel.
    """
    if hunt_id:
        add_log(hunt_id, f"🚀 Starting Troy Discovery Loop on {len(leads)} leads ({max_workers} parallel workers)...", "INFO")

    def process_lead(lead):
        try:
            result = perpetual_discovery_loop(lead, hunt_id)

            # Merge results back into lead
            if result.get("owner_name"):
                lead["owner_name"] = result["owner_name"]
            if result.get("owner_email"):
                lead["anymailfinder_email"] = result["owner_email"]
                lead["email_source"] = result.get("email_source")
            if result.get("owner_title"):
                lead["owner_title"] = result["owner_title"]
            if result.get("linkedin_url"):
                lead["linkedin_url"] = result["linkedin_url"]
            if result.get("discovery_layers_tried"):
                lead["discovery_layers"] = result["discovery_layers_tried"]

            return lead
        except Exception as e:
            if hunt_id:
                add_log(hunt_id, f"  Error processing {lead.get('name', 'unknown')}: {str(e)[:50]}", "ERROR")
            return lead

    # Process in parallel
    enriched = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_lead, lead): lead for lead in leads}
        for future in as_completed(futures):
            try:
                enriched.append(future.result())
            except Exception as e:
                enriched.append(futures[future])

    # Stats
    owners_found = sum(1 for l in enriched if l.get("owner_name"))
    emails_found = sum(1 for l in enriched if l.get("anymailfinder_email"))
    linkedin_found = sum(1 for l in enriched if l.get("linkedin_url"))

    if hunt_id:
        add_log(hunt_id, f"✓ Troy Complete: {owners_found} owners, {emails_found} emails, {linkedin_found} LinkedIn profiles", "SUCCESS")

    return enriched


# ============================================================================
# Insight Engine - Website Scraping & AI Analysis
# ============================================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Rate limiting for LLM calls
import threading
llm_semaphore = threading.Semaphore(5)  # Max 5 concurrent calls
llm_last_call = 0
llm_lock = threading.Lock()

def rate_limited_delay():
    """Ensure 200ms between LLM calls."""
    global llm_last_call
    with llm_lock:
        now = time.time()
        elapsed = now - llm_last_call
        if elapsed < 0.2:
            time.sleep(0.2 - elapsed)
        llm_last_call = time.time()


def scrape_website_for_insights(url: str, max_pages: int = 5) -> Dict:
    """
    Scrape website and extract text from key pages.
    Returns: {raw_text, pages_scraped, word_count, scraped_at}
    """
    result = {
        "raw_text": "",
        "pages_scraped": [],
        "word_count": 0,
        "scraped_at": datetime.now().isoformat()
    }

    if not url:
        return result

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    except:
        return result

    # Pages to scrape (in priority order)
    pages = [
        url,  # Homepage
        f"{base_url}/about",
        f"{base_url}/about-us",
        f"{base_url}/services",
        f"{base_url}/our-services",
        f"{base_url}/contact",
        f"{base_url}/team",
        f"{base_url}/pricing",
    ]

    headers = {"User-Agent": random.choice(USER_AGENTS)}
    all_text = []

    for page_url in pages[:max_pages]:
        try:
            resp = requests.get(page_url, headers=headers, timeout=10, allow_redirects=True)
            if resp.status_code != 200:
                continue

            # Parse HTML and extract text
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator=' ', strip=True)

            # Clean up whitespace
            text = ' '.join(text.split())

            if text and len(text) > 100:
                all_text.append(f"[PAGE: {page_url}]\n{text[:3000]}")  # Limit per page
                result["pages_scraped"].append(page_url)

        except Exception as e:
            continue

    # Combine all text (limit to ~12000 chars / ~3000 tokens)
    result["raw_text"] = "\n\n".join(all_text)[:12000]
    result["word_count"] = len(result["raw_text"].split())

    return result


def call_openrouter_llm(prompt: str, system_prompt: str = None, model: str = "meta-llama/llama-3.3-70b-instruct") -> Optional[str]:
    """
    Call OpenRouter LLM with rate limiting.
    Primary: Llama 3.3 70B (FREE)
    Fallback: Qwen 2.5 72B (FREE)
    """
    if not OPENROUTER_API_KEY:
        return None

    with llm_semaphore:
        rate_limited_delay()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Try primary model first
        models_to_try = [
            "meta-llama/llama-3.3-70b-instruct",
            "qwen/qwen-2.5-72b-instruct",
            "mistralai/mistral-7b-instruct"
        ]

        for model in models_to_try:
            try:
                resp = requests.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://leadsnipe.app",
                        "X-Title": "LeadSnipe Insight Engine"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 1000,
                        "temperature": 0.7
                    },
                    timeout=30
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                elif resp.status_code == 429:
                    # Rate limited, try next model
                    time.sleep(1)
                    continue
                else:
                    continue

            except Exception as e:
                continue

        return None


def generate_quick_insights(raw_text: str, business_name: str) -> List[str]:
    """
    Generate 5 quick insights about a business using LLM.
    Returns list of insight strings.
    """
    if not raw_text or len(raw_text) < 100:
        return ["No website content available for analysis"]

    prompt = f"""Analyze this business website content for "{business_name}" and provide exactly 5 quick insights.

Focus on:
- What services/products they offer
- Potential weaknesses or gaps (no online booking, outdated design, etc.)
- Business characteristics (years in business, team size, service area)
- Opportunities for improvement
- Things that make them unique or notable

Website Content:
{raw_text[:8000]}

Respond with exactly 5 bullet points, each starting with "•". Keep each insight to 1-2 sentences max. Be specific and actionable."""

    system_prompt = "You are a business analyst helping sales professionals understand potential clients. Be concise, specific, and focus on actionable insights."

    response = call_openrouter_llm(prompt, system_prompt)

    if not response:
        return ["Unable to generate insights - LLM unavailable"]

    # Parse bullet points
    insights = []
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            # Clean up the bullet
            insight = line.lstrip('•-* ').strip()
            if insight:
                insights.append(insight)

    # Ensure we have at least something
    if not insights:
        insights = [response[:200]]  # Fallback to raw response

    return insights[:5]  # Max 5 insights


def ask_insight_question(raw_text: str, business_name: str, question: str) -> str:
    """
    Answer any question about a business based on scraped website content.
    """
    if not raw_text or len(raw_text) < 100:
        return "No website content available. The business website could not be scraped or has no content."

    prompt = f"""Based on the website content for "{business_name}", answer this question:

Question: {question}

Website Content:
{raw_text[:8000]}

Provide a helpful, specific answer based on what you can see in the website content. If the answer isn't clear from the content, say so and provide your best inference. Be conversational and actionable."""

    system_prompt = """You are a sales intelligence assistant. Help the user understand this business so they can craft personalized outreach. Be specific, cite details from the website when possible, and focus on actionable insights that help with sales."""

    response = call_openrouter_llm(prompt, system_prompt)

    if not response:
        return "Unable to process your question. Please try again."

    return response


def enrich_leads_with_insights(leads: List[Dict], hunt_id: str = None, max_workers: int = 3) -> List[Dict]:
    """
    Scrape websites and generate quick insights for all leads.
    """
    if hunt_id:
        add_log(hunt_id, f"🔮 Starting Insight Engine on {len(leads)} leads...", "INFO")

    def process_lead(lead):
        try:
            website = lead.get("website")
            business_name = lead.get("name", "Unknown Business")

            # Scrape website
            scraped = scrape_website_for_insights(website)

            if scraped.get("raw_text"):
                lead["website_content"] = scraped

                # Generate quick insights
                insights = generate_quick_insights(scraped["raw_text"], business_name)
                lead["quick_insights"] = insights

                if hunt_id:
                    add_log(hunt_id, f"  ✓ {business_name}: {len(insights)} insights generated", "SUCCESS")
            else:
                lead["website_content"] = {"raw_text": "", "pages_scraped": [], "word_count": 0}
                lead["quick_insights"] = ["Website could not be scraped"]
                if hunt_id:
                    add_log(hunt_id, f"  ⚠ {business_name}: No website content found", "WARN")

            return lead

        except Exception as e:
            if hunt_id:
                add_log(hunt_id, f"  ✗ Error processing {lead.get('name', 'unknown')}: {str(e)[:50]}", "ERROR")
            lead["quick_insights"] = ["Error generating insights"]
            return lead

    # Process in parallel (but limited to avoid rate limits)
    enriched = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_lead, lead): lead for lead in leads}
        for future in as_completed(futures):
            try:
                enriched.append(future.result())
            except:
                enriched.append(futures[future])

    if hunt_id:
        insights_count = sum(1 for l in enriched if l.get("quick_insights") and len(l.get("quick_insights", [])) > 0)
        add_log(hunt_id, f"✓ Insight Engine Complete: {insights_count}/{len(leads)} leads analyzed", "SUCCESS")

    return enriched


# ============================================================================
# Gmail Send Functions
# ============================================================================

def send_gmail_email(to_email: str, subject: str, body: str, from_name: str = "LeadSnipe") -> Dict:
    """
    Send an email via Gmail API (not just draft).
    Returns: {success, message_id, error}
    """
    import base64
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    result = {"success": False, "message_id": None, "error": None}

    try:
        # Check for Gmail credentials
        if not os.path.exists("token.json"):
            result["error"] = "Gmail not connected. Please connect Gmail first."
            return result

        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)

        # Create message
        message = MIMEMultipart()
        message["to"] = to_email
        message["subject"] = subject
        message["from"] = from_name

        # Add body
        message.attach(MIMEText(body, "plain"))

        # Encode
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send
        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        result["success"] = True
        result["message_id"] = sent.get("id")

    except Exception as e:
        result["error"] = str(e)

    return result


def send_bulk_emails(emails: List[Dict], delay_seconds: int = 3) -> List[Dict]:
    """
    Send multiple emails with rate limiting.
    emails: [{to, subject, body}, ...]
    Returns: [{to, success, message_id, error}, ...]
    """
    results = []

    for i, email in enumerate(emails):
        # Send email
        result = send_gmail_email(
            to_email=email.get("to"),
            subject=email.get("subject"),
            body=email.get("body")
        )
        result["to"] = email.get("to")
        results.append(result)

        # Rate limiting delay (except for last email)
        if i < len(emails) - 1:
            time.sleep(delay_seconds)

    return results


# ============================================================================
# Pipeline Runner with Logging
# ============================================================================

def add_log(hunt_id: str, message: str, level: str = "INFO"):
    """Add log to both in-memory queue and database."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"

    # In-memory for SSE streaming
    if hunt_id not in log_queues:
        log_queues[hunt_id] = deque(maxlen=1000)
    log_queues[hunt_id].append(log_entry)

    # Database for persistence
    db_add_log(hunt_id, message, level)

    # Also print to server console
    print(f"[{hunt_id}] {log_entry}")


def update_status(hunt_id: str, stage: HuntStage, progress: int, message: str, **kwargs):
    """Update hunt status in memory and database."""
    if hunt_id in hunts:
        hunts[hunt_id].update({
            "status": stage.value,
            "progress_percent": progress,
            "stage_message": message,
            **kwargs
        })
        # Save to database
        db_save_hunt(hunts[hunt_id])

        # Add log
        add_log(hunt_id, f"{stage.value.upper()}: {message}")


def run_pipeline_with_logging(hunt_id: str, niche: str, state: str, limit: int):
    """Execute the 4-stage lead pipeline with real-time logging."""

    os.makedirs(".tmp", exist_ok=True)

    raw_file = f".tmp/hunt_{hunt_id}_raw.json"
    owners_file = f".tmp/hunt_{hunt_id}_owners.json"
    emails_file = f".tmp/hunt_{hunt_id}_emails.json"

    def run_script(cmd: List[str], stage_name: str, timeout: int = 300):
        """Run a script and stream its output to logs."""
        add_log(hunt_id, f"Starting {stage_name}...")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Stream output line by line
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    add_log(hunt_id, line.strip(), "SCRIPT")

            process.wait(timeout=timeout)

            if process.returncode != 0:
                add_log(hunt_id, f"{stage_name} exited with code {process.returncode}", "WARN")
            else:
                add_log(hunt_id, f"{stage_name} completed successfully")

            return process.returncode

        except subprocess.TimeoutExpired:
            process.kill()
            add_log(hunt_id, f"{stage_name} timed out after {timeout}s", "ERROR")
            return -1
        except Exception as e:
            add_log(hunt_id, f"{stage_name} error: {str(e)}", "ERROR")
            return -1

    try:
        # ====================================================================
        # Stage 1: Scraping Google Maps (0-25%)
        # ====================================================================
        update_status(hunt_id, HuntStage.SCRAPING, 5, "Starting Google Maps scrape...")

        run_script([
            sys.executable, "execution/direct_lead_gen.py",
            "--industry", niche,
            "--location", f"{hunts[hunt_id].get('city', '')}, {state}",
            "--limit", str(limit),
            "--output", raw_file
        ], "Lead Sniper Engine (Direct)", timeout=300)

        # Load scraped leads
        if os.path.exists(raw_file):
            with open(raw_file) as f:
                leads = json.load(f)
        else:
            leads = []

        update_status(hunt_id, HuntStage.SCRAPING, 25,
                      f"Scraped {len(leads)} leads from Google Maps",
                      leads_found=len(leads))

        if not leads:
            update_status(hunt_id, HuntStage.COMPLETED, 100,
                          "No leads found for this search",
                          completed_at=datetime.now().isoformat())
            return

        # ====================================================================
        # Stage 2: Finding Owners / LinkedIn (25-50%)
        # ====================================================================
        update_status(hunt_id, HuntStage.FINDING_OWNERS, 30,
                      "⚡ Finding decision makers via Teleport Snoop (10 parallel)...")

        run_script([
            sys.executable, "execution/find_owner_linkedin.py",
            "--file", raw_file,
            "--output", owners_file,
            "--concurrency", "10"
        ], "LinkedIn Snoop (Parallel)", timeout=120)

        # Load enriched leads
        if os.path.exists(owners_file):
            with open(owners_file) as f:
                leads = json.load(f)

        owners_found = sum(1 for l in leads if l.get("owner_name"))
        linkedin_found = sum(1 for l in leads if l.get("linkedin_url"))

        update_status(hunt_id, HuntStage.FINDING_OWNERS, 50,
                      f"Found {owners_found} owners, {linkedin_found} LinkedIn profiles",
                      owners_found=owners_found)

        # ====================================================================
        # Stage 3: TROY - Perpetual Discovery Loop (50-75%)
        # 4-Layer CEO/Owner Discovery System
        # ====================================================================
        update_status(hunt_id, HuntStage.GETTING_EMAILS, 55,
                      "🔥 TROY: Initiating Perpetual Discovery Loop...")

        add_log(hunt_id, "=" * 50, "INFO")
        add_log(hunt_id, "TROY DISCOVERY SYSTEM - 4 Layer Attack", "INFO")
        add_log(hunt_id, "Layer 1: Apollo + Anymailfinder Database", "INFO")
        add_log(hunt_id, "Layer 2: Web Sniffing (About/Team/Contact)", "INFO")
        add_log(hunt_id, "Layer 3: DuckDuckGo Recursive Search", "INFO")
        add_log(hunt_id, "Layer 4: Email Pattern Guessing", "INFO")
        add_log(hunt_id, "Fail-Safe: Business email fallback", "INFO")
        add_log(hunt_id, "=" * 50, "INFO")

        # Run Troy on all leads
        update_status(hunt_id, HuntStage.GETTING_EMAILS, 60,
                      f"🔍 Troy hunting {len(leads)} targets (5 parallel workers)...")

        leads = enrich_leads_with_troy(leads, hunt_id, max_workers=5)

        # Save enriched leads
        with open(emails_file, "w") as f:
            json.dump(leads, f, indent=2)

        # Calculate stats
        owners_found = sum(1 for l in leads if l.get("owner_name"))
        emails_found = sum(1 for l in leads if l.get("anymailfinder_email") or l.get("email"))
        linkedin_found = sum(1 for l in leads if l.get("linkedin_url"))

        # Source breakdown
        source_counts = {}
        for lead in leads:
            src = lead.get("email_source", "none")
            source_counts[src] = source_counts.get(src, 0) + 1

        add_log(hunt_id, f"📊 Troy Results: {owners_found} owners, {emails_found} emails, {linkedin_found} LinkedIn", "SUCCESS")
        for src, count in source_counts.items():
            if src != "none":
                add_log(hunt_id, f"   • {src}: {count} emails", "INFO")

        update_status(hunt_id, HuntStage.GETTING_EMAILS, 75,
                      f"✓ Troy complete: {emails_found} emails found",
                      emails_found=emails_found,
                      owners_found=owners_found)

        # ====================================================================
        # Stage 3.5: Insight Engine (75-80%)
        # Scrape websites and generate AI insights for each lead
        # ====================================================================
        update_status(hunt_id, HuntStage.GENERATING_OUTREACH, 76,
                      "🔮 Insight Engine: Analyzing websites...")

        add_log(hunt_id, "=" * 50, "INFO")
        add_log(hunt_id, "INSIGHT ENGINE - Website Intelligence", "INFO")
        add_log(hunt_id, "• Scraping key pages (home, about, services)", "INFO")
        add_log(hunt_id, "• Generating AI-powered quick insights", "INFO")
        add_log(hunt_id, "• Using FREE Llama 3.3 70B via OpenRouter", "INFO")
        add_log(hunt_id, "=" * 50, "INFO")

        # Only process leads that have websites
        leads_with_websites = [l for l in leads if l.get("website")]
        if leads_with_websites:
            leads = enrich_leads_with_insights(leads, hunt_id, max_workers=3)

            # Save insights-enriched leads
            with open(emails_file, "w") as f:
                json.dump(leads, f, indent=2)

            insights_count = sum(1 for l in leads if l.get("quick_insights") and len(l.get("quick_insights", [])) > 1)
            add_log(hunt_id, f"✓ Insight Engine: {insights_count}/{len(leads_with_websites)} websites analyzed", "SUCCESS")
        else:
            add_log(hunt_id, "⚠ No leads with websites to analyze", "WARN")

        update_status(hunt_id, HuntStage.GENERATING_OUTREACH, 80,
                      f"✓ Insights complete for {len(leads_with_websites)} leads")

        # ====================================================================
        # Stage 4: Generating Outreach (80-95%)
        # ====================================================================
        update_status(hunt_id, HuntStage.GENERATING_OUTREACH, 80,
                      "⚡ AI Outreach: Parallel email generation (10 workers)...")

        current_data_file = emails_file if os.path.exists(emails_file) else (owners_file if os.path.exists(owners_file) else raw_file)

        run_script([
            sys.executable, "execution/generate_outreach_emails.py",
            "--leads", current_data_file,
            "--sender", "Tedca",
            "--concurrency", "10"
        ], "AI Outreach Generator (Parallel)", timeout=120)

        # Load final leads
        if os.path.exists(current_data_file):
            with open(current_data_file) as f:
                final_leads = json.load(f)
        else:
            final_leads = leads

        # Merge email drafts
        drafts_file = ".tmp/email_drafts.json"
        if os.path.exists(drafts_file):
            with open(drafts_file) as f:
                draft_list = json.load(f)
                drafts = {d.get("to", ""): d for d in draft_list}

            for lead in final_leads:
                email = lead.get("anymailfinder_email") or lead.get("email")
                if email and email in drafts:
                    lead["email_draft"] = {
                        "subject": drafts[email].get("subject"),
                        "body": drafts[email].get("body"),
                        "gmail_draft_id": drafts[email].get("gmail_draft_id")
                    }

        # Add IDs and computed fields
        for i, lead in enumerate(final_leads):
            lead["id"] = lead.get("place_id") or f"lead_{hunt_id}_{i}"

            amf_email = lead.get("anymailfinder_email")
            scraper_email = lead.get("email")
            is_scraper_verified = lead.get("email_verification", {}).get("deliverable") is True

            lead["has_direct_contact"] = bool(amf_email or scraper_email or lead.get("linkedin_url"))
            lead["email_verified"] = bool(amf_email or (scraper_email and is_scraper_verified))

        # Save final results
        final_output = ".tmp/leads.json"
        with open(final_output, "w") as f:
            json.dump(final_leads, f, indent=2)

        # Store in memory and database
        leads_store[hunt_id] = final_leads
        hunts[hunt_id]["leads"] = final_leads

        # Complete!
        final_owners = sum(1 for l in final_leads if l.get("owner_name"))
        final_emails = sum(1 for l in final_leads if l.get("anymailfinder_email"))

        update_status(hunt_id, HuntStage.COMPLETED, 100,
                      f"Hunt complete! {final_owners} owners, {final_emails} emails",
                      leads_found=len(final_leads),
                      owners_found=final_owners,
                      emails_found=final_emails,
                      completed_at=datetime.now().isoformat())

        add_log(hunt_id, f"Pipeline complete! Results saved to {final_output}", "SUCCESS")

    except Exception as e:
        update_status(hunt_id, HuntStage.FAILED, 0,
                      f"Pipeline failed: {str(e)[:100]}",
                      error=str(e))
        add_log(hunt_id, f"Pipeline error: {e}", "ERROR")


# ============================================================================
# Gmail OAuth Helper
# ============================================================================

GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly'
]

def check_gmail_token() -> dict:
    """Check if Gmail token exists and is valid."""
    token_path = "token.json"
    creds_path = "credentials.json"

    result = {
        "has_credentials": os.path.exists(creds_path),
        "has_token": os.path.exists(token_path),
        "token_valid": False,
        "email": None
    }

    if result["has_token"]:
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)
            result["token_valid"] = not creds.expired or creds.refresh_token is not None

            # Try to get email
            if result["token_valid"]:
                try:
                    from googleapiclient.discovery import build
                    service = build('gmail', 'v1', credentials=creds)
                    profile = service.users().getProfile(userId='me').execute()
                    result["email"] = profile.get('emailAddress')
                except:
                    pass
        except Exception as e:
            result["error"] = str(e)

    return result


def initiate_gmail_oauth() -> str:
    """Start Gmail OAuth flow and return authorization URL."""
    try:
        from google_auth_oauthlib.flow import Flow

        if not os.path.exists("credentials.json"):
            raise Exception("credentials.json not found. Download from Google Cloud Console.")

        flow = Flow.from_client_secrets_file(
            "credentials.json",
            scopes=GMAIL_SCOPES,
            redirect_uri="http://localhost:8000/api/gmail/callback"
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return auth_url

    except Exception as e:
        raise Exception(f"OAuth setup failed: {e}")


def complete_gmail_oauth(code: str) -> dict:
    """Complete OAuth flow with authorization code."""
    try:
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_secrets_file(
            "credentials.json",
            scopes=GMAIL_SCOPES,
            redirect_uri="http://localhost:8000/api/gmail/callback"
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token
        with open("token.json", "w") as f:
            f.write(creds.to_json())

        # Get email address
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()

        return {
            "success": True,
            "email": profile.get('emailAddress'),
            "message": "Gmail connected successfully!"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="LeadSnipe API",
    description="API for LeadSnipe lead generation pipeline",
    version="2.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup and load existing hunts."""
    init_database()

    # Load existing hunts from database into memory
    for hunt in db_get_all_hunts():
        hunts[hunt["hunt_id"]] = {
            "hunt_id": hunt["hunt_id"],
            "niche": hunt["niche"],
            "location": hunt["location"],
            "city": hunt["city"],
            "state": hunt["state"],
            "limit": hunt["limit_count"],
            "status": hunt["status"],
            "progress_percent": hunt["progress_percent"],
            "stage_message": hunt["stage_message"],
            "leads_found": hunt["leads_found"],
            "owners_found": hunt["owners_found"],
            "emails_found": hunt["emails_found"],
            "started_at": hunt["started_at"],
            "completed_at": hunt["completed_at"],
            "error": hunt["error"]
        }
        if hunt["leads_json"]:
            leads_store[hunt["hunt_id"]] = json.loads(hunt["leads_json"])

    print(f"[DB] Loaded {len(hunts)} hunts from database")


@app.get("/")
async def root():
    """Health check endpoint."""
    gmail_status = check_gmail_token()
    return {
        "status": "ok",
        "service": "LeadSnipe API",
        "version": "2.0.0",
        "gmail_connected": gmail_status["token_valid"],
        "gmail_email": gmail_status.get("email")
    }


@app.post("/api/hunt", response_model=HuntResponse)
async def start_hunt(request: HuntRequest):
    """Start a new lead hunt."""

    hunt_id = f"hunt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    try:
        city, state = parse_location(request.location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Initialize hunt status
    hunt_data = {
        "hunt_id": hunt_id,
        "user_id": request.user_id,
        "niche": request.niche,
        "location": request.location,
        "city": city,
        "state": state,
        "limit": request.limit,
        "status": HuntStage.QUEUED.value,
        "progress_percent": 0,
        "stage_message": "Preparing hunt...",
        "leads_found": 0,
        "owners_found": 0,
        "emails_found": 0,
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None
    }

    hunts[hunt_id] = hunt_data
    db_save_hunt(hunt_data)

    # Initialize log queue
    log_queues[hunt_id] = deque(maxlen=1000)

    # Start pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline_with_logging,
        args=(hunt_id, request.niche, state, request.limit),
        daemon=True
    )
    thread.start()

    add_log(hunt_id, f"Hunt started: {request.niche} in {city}, {state} (limit: {request.limit})")

    return HuntResponse(
        hunt_id=hunt_id,
        message=f"Hunt started. Poll /api/hunt/{hunt_id}/status for updates."
    )


@app.get("/api/hunt/{hunt_id}/status", response_model=HuntStatus)
async def get_hunt_status(hunt_id: str):
    """Get hunt status for polling."""

    # Check memory first, then database
    if hunt_id not in hunts:
        db_hunt = db_get_hunt(hunt_id)
        if db_hunt:
            hunts[hunt_id] = db_hunt
        else:
            raise HTTPException(status_code=404, detail="Hunt not found")

    hunt = hunts[hunt_id]
    return HuntStatus(
        hunt_id=hunt["hunt_id"],
        niche=hunt.get("niche", "Unknown"),
        location=hunt.get("location", "Unknown"),
        limit=hunt.get("limit", 0),
        status=hunt["status"],
        progress_percent=hunt["progress_percent"],
        stage_message=hunt["stage_message"],
        leads_found=hunt["leads_found"],
        owners_found=hunt["owners_found"],
        emails_found=hunt["emails_found"],
        started_at=hunt["started_at"],
        completed_at=hunt.get("completed_at"),
        error=hunt.get("error")
    )


@app.get("/api/hunt/{hunt_id}/logs")
async def stream_logs(hunt_id: str, request: Request):
    """Stream logs for a hunt via Server-Sent Events (SSE)."""

    if hunt_id not in hunts and not db_get_hunt(hunt_id):
        raise HTTPException(status_code=404, detail="Hunt not found")

    async def event_generator():
        last_index = 0

        # First, send any existing logs from database
        existing_logs = db_get_logs(hunt_id)
        for log in existing_logs:
            yield f"data: {json.dumps(log)}\n\n"
            last_index = log["id"]

        # Then stream new logs
        while True:
            if await request.is_disconnected():
                break

            # Check for new logs in database
            new_logs = db_get_logs(hunt_id, last_index)
            for log in new_logs:
                yield f"data: {json.dumps(log)}\n\n"
                last_index = log["id"]

            # Check if hunt is complete
            hunt = hunts.get(hunt_id)
            if hunt and hunt.get("status") in ["completed", "failed"]:
                yield f"data: {json.dumps({'type': 'complete', 'status': hunt['status']})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/leads", response_model=LeadListResponse)
async def get_leads(
    hunt_id: Optional[str] = None,
    filter: str = "all",
    limit: int = 100,
    offset: int = 0
):
    """Get all leads, optionally filtered."""

    leads = []

    if hunt_id:
        if hunt_id in leads_store:
            leads = leads_store[hunt_id]
        else:
            # Try loading from database
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT leads_json FROM hunts WHERE hunt_id = ?', (hunt_id,))
                row = cursor.fetchone()
                if row and row['leads_json']:
                    leads = json.loads(row['leads_json'])
                    leads_store[hunt_id] = leads # Cache it
    
    if not leads and os.path.exists(".tmp/leads.json"):
        with open(".tmp/leads.json") as f:
            leads = json.load(f)

    if filter == "decision_makers":
        leads = [l for l in leads if l.get("owner_name")]
    elif filter == "verified_email":
        leads = [l for l in leads if l.get("anymailfinder_email")]
    elif filter == "linkedin":
        leads = [l for l in leads if l.get("linkedin_url")]

    for i, lead in enumerate(leads):
        if "id" not in lead:
            lead["id"] = lead.get("place_id", f"lead_{i}")
        lead["has_direct_contact"] = bool(
            lead.get("anymailfinder_email") or lead.get("linkedin_url")
        )
        lead["email_verified"] = bool(lead.get("anymailfinder_email"))

    total = len(leads)
    paginated = leads[offset:offset + limit]

    return LeadListResponse(leads=paginated, total=total, hunt_id=hunt_id)


@app.get("/api/leads/{lead_id}")
async def get_lead(lead_id: str):
    """Get single lead by ID."""

    all_leads = []

    for leads in leads_store.values():
        all_leads.extend(leads)

    if not all_leads and os.path.exists(".tmp/leads.json"):
        with open(".tmp/leads.json") as f:
            all_leads = json.load(f)

    for lead in all_leads:
        if lead.get("id") == lead_id or lead.get("place_id") == lead_id:
            lead["has_direct_contact"] = bool(
                lead.get("anymailfinder_email") or lead.get("linkedin_url")
            )
            lead["email_verified"] = bool(lead.get("anymailfinder_email"))
            return lead

    raise HTTPException(status_code=404, detail="Lead not found")


# ============================================================================
# Insight Engine API Endpoints
# ============================================================================

class InsightQuestionRequest(BaseModel):
    question: str = Field(..., example="What can I sell them?")

class SendEmailRequest(BaseModel):
    to: str = Field(..., example="ceo@example.com")
    subject: str = Field(..., example="Quick question about your business")
    body: str = Field(..., example="Hi, I noticed...")

class BulkSendRequest(BaseModel):
    emails: List[SendEmailRequest]


@app.get("/api/lead/{lead_id}/insights")
async def get_lead_insights(lead_id: str):
    """Get cached insights for a lead."""
    # Find the lead
    for hunt_id, leads in leads_store.items():
        for lead in leads:
            if lead.get("id") == lead_id or lead.get("place_id") == lead_id:
                return {
                    "lead_id": lead_id,
                    "business_name": lead.get("name"),
                    "quick_insights": lead.get("quick_insights", []),
                    "website_content": lead.get("website_content", {}),
                    "has_content": bool(lead.get("website_content", {}).get("raw_text"))
                }

    raise HTTPException(status_code=404, detail="Lead not found")


@app.post("/api/lead/{lead_id}/insights/generate")
async def generate_lead_insights(lead_id: str):
    """Generate or regenerate insights for a lead."""
    # Find the lead
    for hunt_id, leads in leads_store.items():
        for lead in leads:
            if lead.get("id") == lead_id or lead.get("place_id") == lead_id:
                website = lead.get("website")
                business_name = lead.get("name", "Unknown Business")

                # Scrape website
                scraped = scrape_website_for_insights(website)
                lead["website_content"] = scraped

                # Generate insights
                if scraped.get("raw_text"):
                    insights = generate_quick_insights(scraped["raw_text"], business_name)
                    lead["quick_insights"] = insights
                else:
                    lead["quick_insights"] = ["Website could not be scraped"]

                return {
                    "lead_id": lead_id,
                    "business_name": business_name,
                    "quick_insights": lead["quick_insights"],
                    "pages_scraped": scraped.get("pages_scraped", []),
                    "word_count": scraped.get("word_count", 0)
                }

    raise HTTPException(status_code=404, detail="Lead not found")


@app.post("/api/lead/{lead_id}/insights/ask")
async def ask_lead_question(lead_id: str, request: InsightQuestionRequest):
    """Ask any question about a lead's website."""
    # Find the lead
    for hunt_id, leads in leads_store.items():
        for lead in leads:
            if lead.get("id") == lead_id or lead.get("place_id") == lead_id:
                website_content = lead.get("website_content", {})
                raw_text = website_content.get("raw_text", "")
                business_name = lead.get("name", "Unknown Business")

                # If no content, try to scrape first
                if not raw_text:
                    scraped = scrape_website_for_insights(lead.get("website"))
                    raw_text = scraped.get("raw_text", "")
                    lead["website_content"] = scraped

                # Answer the question
                answer = ask_insight_question(raw_text, business_name, request.question)

                return {
                    "lead_id": lead_id,
                    "business_name": business_name,
                    "question": request.question,
                    "answer": answer
                }

    raise HTTPException(status_code=404, detail="Lead not found")


# ============================================================================
# Email Send API Endpoints
# ============================================================================

@app.post("/api/email/send")
async def api_send_email(request: SendEmailRequest):
    """Send a single email via Gmail."""
    result = send_gmail_email(
        to_email=request.to,
        subject=request.subject,
        body=request.body
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "success": True,
        "message_id": result["message_id"],
        "to": request.to
    }


@app.post("/api/email/send-bulk")
async def api_send_bulk_emails(request: BulkSendRequest):
    """Send multiple emails with rate limiting (3s delay)."""
    if len(request.emails) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 emails per batch")

    emails = [{"to": e.to, "subject": e.subject, "body": e.body} for e in request.emails]
    results = send_bulk_emails(emails, delay_seconds=3)

    success_count = sum(1 for r in results if r["success"])

    return {
        "total": len(results),
        "success_count": success_count,
        "failed_count": len(results) - success_count,
        "results": results
    }


@app.get("/api/hunts")
async def list_hunts(user_id: Optional[str] = None):
    """List all hunts (from database for persistence)."""
    with get_db() as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute('SELECT * FROM hunts WHERE user_id = ? ORDER BY started_at DESC', (user_id,))
        else:
            cursor.execute('SELECT * FROM hunts ORDER BY started_at DESC')
        rows = cursor.fetchall()
        all_hunts = [dict(row) for row in rows]
    
    return {
        "hunts": all_hunts,
        "total": len(all_hunts)
    }


# ============================================================================
# Gmail OAuth Endpoints
# ============================================================================

@app.get("/api/gmail/status")
async def gmail_status():
    """Check Gmail connection status."""
    return check_gmail_token()


@app.get("/api/gmail/connect")
async def gmail_connect():
    """Initiate Gmail OAuth flow."""
    try:
        auth_url = initiate_gmail_oauth()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gmail/callback")
async def gmail_callback(code: str = None, error: str = None):
    """Handle OAuth callback from Google."""
    if error:
        return RedirectResponse(
            url=f"/.tmp/leadsnipe_settings.html?gmail_error={error}"
        )

    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    result = complete_gmail_oauth(code)

    if result["success"]:
        # Redirect to settings page with success
        return RedirectResponse(
            url=f"/.tmp/leadsnipe_settings.html?gmail_connected=true&email={result['email']}"
        )
    else:
        return RedirectResponse(
            url=f"/.tmp/leadsnipe_settings.html?gmail_error={result['error']}"
        )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("  LeadSnipe API Server v2.0")
    print("="*60)
    print("\n  Core Endpoints:")
    print("    POST /api/hunt              - Start a new hunt")
    print("    GET  /api/hunt/{id}/status  - Poll for progress")
    print("    GET  /api/hunt/{id}/logs    - Stream logs (SSE)")
    print("    GET  /api/leads             - Get all leads")
    print("    GET  /api/hunts             - List all hunts (persisted)")
    print("\n  Gmail OAuth:")
    print("    GET  /api/gmail/status      - Check Gmail connection")
    print("    GET  /api/gmail/connect     - Start OAuth flow")
    print("    GET  /api/gmail/callback    - OAuth callback")
    print("\n  Starting server at http://127.0.0.1:8000")
    print("="*60 + "\n")

    uvicorn.run(app, host="127.0.0.1", port=8000)
