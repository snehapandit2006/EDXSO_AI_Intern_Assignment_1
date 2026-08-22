from datetime import datetime, timezone
from typing import List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.config import EXPORTS_DATA_DIR
from app.database.models import OutreachLog
from app.outreach.sender import send_email_outreach


def process_outreach_for_qualified(
    db: Session,
    campaign_id: int,
    personalized_creators: List[Dict[str, Any]],
    send_mode: str = "simulation"
) -> List[Dict[str, Any]]:
    """
    Process email outreach for all qualified creators with duplicate prevention checks.
    Updates OutreachLog in SQLite DB and exports outreach_tracker.csv.
    """
    print(f"[Outreach Layer] Processing outreach sending layer for {len(personalized_creators)} creators (Mode: {send_mode})...")

    outreach_records = []

    for item in personalized_creators:
        creator_id = item.get("db_creator_id")
        email = item.get("contact_email", "Not Found")
        username = item.get("username", "")
        message = item.get("message", {})
        message_id = item.get("db_message_id")

        # 1. Check for Duplicate Outreach Record in DB
        existing_log = db.query(OutreachLog).filter_by(campaign_id=campaign_id, creator_id=creator_id).first()
        if existing_log and existing_log.sent:
            print(f" -> [DUPLICATE PREVENTED] Outreach already sent to @{username} (Log ID: {existing_log.id}). Skipping.")
            outreach_records.append({
                "creator_id": creator_id,
                "username": username,
                "email": email,
                "status": "DUPLICATE",
                "sent": True,
                "sent_at": existing_log.sent_at.isoformat() if existing_log.sent_at else None,
                "error": "Duplicate outreach attempt prevented by database constraint."
            })
            continue

        # 2. Execute Outreach Sending or Simulation
        subject = message.get("email_subject", "Collaboration Opportunity")
        body = message.get("email_body", "")

        success, status, notes = send_email_outreach(email, subject, body, send_mode=send_mode)
        now_dt = datetime.now(timezone.utc)

        # 3. Save / Update Database Record
        if not existing_log:
            log_entry = OutreachLog(
                campaign_id=campaign_id,
                creator_id=creator_id,
                email=email,
                message_id=message_id,
                status=status,
                sent=success,
                sent_at=now_dt if success else None,
                error=notes if not success else None
            )
            db.add(log_entry)
        else:
            existing_log.email = email
            existing_log.message_id = message_id
            existing_log.status = status
            existing_log.sent = success
            existing_log.sent_at = now_dt if success else None
            existing_log.error = notes if not success else None

        db.commit()

        outreach_records.append({
            "creator_id": creator_id,
            "username": username,
            "email": email,
            "status": status,
            "sent": success,
            "sent_at": now_dt.isoformat() if success else None,
            "notes": notes
        })

    # Export Outreach Tracker CSV
    if outreach_records:
        df = pd.DataFrame(outreach_records)
        csv_path = EXPORTS_DATA_DIR / "outreach_tracker.csv"
        df.to_csv(csv_path, index=False)
        print(f"[Outreach Layer] Tracker updated. Exported outreach tracking history to: {csv_path}")

    return outreach_records
