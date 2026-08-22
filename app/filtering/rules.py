from typing import List, Tuple, Dict, Any
from app.config import TARGET_PLATFORM, MIN_FOLLOWERS, MAX_FOLLOWERS

VALID_PLATFORMS = [
    "instagram", "github", "dev.to", "youtube", "hashnode", "twitter", "x",
    "github & dev.to tech platforms", "multi-platform tech (github, dev.to, tech blogs)", "technology"
]


def check_hard_gates(creator: Dict[str, Any]) -> Tuple[bool, bool, List[str], str]:
    """
    Evaluate strict hard qualification gates.
    Returns:
      (hard_pass, missing_data_route_to_review, failed_criteria_list, gate_reason)
    """
    failed = []
    platform = str(creator.get("platform", "GitHub")).strip()
    followers = creator.get("followers")
    email = creator.get("contact_email", "Not Found")
    eng_rate = creator.get("engagement_rate")

    # 1. Platform Gate
    if platform.lower() not in VALID_PLATFORMS:
        failed.append(f"Platform mismatch: '{platform}' not in valid creator platforms")

    # 2. Follower Bound Gate (5,000 <= followers <= 100,000)
    is_follower_missing = False
    if followers is None or followers == "Not Found" or followers == "":
        is_follower_missing = True
    else:
        try:
            val_followers = int(followers)
            if val_followers < MIN_FOLLOWERS:
                failed.append(f"Follower count below minimum threshold: {val_followers:,} < {MIN_FOLLOWERS:,}")
            elif val_followers > MAX_FOLLOWERS:
                failed.append(f"Follower count exceeds micro-influencer cap: {val_followers:,} > {MAX_FOLLOWERS:,}")
        except (ValueError, TypeError):
            is_follower_missing = True

    # If platform mismatch or explicit follower bound fail -> Instant REJECTED
    if failed:
        return False, False, failed, f"Failed hard criteria: {', '.join(failed)}"

    # 3. Mandatory Data Availability Gates (Email, Engagement Rate, Follower Count)
    missing_fields = []
    if is_follower_missing:
        missing_fields.append("Follower count missing ('Not Found')")

    if email == "Not Found" or not email:
        missing_fields.append("Mandatory contact email missing ('Not Found')")

    is_eng_missing = False
    if eng_rate is None or eng_rate == "Not Found" or eng_rate == "":
        is_eng_missing = True
    else:
        try:
            val = float(eng_rate)
            if val <= 0:
                is_eng_missing = True
        except (ValueError, TypeError):
            is_eng_missing = True

    if is_eng_missing:
        missing_fields.append("Mandatory engagement rate missing ('Not Found')")

    # If missing follower count, email, or engagement -> Route to REVIEW (not QUALIFIED)
    if missing_fields:
        reason = f"Routed to REVIEW: {', '.join(missing_fields)}"
        return True, True, missing_fields, reason

    return True, False, [], "Passed all hard qualification gates."
