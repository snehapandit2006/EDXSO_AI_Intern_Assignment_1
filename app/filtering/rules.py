from typing import List, Tuple, Dict, Any
from app.config import TARGET_PLATFORM, MIN_FOLLOWERS, MAX_FOLLOWERS


def check_hard_gates(creator: Dict[str, Any]) -> Tuple[bool, bool, List[str], str]:
    """
    Evaluate strict hard qualification gates.
    Returns:
      (hard_pass, missing_data_route_to_review, failed_criteria_list, gate_reason)
    """
    failed = []
    platform = creator.get("platform", "Instagram")
    followers = creator.get("followers", 0)
    email = creator.get("contact_email", "Not Found")
    eng_rate = creator.get("engagement_rate")

    # 1. Platform Gate
    if platform.lower() != TARGET_PLATFORM.lower():
        failed.append(f"Platform mismatch: '{platform}' != '{TARGET_PLATFORM}'")

    # 2. Follower Bound Gate (5,000 <= followers <= 100,000)
    if followers < MIN_FOLLOWERS:
        failed.append(f"Follower count below minimum threshold: {followers:,} < {MIN_FOLLOWERS:,}")
    elif followers > MAX_FOLLOWERS:
        failed.append(f"Follower count exceeds micro-influencer cap: {followers:,} > {MAX_FOLLOWERS:,}")

    # If platform or follower bounds fail -> Instant REJECTED
    if failed:
        return False, False, failed, f"Failed hard criteria: {', '.join(failed)}"

    # 3. Mandatory Contact Email & Engagement Rate Gates
    missing_fields = []
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

    # If missing email or engagement -> Must route to REVIEW (not QUALIFIED)
    if missing_fields:
        reason = f"Routed to REVIEW: {', '.join(missing_fields)}"
        return True, True, missing_fields, reason

    return True, False, [], "Passed all hard qualification gates."
