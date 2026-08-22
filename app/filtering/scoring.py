from typing import Dict, Any, Tuple, Optional
from app.config import SCORING_WEIGHTS, SUB_NICHES


def calculate_tech_relevance_score(creator: Dict[str, Any]) -> float:
    """Calculate Technology / Niche Relevance score (0-100)."""
    score = 50.0
    bio = creator.get("bio", "").lower()
    sub_niche = creator.get("sub_niche", "").lower()
    themes = [t.lower() for t in creator.get("content_themes", [])]

    # Keyword check against campaign sub-niches
    keywords = ["ai", "genai", "llm", "developer", "coding", "python", "software", "devtools", "saas", "tech"]
    matches = sum(1 for kw in keywords if kw in bio or kw in sub_niche or any(kw in t for t in themes))

    score += min(matches * 10.0, 45.0)
    if "ai" in bio or "llm" in bio or "dev tools" in bio:
        score += 5.0

    return min(max(score, 0.0), 100.0)


def calculate_content_relevance_score(creator: Dict[str, Any]) -> float:
    """Calculate Content Quality & Format Relevance score (0-100)."""
    score = 60.0
    style = creator.get("content_style", "").lower()
    recent = [str(r).lower() for r in creator.get("recent_content", [])]

    if any(k in style for k in ["educational", "tutorial", "code breakdown", "demo"]):
        score += 20.0
    if len(recent) >= 2:
        score += 15.0
    if "carousel" in style or "reels" in style:
        score += 5.0

    return min(max(score, 0.0), 100.0)


def calculate_engagement_score(creator: Dict[str, Any]) -> float:
    """Calculate Engagement Score (0-100) based on niche benchmarks (3.0% - 7.0%)."""
    eng_rate = creator.get("engagement_rate")
    if eng_rate is None or eng_rate == "Not Found" or eng_rate == "":
        return 0.0

    try:
        val = float(eng_rate)
    except (ValueError, TypeError):
        return 0.0

    if val <= 0:
        return 0.0

    # 4.5% - 7.0% -> 100 pts, 3.0% - 4.5% -> 80 pts, <3.0% -> scaled down
    if val >= 4.5:
        return min(80.0 + (val - 4.5) * 8.0, 100.0)
    elif val >= 3.0:
        return 60.0 + (val - 3.0) * 13.3
    else:
        return max(val * 20.0, 10.0)


def calculate_brand_fit_score(creator: Dict[str, Any]) -> Tuple[float, str]:
    """Calculate Brand Fit Score (0-100) and rationale."""
    score = 70.0
    reasons = []

    bio = creator.get("bio", "").lower()

    if any(term in bio for term in ["founder", "engineer", "lead", "educator", "researcher", "devrel"]):
        score += 15.0
        reasons.append("Professional role aligned with developer tools campaign")

    if any(term in bio for term in ["collab", "contact", "dm for", "inquiries"]):
        score += 10.0
        reasons.append("Open to brand collaborations and sponsorship outreach")

    if "hardware reviews" in bio or "unboxing" in bio:
        score -= 10.0
        reasons.append("Consumer hardware focus may lessen developer software alignment")

    if not reasons:
        reasons.append("Standard developer audience and clean professional bio")

    final_score = min(max(score, 0.0), 100.0)
    return final_score, "; ".join(reasons)


def calculate_audience_fit_score(creator: Dict[str, Any]) -> Tuple[Optional[float], bool]:
    """
    Calculate Audience & Geography Fit score (0-100).
    Returns (score, data_available_boolean).
    If demographic data is 'Not Found', returns (None, False).
    """
    geog = creator.get("audience_geography", "Not Found")
    age = creator.get("audience_age", "Not Found")
    gender = creator.get("audience_gender", "Not Found")
    creator_geog = creator.get("creator_geography", "Not Found")

    if geog == "Not Found" and age == "Not Found" and creator_geog == "Not Found":
        return None, False

    score = 70.0
    if "United States" in geog or "United States" in creator_geog or "UK" in geog or "Canada" in geog or "Germany" in geog or "India" in geog:
        score += 15.0
    if "20-35" in age or "21-35" in age or "22-38" in age or "18-32" in age:
        score += 15.0

    return min(max(score, 0.0), 100.0), True


def calculate_total_score(creator: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate weighted total score with dynamic weight reweighting if demographic data is missing.
    """
    tech_score = calculate_tech_relevance_score(creator)
    content_score = calculate_content_relevance_score(creator)
    eng_score = calculate_engagement_score(creator)
    brand_score, brand_reason = calculate_brand_fit_score(creator)
    audience_score, audience_data_present = calculate_audience_fit_score(creator)

    weights = dict(SCORING_WEIGHTS)

    if not audience_data_present:
        # Exclude audience_fit weight and reweight remaining weights to sum to 1.0
        w_aud = weights.pop("audience_fit", 0.10)
        remaining_sum = sum(weights.values())
        if remaining_sum > 0:
            weights = {k: v / remaining_sum for k, v in weights.items()}

        total_score = (
            tech_score * weights.get("tech_relevance", 0.333) +
            content_score * weights.get("content_relevance", 0.278) +
            eng_score * weights.get("engagement", 0.222) +
            brand_score * weights.get("brand_fit", 0.167)
        )
    else:
        total_score = (
            tech_score * weights.get("tech_relevance", 0.30) +
            content_score * weights.get("content_relevance", 0.25) +
            eng_score * weights.get("engagement", 0.20) +
            brand_score * weights.get("brand_fit", 0.15) +
            (audience_score or 0.0) * weights.get("audience_fit", 0.10)
        )

    return {
        "niche_score": round(tech_score, 2),
        "content_score": round(content_score, 2),
        "engagement_score": round(eng_score, 2),
        "brand_fit_score": round(brand_score, 2),
        "brand_fit_reason": brand_reason,
        "geography_score": round(audience_score, 2) if audience_score is not None else None,
        "audience_fit_score": round(audience_score, 2) if audience_score is not None else None,
        "audience_data_present": audience_data_present,
        "total_score": round(total_score, 2)
    }
