from app.database.models import init_db, SessionLocal, Campaign, Creator, OutreachLog
from app.outreach.sender import send_email_outreach
from app.outreach.tracker import process_outreach_for_qualified


def test_sending_simulation():
    """Verify simulation mode returns success without actual SMTP network call."""
    success, status, notes = send_email_outreach("test@domain.com", "Subject", "Body text", send_mode="simulation")
    assert success
    assert status == "SENT"
    assert "Simulated outreach sent" in notes


def test_duplicate_outreach_prevention(monkeypatch, tmp_path):
    """Verify database unique constraint prevents duplicate outreach to same creator in campaign."""
    monkeypatch.setattr("app.outreach.tracker.EXPORTS_DATA_DIR", tmp_path)
    init_db()
    db = SessionLocal()

    campaign = Campaign(title="Test Dup Campaign", target_niche="Tech", platform="Instagram")
    db.add(campaign)
    db.commit()

    creator = Creator(
        campaign_id=campaign.id,
        name="Test Dup",
        username="test_dup",
        profile_url="https://instagram.com/test_dup",
        followers=10000,
        contact_email="dup@domain.com",
        source="Test",
        source_url="https://test.com"
    )
    db.add(creator)
    db.commit()

    item = {
        "db_creator_id": creator.id,
        "username": "test_dup",
        "contact_email": "dup@domain.com",
        "message": {"email_subject": "Hi", "email_body": "Body"},
        "db_message_id": None
    }

    # First send -> SENT
    res1 = process_outreach_for_qualified(db, campaign.id, [item], send_mode="simulation")
    assert res1[0]["status"] == "SENT"

    # Second send attempt -> DUPLICATE PREVENTED
    res2 = process_outreach_for_qualified(db, campaign.id, [item], send_mode="simulation")
    assert res2[0]["status"] == "DUPLICATE"

    db.close()
