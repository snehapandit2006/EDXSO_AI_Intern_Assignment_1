from app.personalization.generator import generate_fallback_message
from app.personalization.validators import validate_outreach_message, count_words


def test_fallback_message_word_counts():
    """Verify generated pitches strictly satisfy word count limits (Email: 60-90, DM: 15-30)."""
    sample_creator = {
        "name": "Sarah Chen",
        "username": "sarah.ai.dev",
        "sub_niche": "Artificial Intelligence",
        "recent_content": ["Cursor AI vs VS Code"]
    }

    msg = generate_fallback_message(sample_creator, "AI Productivity Campaign")
    email_count = count_words(msg["email_body"])
    dm_count = count_words(msg["dm_body"])

    assert 60 <= email_count <= 90, f"Email word count {email_count} outside [60, 90]"
    assert 15 <= dm_count <= 30, f"DM word count {dm_count} outside [15, 30]"


def test_validator_detects_out_of_bounds():
    """Verify validator flags invalid word count bounds."""
    creator = {"name": "Sarah"}
    invalid_msg = {
        "email_body": "Short email.",
        "dm_body": "Too short."
    }
    is_valid, errors, counts = validate_outreach_message(invalid_msg, creator)
    assert not is_valid
    assert len(errors) >= 2
