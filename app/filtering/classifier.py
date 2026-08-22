from typing import Dict, Any
from app.config import QUALIFIED_THRESHOLD, REVIEW_THRESHOLD
from app.filtering.rules import check_hard_gates
from app.filtering.scoring import calculate_total_score


def classify_creator(creator: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate creator through strict hard gates and soft scoring matrix.
    Produces classification (QUALIFIED, REVIEW, REJECTED), total score, and explicit justification.
    """
    hard_pass, route_to_review, hard_failed_criteria, hard_reason = check_hard_gates(creator)
    scoring_result = calculate_total_score(creator)
    total_score = scoring_result["total_score"]

    if not hard_pass:
        # Failed critical platform or follower count bounds -> REJECTED
        return {
            "niche_score": scoring_result["niche_score"],
            "content_score": scoring_result["content_score"],
            "engagement_score": scoring_result["engagement_score"],
            "brand_fit_score": scoring_result["brand_fit_score"],
            "brand_fit_reason": scoring_result["brand_fit_reason"],
            "geography_score": scoring_result["geography_score"],
            "audience_fit_score": scoring_result["audience_fit_score"],
            "total_score": total_score,
            "classification": "REJECTED",
            "filter_reason": hard_reason,
            "failed_criteria": hard_failed_criteria
        }

    if route_to_review:
        # Passed follower/platform bounds, but missing mandatory email or engagement metric -> REVIEW
        return {
            "niche_score": scoring_result["niche_score"],
            "content_score": scoring_result["content_score"],
            "engagement_score": scoring_result["engagement_score"],
            "brand_fit_score": scoring_result["brand_fit_score"],
            "brand_fit_reason": scoring_result["brand_fit_reason"],
            "geography_score": scoring_result["geography_score"],
            "audience_fit_score": scoring_result["audience_fit_score"],
            "total_score": total_score,
            "classification": "REVIEW",
            "filter_reason": f"{hard_reason} (Soft Score: {total_score}/100)",
            "failed_criteria": hard_failed_criteria
        }

    # All hard gates passed! Evaluate soft score thresholds
    if total_score >= QUALIFIED_THRESHOLD:
        classification = "QUALIFIED"
        reason = f"Passed all hard gates and exceeded qualification score threshold ({total_score} >= {QUALIFIED_THRESHOLD}). High tech relevance ({scoring_result['niche_score']}/100) and brand fit ({scoring_result['brand_fit_score']}/100)."
        failed = []
    elif total_score >= REVIEW_THRESHOLD:
        classification = "REVIEW"
        reason = f"Passed hard gates, but soft score ({total_score}/100) falls in manual review range ({REVIEW_THRESHOLD}-{QUALIFIED_THRESHOLD - 1})."
        failed = [f"Score below qualification threshold ({total_score} < {QUALIFIED_THRESHOLD})"]
    else:
        classification = "REJECTED"
        reason = f"Passed hard gates, but soft score ({total_score}/100) falls below minimum threshold ({REVIEW_THRESHOLD})."
        failed = [f"Score below minimum acceptance threshold ({total_score} < {REVIEW_THRESHOLD})"]

    return {
        "niche_score": scoring_result["niche_score"],
        "content_score": scoring_result["content_score"],
        "engagement_score": scoring_result["engagement_score"],
        "brand_fit_score": scoring_result["brand_fit_score"],
        "brand_fit_reason": scoring_result["brand_fit_reason"],
        "geography_score": scoring_result["geography_score"],
        "audience_fit_score": scoring_result["audience_fit_score"],
        "total_score": total_score,
        "classification": classification,
        "filter_reason": reason,
        "failed_criteria": failed
    }
