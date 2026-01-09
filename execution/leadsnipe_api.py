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
from collections import deque
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel, Field

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
    """Parse 'City, State' or 'City, ST' into (city, state_abbrev)."""
    parts = location.split(",")
    if len(parts) < 2:
        words = location.strip().split()
        if len(words) >= 2:
            potential_state = words[-1].strip()
            city = " ".join(words[:-1])
            if len(potential_state) == 2:
                return city, potential_state.upper()
        raise ValueError(f"Invalid location format: {location}. Expected 'City, State'")

    city = parts[0].strip()
    state_raw = parts[1].strip().lower()

    if len(state_raw) == 2:
        return city, state_raw.upper()

    state = STATE_ABBREV.get(state_raw)
    if not state:
        raise ValueError(f"Unknown state: {state_raw}")

    return city, state


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
            sys.executable, "execution/n8n_gmaps_scraper.py",
            "--industry", niche,
            "--state", state,
            "--target-leads", str(limit),
            "--output", raw_file
        ], "Google Maps Scraper", timeout=300)

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
        # Stage 3: Email verification & Enrichment (50-75%)
        # ====================================================================
        update_status(hunt_id, HuntStage.GETTING_EMAILS, 55,
                      "Verifying existing email addresses...")

        current_data_file = owners_file if os.path.exists(owners_file) else raw_file

        run_script([
            sys.executable, "execution/verify_email.py",
            "--file", current_data_file,
            "--output", owners_file,
            "--no-smtp"
        ], "Email Verification", timeout=300)

        # Load and clean undeliverable emails
        if os.path.exists(owners_file):
            with open(owners_file) as f:
                leads = json.load(f)

            cleaned_count = 0
            for lead in leads:
                verif = lead.get("email_verification", {})
                if lead.get("email") and not verif.get("deliverable"):
                    lead["email"] = None
                    cleaned_count += 1

            if cleaned_count > 0:
                add_log(hunt_id, f"Cleaned {cleaned_count} undeliverable emails")
                with open(owners_file, "w") as f:
                    json.dump(leads, f, indent=2)

        # Anymailfinder enrichment
        update_status(hunt_id, HuntStage.GETTING_EMAILS, 65,
                      "⚡ Smart-Hunter: CEO/Owner email enrichment (10 parallel)...")

        run_script([
            sys.executable, "execution/anymailfinder_email.py",
            "--file", owners_file if os.path.exists(owners_file) else raw_file,
            "--output", emails_file,
            "--concurrency", "10"
        ], "Smart-Hunter Email (Parallel)", timeout=120)

        # Load final leads
        if os.path.exists(emails_file):
            with open(emails_file) as f:
                leads = json.load(f)
        elif os.path.exists(owners_file):
            with open(owners_file) as f:
                leads = json.load(f)

        emails_found = sum(1 for l in leads if l.get("anymailfinder_email") or l.get("email"))

        update_status(hunt_id, HuntStage.GETTING_EMAILS, 75,
                      f"Found {emails_found} verified emails",
                      emails_found=emails_found)

        # ====================================================================
        # Stage 4: Generating Outreach (75-95%)
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
