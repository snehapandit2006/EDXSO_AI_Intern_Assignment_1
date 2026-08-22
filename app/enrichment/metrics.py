import re
from typing import Tuple, Optional


def parse_follower_count(val: any) -> int:
    """Normalize follower count strings (e.g. '24.5K', '100,000', 28400) to integer."""
    if isinstance(val, (int, float)):
        return int(val)
    if not val:
        return 0

    s = str(val).strip().upper()
    try:
        if "K" in s:
            num = float(re.sub(r"[^0-9.]", "", s))
            return int(num * 1000)
        elif "M" in s:
            num = float(re.sub(r"[^0-9.]", "", s))
            return int(num * 1000000)
        else:
            num_str = re.sub(r"[^0-9]", "", s)
            return int(num_str) if num_str else 0
    except Exception:
        return 0


def calculate_engagement_rate(
    engagement_val: Optional[float] = None,
    followers: int = 0,
    likes_sample: Optional[list] = None,
    comments_sample: Optional[list] = None
) -> Tuple[Optional[float], str, int]:
    """
    Calculate engagement rate and return (rate_percent, method_description, sample_size).
    If metric is unavailable or uncalculable, returns (None, "Not Found", 0).
    """
    if engagement_val is not None and isinstance(engagement_val, (int, float)) and engagement_val > 0:
        return (round(float(engagement_val), 2), "Average likes + comments on 10 recent posts / followers", 10)

    if likes_sample and comments_sample and followers > 0:
        try:
            avg_likes = sum(likes_sample) / len(likes_sample)
            avg_comments = sum(comments_sample) / len(comments_sample)
            rate = ((avg_likes + avg_comments) / followers) * 100.0
            return (round(rate, 2), f"Calculated from {len(likes_sample)} recent post sample", len(likes_sample))
        except Exception:
            pass

    return (None, "Not Found", 0)
