import re
from typing import Dict, Any, Tuple, List
from app.config import EMAIL_MIN_WORDS, EMAIL_MAX_WORDS, DM_MIN_WORDS, DM_MAX_WORDS


def count_words(text: str) -> int:
    """Count clean words in text block."""
    if not text:
        return 0
    words = re.findall(r"\b[\w'-]+\b", text)
    return len(words)


def validate_outreach_message(
    message_data: Dict[str, Any],
    creator: Dict[str, Any]
) -> Tuple[bool, List[str], Dict[str, int]]:
    """
    Validate word count limits and dynamic personalization signals.
    Returns: (is_valid, validation_errors_list, word_counts_dict)
    """
    errors = []
    email_body = message_data.get("email_body", "").strip()
    dm_body = message_data.get("dm_body", "").strip()

    email_words = count_words(email_body)
    dm_words = count_words(dm_body)

    counts = {
        "email_word_count": email_words,
        "dm_word_count": dm_words
    }

    # 1. Email Word Count Validation (60-90 words)
    if email_words < EMAIL_MIN_WORDS or email_words > EMAIL_MAX_WORDS:
        errors.append(f"Email word count ({email_words} words) outside strict limits ({EMAIL_MIN_WORDS}-{EMAIL_MAX_WORDS} words)")

    # 2. DM Word Count Validation (15-30 words)
    if dm_words < DM_MIN_WORDS or dm_words > DM_MAX_WORDS:
        errors.append(f"DM word count ({dm_words} words) outside strict limits ({DM_MIN_WORDS}-{DM_MAX_WORDS} words)")

    # 3. Creator Name Signal Check
    name = creator.get("name", "")
    first_name = name.split()[0] if name else ""
    if first_name and first_name.lower() not in email_body.lower():
        errors.append(f"Email body missing creator first name ('{first_name}')")

    return len(errors) == 0, errors, counts
