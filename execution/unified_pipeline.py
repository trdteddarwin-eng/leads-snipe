#!/usr/bin/env python3
"""
Unified Lead Generation Pipeline for LeadSnipe

Main orchestrator that ALWAYS runs:
1. Lead Discovery (Engine Zero - SerpAPI)
2. Email Verification (FREE 3-layer)
3. LinkedIn Discovery (FREE multi-strategy)
4. Paid Fallback (OPTIONAL - disabled by default)

Usage:
    from unified_pipeline import UnifiedPipeline, PipelineConfig

    config = PipelineConfig(target_leads=200)
    pipeline = UnifiedPipeline(config)
    leads = pipeline.run("Dentist", "Newark, NJ")
"""

import os
import json
import threading
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Local imports
try:
    from engine_zero import EngineZero, EngineConfig, Lead
    from verify_email import verify_email, check_syntax, check_mx, check_smtp
    from linkedin_finder_unified import LinkedInFinder
    from rate_limiter import RateLimiter, get_limiter
    from icebreaker_engine import IcebreakerEngine
except ImportError:
    # Handle running from different directories
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from engine_zero import EngineZero, EngineConfig, Lead
    from verify_email import verify_email, check_syntax, check_mx, check_smtp
    from linkedin_finder_unified import LinkedInFinder
    from rate_limiter import RateLimiter, get_limiter


@dataclass
class PipelineConfig:
    """Configuration for the unified pipeline."""
    # Target
    target_leads: int = 200

    # Workers
    discovery_workers: int = 5
    scraping_workers: int = 50
    verification_workers: int = 20
    linkedin_workers: int = 10

    # Features
    enable_email_verification: bool = True  # Always ON
    enable_linkedin_discovery: bool = True  # Always ON
    enable_paid_fallback: bool = False      # Disabled by default
    paid_fallback_max_spend: float = 2.0    # Max $ for paid APIs if enabled

    # Engine Zero config
    max_cities: int = 15
    radius_miles: int = 20
    scrape_timeout: int = 10

    # Verification config
    do_smtp_check: bool = True              # Full 3-layer verification

    # Personalization config
    enable_icebreaker: bool = True          # Strategic personalization
    icebreaker_workers: int = 10

    # Hooks for progress reporting
    hunt_id: Optional[str] = None
    add_log: Optional[Callable] = None
    update_status: Optional[Callable] = None


class UnifiedPipeline:
    """
    Unified lead generation pipeline that ALWAYS verifies emails
    and discovers LinkedIn profiles using FREE methods first.

    Stages:
    1. Discovery - Engine Zero (SerpAPI + 50 parallel scrapers)
    2. Email Verification - FREE 3-layer (Syntax/DNS/SMTP)
    3. LinkedIn Discovery - FREE multi-strategy
    4. Paid Fallback - Optional Anymailfinder for unverified emails
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

        # Stats tracking
        self.stats = {
            "stage": "init",
            "leads_discovered": 0,
            "emails_verified": 0,
            "emails_unverified": 0,
            "linkedin_found": 0,
            "paid_api_calls": 0,
            "paid_api_spend": 0.0,
            "duration_seconds": 0,
        }
        self._stats_lock = threading.Lock()

    def _log(self, message: str, level: str = "INFO"):
        """Log message via hook or print."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        print(formatted, flush=True)

        if self.config.add_log and self.config.hunt_id:
            try:
                self.config.add_log(self.config.hunt_id, message, level)
            except Exception:
                pass

    def _update_progress(self, stage: str, progress: int, message: str, **kwargs):
        """Update progress via hook."""
        if self.config.update_status and self.config.hunt_id:
            try:
                self.config.update_status(
                    self.config.hunt_id,
                    stage,
                    progress,
                    message,
                    **kwargs
                )
            except Exception as e:
                print(f"Progress update error: {e}")

    # =========================================================================
    # Stage 1: Discovery (Engine Zero)
    # =========================================================================

    def stage1_discover(self, industry: str, location: str) -> List[Lead]:
        """
        Run Engine Zero for lead discovery.

        Returns list of Lead objects with scraped emails and text.
        """
        self._log("=" * 60)
        self._log("STAGE 1: Lead Discovery (Engine Zero)")
        self._log("=" * 60)

        with self._stats_lock:
            self.stats["stage"] = "discovery"

        # Configure Engine Zero
        engine_config = EngineConfig(
            target_leads=int(self.config.target_leads * 1.25),  # Fetch extra for filtering
            max_cities=self.config.max_cities,
            radius_miles=self.config.radius_miles,
            discovery_workers=self.config.discovery_workers,
            scraping_workers=self.config.scraping_workers,
            scrape_timeout=self.config.scrape_timeout,
            hunt_id=self.config.hunt_id,
            add_log=self.config.add_log,
            update_status=self.config.update_status,
        )

        engine = EngineZero(engine_config)

        try:
            leads = engine.run(industry, location, self.config.target_leads)

            with self._stats_lock:
                self.stats["leads_discovered"] = len(leads)

            self._log(f"Discovery complete: {len(leads)} leads")
            return leads

        finally:
            engine.shutdown()

    # =========================================================================
    # Stage 2: Email Verification (FREE)
    # =========================================================================

    def stage2_verify_emails(self, leads: List[Lead]) -> List[Lead]:
        """
        Verify all emails using FREE 3-layer verification.
        Runs in parallel with configurable workers.
        """
        self._log("=" * 60)
        self._log("STAGE 2: Email Verification (FREE)")
        self._log("=" * 60)

        with self._stats_lock:
            self.stats["stage"] = "verification"

        # Count leads with emails
        leads_with_email = [l for l in leads if l.email]
        self._log(f"Verifying {len(leads_with_email)}/{len(leads)} leads with emails")

        self._update_progress("getting_emails", 50, f"Verifying {len(leads_with_email)} emails...")

        # MX cache for efficiency (same domain = same result)
        mx_cache: Dict[str, tuple] = {}  # domain -> (has_mx, reason, servers)
        cache_lock = threading.Lock()

        verified_count = [0]
        unverified_count = [0]

        def verify_single_lead(lead: Lead) -> Lead:
            """Verify a single lead's email."""
            if not lead.email:
                return lead

            email = lead.email.strip().lower()

            # Layer 1: Syntax check
            syntax_valid, syntax_msg = check_syntax(email)
            if not syntax_valid:
                lead.email_verified = False
                lead.email_verification_reason = f"Syntax: {syntax_msg}"
                with self._stats_lock:
                    unverified_count[0] += 1
                return lead

            # Layer 2: MX check (with caching)
            domain = email.split('@')[1]
            with cache_lock:
                if domain in mx_cache:
                    has_mx, mx_msg, mx_servers = mx_cache[domain]
                else:
                    has_mx, mx_msg, mx_servers = check_mx(email)
                    mx_cache[domain] = (has_mx, mx_msg, mx_servers)

            if not has_mx:
                lead.email_verified = False
                lead.email_verification_reason = f"MX: {mx_msg}"
                with self._stats_lock:
                    unverified_count[0] += 1
                return lead

            # Layer 3: SMTP check (if enabled)
            if self.config.do_smtp_check:
                smtp_valid, smtp_msg = check_smtp(email, mx_servers)
                if not smtp_valid:
                    lead.email_verified = False
                    lead.email_verification_reason = f"SMTP: {smtp_msg}"
                    with self._stats_lock:
                        unverified_count[0] += 1
                    return lead

            # All checks passed
            lead.email_verified = True
            lead.email_verification_reason = "Verified"
            with self._stats_lock:
                verified_count[0] += 1

            return lead

        # Parallel verification
        with ThreadPoolExecutor(max_workers=self.config.verification_workers) as executor:
            futures = {executor.submit(verify_single_lead, lead): lead for lead in leads}
            completed = 0

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    lead = futures[future]
                    lead.email_verified = False
                    lead.email_verification_reason = f"Error: {str(e)}"

                completed += 1
                if completed % 20 == 0:
                    progress = 50 + int((completed / len(leads)) * 15)
                    self._update_progress("getting_emails", progress,
                                         f"Verified {completed}/{len(leads)} emails")

        # Update stats
        with self._stats_lock:
            self.stats["emails_verified"] = verified_count[0]
            self.stats["emails_unverified"] = unverified_count[0]

        self._log(f"Verification complete: {verified_count[0]} verified, {unverified_count[0]} unverified")
        self._update_progress("getting_emails", 65, f"Verified {verified_count[0]} emails")

        return leads

    # =========================================================================
    # Stage 3: LinkedIn Discovery (FREE)
    # =========================================================================

    def stage3_find_linkedin(self, leads: List[Lead]) -> List[Lead]:
        """
        Find LinkedIn profiles using FREE multi-strategy approach.
        """
        self._log("=" * 60)
        self._log("STAGE 3: LinkedIn Discovery (FREE)")
        self._log("=" * 60)

        with self._stats_lock:
            self.stats["stage"] = "linkedin"

        self._update_progress("finding_owners", 70, f"Finding LinkedIn for {len(leads)} leads...")

        # Convert Leads to dicts for LinkedIn finder
        lead_dicts = []
        for lead in leads:
            lead_dict = lead.to_dict() if hasattr(lead, 'to_dict') else dict(lead.__dict__)
            lead_dicts.append(lead_dict)

        # Progress callback
        def progress_cb(completed: int, total: int):
            progress = 70 + int((completed / total) * 20)
            self._update_progress("finding_owners", progress,
                                 f"LinkedIn: {completed}/{total}")

        # Run LinkedIn finder
        finder = LinkedInFinder(workers=self.config.linkedin_workers, verbose=True)
        enriched_dicts = finder.find_batch(lead_dicts, progress_callback=progress_cb)

        # Update Lead objects with LinkedIn data
        linkedin_count = 0
        for i, lead in enumerate(leads):
            enriched = enriched_dicts[i]
            lead.linkedin_url = enriched.get("linkedin_url")
            lead.owner_name = enriched.get("owner_name") or lead.owner_name
            lead.owner_first_name = enriched.get("owner_first_name")
            lead.linkedin_source = enriched.get("linkedin_source")

            if lead.linkedin_url:
                linkedin_count += 1

        with self._stats_lock:
            self.stats["linkedin_found"] = linkedin_count

        self._log(f"LinkedIn discovery complete: {linkedin_count}/{len(leads)} found")
        self._update_progress("finding_owners", 90, f"Found {linkedin_count} LinkedIn profiles")

        return leads

    # =========================================================================
    # Stage 4: Paid Fallback (Optional)
    # =========================================================================

    def stage4_paid_fallback(self, leads: List[Lead]) -> List[Lead]:
        """
        Use paid APIs (Anymailfinder) for leads without verified emails.
        Only runs if enable_paid_fallback=True.
        """
        if not self.config.enable_paid_fallback:
            self._log("Paid fallback disabled, skipping")
            return leads

        self._log("=" * 60)
        self._log("STAGE 4: Paid Fallback (Anymailfinder)")
        self._log("=" * 60)

        with self._stats_lock:
            self.stats["stage"] = "fallback"

        # Find leads that need email enrichment
        needs_enrichment = []
        for lead in leads:
            # Needs enrichment if: no email OR email not verified
            if not lead.email or not getattr(lead, 'email_verified', False):
                if lead.website:  # Only if we have a website to work with
                    needs_enrichment.append(lead)

        self._log(f"Leads needing enrichment: {len(needs_enrichment)}")

        if not needs_enrichment:
            return leads

        # Check budget
        cost_per_email = 0.02  # Anymailfinder approximate cost
        max_calls = int(self.config.paid_fallback_max_spend / cost_per_email)
        to_enrich = needs_enrichment[:max_calls]

        self._log(f"Budget allows {max_calls} API calls, enriching {len(to_enrich)} leads")

        # Try to import Anymailfinder
        try:
            from anymailfinder_email import find_decision_maker_email
        except ImportError:
            self._log("Anymailfinder module not available, skipping fallback")
            return leads

        api_calls = 0
        for lead in to_enrich:
            try:
                # Extract domain from website
                from urllib.parse import urlparse
                domain = urlparse(lead.website).netloc
                if domain.startswith('www.'):
                    domain = domain[4:]

                # Call Anymailfinder
                result = find_decision_maker_email(domain)

                if result and result.get("email"):
                    lead.email = result["email"]
                    lead.email_verified = True
                    lead.email_verification_reason = "Anymailfinder"
                    lead.owner_name = result.get("full_name") or lead.owner_name

                    with self._stats_lock:
                        self.stats["emails_verified"] += 1

                api_calls += 1
                with self._stats_lock:
                    self.stats["paid_api_calls"] = api_calls
                    self.stats["paid_api_spend"] = api_calls * cost_per_email

            except Exception as e:
                self._log(f"Anymailfinder error: {e}")

        self._log(f"Paid fallback complete: {api_calls} API calls, ${self.stats['paid_api_spend']:.2f} spent")

        return leads

    # =========================================================================
    # Stage 5: Personalization (Icebreakers)
    # =========================================================================

    async def stage5_generate_icebreakers(self, leads: List[Lead]) -> List[Lead]:
        """
        Generate human-like opening lines for verified leads.
        """
        if not self.config.enable_icebreaker:
            self._log("Icebreaker personalization disabled, skipping")
            return leads

        self._log("=" * 60)
        self._log("STAGE 5: Strategic Personalization (Icebreaker Engine)")
        self._log("=" * 60)

        with self._stats_lock:
            self.stats["stage"] = "personalization"

        # Prioritize leads with emails
        to_personalize = [l for l in leads if l.email]
        self._log(f"Personalizing {len(to_personalize)} leads with emails")

        self._update_progress("generating_outreach", 90, f"Generating {len(to_personalize)} icebreakers...")

        engine = IcebreakerEngine()
        
        async def process_lead(lead: Lead):
            lead_dict = lead.to_dict()
            result = await engine.get_icebreaker(lead_dict)
            lead.icebreaker = result.get("icebreaker")
            return lead

        # Process in parallel with semaphore to respect concurrency
        sem = asyncio.Semaphore(self.config.icebreaker_workers)

        async def sem_process(lead: Lead):
            async with sem:
                return await process_lead(lead)

        tasks = [sem_process(l) for l in to_personalize]
        completed = 0
        
        for coro in asyncio.as_completed(tasks):
            await coro
            completed += 1
            if completed % 10 == 0:
                progress = 90 + int((completed / max(1, len(to_personalize))) * 10)
                self._update_progress("generating_outreach", progress, 
                                     f"Personalized {completed}/{len(to_personalize)} leads")

        self._log(f"Personalization complete: {len(to_personalize)} icebreakers generated")
        self._update_progress("completed", 100, "Hunt complete with personalization")
        
        return leads

    # =========================================================================
    # Main Entry Point
    # =========================================================================

    async def run(self, industry: str, location: str, target: Optional[int] = None) -> List[Lead]:
        """
        Execute the full unified pipeline.

        Args:
            industry: Business type (e.g., "Dentist")
            location: Target location (e.g., "Newark, NJ")
            target: Target lead count (default: config.target_leads)

        Returns:
            List of fully enriched Lead objects with:
            - email (verified)
            - email_verified flag
            - linkedin_url
            - owner_name
        """
        target = target or self.config.target_leads
        start_time = datetime.now()

        self._log("=" * 70)
        self._log("  UNIFIED PIPELINE - Optimized Lead Generation")
        self._log("=" * 70)
        self._log(f"Industry: {industry}")
        self._log(f"Location: {location}")
        self._log(f"Target: {target} leads")
        self._log(f"Email verification: ENABLED (FREE)")
        self._log(f"LinkedIn discovery: ENABLED (FREE)")
        self._log(f"Paid fallback: {'ENABLED ($' + str(self.config.paid_fallback_max_spend) + ' cap)' if self.config.enable_paid_fallback else 'DISABLED'}")
        self._log("")

        try:
            # Stage 1: Discovery
            self._update_progress("scraping", 5, "Starting lead discovery...")
            leads = self.stage1_discover(industry, location)

            if not leads:
                self._log("No leads found!", "ERROR")
                self._update_progress("failed", 0, "No leads found")
                return []

            # Stage 2: Email Verification (ALWAYS)
            leads = self.stage2_verify_emails(leads)

            # Stage 3: LinkedIn Discovery (ALWAYS)
            leads = self.stage3_find_linkedin(leads)

            # Stage 4: Paid Fallback (OPTIONAL)
            if self.config.enable_paid_fallback:
                leads = self.stage4_paid_fallback(leads)

            # Stage 5: Personalization (Icebreakers) - Async call
            leads = await self.stage5_generate_icebreakers(leads)

            # Trim to target
            leads = leads[:target]

            # Final stats
            duration = (datetime.now() - start_time).total_seconds()
            with self._stats_lock:
                self.stats["duration_seconds"] = duration

            emails_verified = sum(1 for l in leads if getattr(l, 'email_verified', False))
            linkedin_found = sum(1 for l in leads if getattr(l, 'linkedin_url', None))
            emails_total = sum(1 for l in leads if l.email)

            self._log("")
            self._log("=" * 70)
            self._log("  PIPELINE COMPLETE")
            self._log("=" * 70)
            self._log(f"Total leads: {len(leads)}")
            self._log(f"Emails found: {emails_total}")
            self._log(f"Emails verified: {emails_verified} ({100*emails_verified//max(1,emails_total)}%)")
            self._log(f"LinkedIn found: {linkedin_found} ({100*linkedin_found//max(1,len(leads))}%)")
            self._log(f"Duration: {duration:.1f}s")
            if self.config.enable_paid_fallback:
                self._log(f"Paid API spend: ${self.stats['paid_api_spend']:.2f}")
            self._log("=" * 70)

            self._update_progress(
                "completed", 100,
                f"Complete: {len(leads)} leads, {emails_verified} verified, {linkedin_found} LinkedIn",
                leads_found=len(leads),
                emails_found=emails_verified,
                owners_found=linkedin_found
            )

            return leads

        except Exception as e:
            self._log(f"Pipeline error: {e}", "ERROR")
            self._update_progress("failed", 0, str(e))
            raise

    def get_stats(self) -> Dict:
        """Get pipeline statistics."""
        with self._stats_lock:
            return dict(self.stats)


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Unified Lead Generation Pipeline")
    parser.add_argument("--industry", "-i", required=True, help="Business type")
    parser.add_argument("--location", "-l", required=True, help="Target location")
    parser.add_argument("--target", "-t", type=int, default=200, help="Target leads")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--no-smtp", action="store_true", help="Skip SMTP verification")
    parser.add_argument("--paid-fallback", action="store_true", help="Enable paid API fallback")
    parser.add_argument("--max-spend", type=float, default=2.0, help="Max paid API spend")

    args = parser.parse_args()

    config = PipelineConfig(
        target_leads=args.target,
        do_smtp_check=not args.no_smtp,
        enable_paid_fallback=args.paid_fallback,
        paid_fallback_max_spend=args.max_spend,
    )

    pipeline = UnifiedPipeline(config)
    leads = asyncio.run(pipeline.run(args.industry, args.location, args.target))

    # Save output
    output_path = args.output or f".tmp/unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(output_path) or ".tmp", exist_ok=True)

    output_data = []
    for lead in leads:
        data = lead.to_dict() if hasattr(lead, 'to_dict') else dict(lead.__dict__)
        # Add verification fields
        data["email_verified"] = getattr(lead, 'email_verified', False)
        data["linkedin_url"] = getattr(lead, 'linkedin_url', None)
        data["owner_name"] = getattr(lead, 'owner_name', None)
        output_data.append(data)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nSaved {len(leads)} leads to: {output_path}")
    print(f"Stats: {pipeline.get_stats()}")


if __name__ == "__main__":
    main()
