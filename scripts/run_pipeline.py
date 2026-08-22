"""
Master E2E Pipeline Script: EDXSO AI Influencer Outreach System
Executes complete pipeline: Discovery -> Enrichment -> Filtering -> Personalization
    -> HUMAN REVIEW GATE -> Outreach -> Database Persistence.

Usage:
  python -m scripts.run_pipeline             # Full pipeline (auto-approve QUALIFIED)
  python -m scripts.run_pipeline --review    # Full pipeline with interactive review gate
"""
import sys
import json
from pathlib import Path

# Force UTF-8 standard output encoding for cross-platform compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import CAMPAIGN_TITLE, SEND_MODE
from app.database.models import init_db, SessionLocal
from app.database.repository import (
    get_or_create_campaign, upsert_creator, save_filter_result, save_message, save_outreach_log
)
from app.discovery import run_discovery
from app.enrichment import run_enrichment
from app.filtering import run_filtering
from app.personalization import run_personalization
from app.outreach.tracker import process_outreach_for_qualified


def _human_review_gate(personalized_creators: list) -> list:
    """
    EDXSO REVIEW GATE: Present each personalized pitch for human approval
    before it proceeds to the outreach sending layer.
    Returns only the approved creators.
    """
    print("\n" + "=" * 70)
    print("       [!] HUMAN REVIEW GATE - MANDATORY APPROVAL REQUIRED  [!]       ")
    print("=" * 70)
    print(f"  {len(personalized_creators)} personalized pitches are pending review.")
    print("  Only APPROVED pitches will be sent to the outreach layer.")
    print("=" * 70)

    approved = []
    for i, creator in enumerate(personalized_creators, 1):
        msg = creator.get("message", {})
        print(f"\n[{i}/{len(personalized_creators)}] Creator: {creator.get('name')} (@{creator.get('username')})")
        print(f"  Email Subject : {msg.get('email_subject', 'N/A')}")
        print(f"  Email Words   : {msg.get('email_word_count', '?')} (Target: 60-90)")
        print(f"  DM Words      : {msg.get('dm_word_count', '?')} (Target: 15-30)")
        print(f"  Validation    : {msg.get('validation_status', 'UNKNOWN')}")
        print(f"  Gen Model     : {msg.get('generation_model', 'N/A')}")
        print(f"\n  --- Email Body Preview ---")
        preview = msg.get("email_body", "")[:200]
        print(f"  {preview}...")
        print(f"\n  --- DM Body ---")
        print(f"  {msg.get('dm_body', '')}")
        print()

        while True:
            choice = input(f"  Approve pitch for @{creator.get('username')}? [y/n/q to quit]: ").strip().lower()
            if choice == "y":
                creator["approval_status"] = "APPROVED"
                approved.append(creator)
                print(f"  [+] APPROVED - @{creator.get('username')}")
                break
            elif choice == "n":
                creator["approval_status"] = "REJECTED_BY_REVIEWER"
                print(f"  [-] REJECTED - @{creator.get('username')} will be skipped.")
                break
            elif choice == "q":
                print(f"\n  [STOP] Review session terminated by user. Approved so far: {len(approved)}")
                return approved
            else:
                print("  Please enter 'y', 'n', or 'q'.")

    print(f"\n[Review Gate] Review complete: {len(approved)}/{len(personalized_creators)} pitches approved.")
    return approved


def execute_full_pipeline(interactive_review: bool = False):
    print("=" * 70)
    print("      EDXSO AUTOMATED MICRO-INFLUENCER OUTREACH PIPELINE       ")
    print("=" * 70)

    # 1. Database Setup
    init_db()
    db = SessionLocal()
    campaign = get_or_create_campaign(db, title=CAMPAIGN_TITLE)
    print(f"\n[Pipeline Init] Database connected. Active Campaign ID: {campaign.id} ('{campaign.title}')")

    # 2. Stage 1: Creator Discovery (real HTTP GET from public sources)
    raw_creators = run_discovery()

    # 3. Stage 2: Profile Enrichment
    enriched_creators = run_enrichment(raw_creators)

    # Persist all enriched creators into Database
    db_creators = []
    for creator in enriched_creators:
        c_obj = upsert_creator(db, campaign.id, creator)
        creator["db_creator_id"] = c_obj.id
        db_creators.append(creator)

    # 4. Stage 3: Filtering & Explainability Classification
    filter_results = run_filtering(db_creators)

    # Persist Filter Results to DB
    for category in ["QUALIFIED", "REVIEW", "REJECTED"]:
        for creator in filter_results[category]:
            c_id = creator["db_creator_id"]
            save_filter_result(db, campaign.id, c_id, creator)

    qualified_creators = filter_results["QUALIFIED"]

    # 5. Stage 4: Gemini AI Personalization for Qualified Creators
    personalized_creators = run_personalization(qualified_creators, campaign_title=campaign.title)

    # Persist all generated messages to DB (with PENDING approval status)
    for creator in personalized_creators:
        c_id = creator["db_creator_id"]
        msg = creator["message"]
        msg["approval_status"] = "PENDING"
        msg_obj = save_message(db, campaign.id, c_id, msg)
        creator["db_message_id"] = msg_obj.id

    # 6. MANDATORY REVIEW GATE
    if interactive_review:
        approved_creators = _human_review_gate(personalized_creators)
    else:
        # Auto-approve all QUALIFIED pitches in non-interactive mode (CI / Streamlit)
        print(f"\n[Review Gate] Auto-approve mode: {len(personalized_creators)} pitches approved for outreach.")
        for c in personalized_creators:
            c["approval_status"] = "APPROVED"
        approved_creators = personalized_creators

    if not approved_creators:
        print("\n[Pipeline] No pitches approved for sending. Outreach layer skipped.")
        db.close()
        return

    # 7. Stage 5: Outreach Sending Simulation & Tracker Layer
    outreach_summary = process_outreach_for_qualified(
        db,
        campaign.id,
        approved_creators,
        send_mode=SEND_MODE
    )

    db.close()

    print("\n" + "=" * 70)
    print("                    PIPELINE EXECUTION SUMMARY                  ")
    print("=" * 70)
    print(f" Total Raw Discovered Records : {len(raw_creators)}")
    print(f" Total Normalized Records     : {len(enriched_creators)}")
    print(f" Qualified Creators Shortlist : {len(filter_results['QUALIFIED'])}")
    print(f" Review Pipeline Creators     : {len(filter_results['REVIEW'])}")
    print(f" Rejected Creators            : {len(filter_results['REJECTED'])}")
    print(f" AI Pitches Generated         : {len(personalized_creators)}")
    print(f" Pitches Approved for Sending : {len(approved_creators)}")
    print(f" Outreach Sending Logged      : {len(outreach_summary)}")
    print("=" * 70)
    print("SUCCESS: All datasets saved to data/raw/, data/processed/, and data/exports/.")


if __name__ == "__main__":
    review_mode = "--review" in sys.argv or "-r" in sys.argv
    execute_full_pipeline(interactive_review=review_mode)
