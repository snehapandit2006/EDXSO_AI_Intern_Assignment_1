import time
import os
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from app.config import SEND_MODE


def send_email_outreach(
    to_email: str,
    subject: str,
    body: str,
    send_mode: str = SEND_MODE
) -> Tuple[bool, str, str]:
    """
    Execute email outreach sending or simulation.
    Returns: (success_bool, status_string, error_or_notes_string)
    """
    if not to_email or to_email == "Not Found":
        return False, "SKIPPED", "No valid email address found for creator."

    if send_mode.lower() == "simulation":
        # Simulate Network Send Latency
        time.sleep(0.1)
        timestamp = datetime.now(timezone.utc).isoformat()
        notes = f"Simulated outreach sent successfully to {to_email} at {timestamp}"
        return True, "SENT", notes

    elif send_mode.lower() == "smtp":
        # Optional Live SMTP sending implementation
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", 587))
            smtp_user = os.getenv("SMTP_USERNAME", "")
            smtp_pass = os.getenv("SMTP_PASSWORD", "")

            if not smtp_user or not smtp_pass:
                return False, "FAILED", "SMTP credentials missing in environment (.env)"

            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            timestamp = datetime.now(timezone.utc).isoformat()
            return True, "SENT", f"Live SMTP email sent successfully to {to_email} at {timestamp}"

        except Exception as e:
            return False, "FAILED", f"SMTP sending error: {str(e)}"

    else:
        return False, "FAILED", f"Unknown SEND_MODE: '{send_mode}'"


def prepare_dm_workflow(dm_body: str, username: str) -> Dict[str, str]:
    """Format Instagram DM payload for copyable manual workflow."""
    return {
        "platform": "Instagram",
        "username": username,
        "profile_url": f"https://instagram.com/{username}",
        "dm_body": dm_body,
        "instructions": "Click 'Copy DM' and open creator's Instagram profile link to send DM directly."
    }
