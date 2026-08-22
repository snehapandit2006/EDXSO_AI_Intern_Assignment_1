from app.filtering.rules import check_hard_gates
from app.filtering.classifier import classify_creator


def test_hard_gate_follower_rejection():
    """Verify follower counts > 100k or < 5k are rejected."""
    over_limit = {
        "platform": "Instagram",
        "followers": 145000,
        "contact_email": "test@domain.com",
        "engagement_rate": 4.5
    }
    pass_hard, route_review, failed, reason = check_hard_gates(over_limit)
    assert not pass_hard
    assert any("cap" in f for f in failed)


def test_missing_email_routes_to_review():
    """Verify creators missing contact email are routed to REVIEW rather than QUALIFIED."""
    missing_email = {
        "name": "Elena",
        "username": "elena_test",
        "platform": "Instagram",
        "followers": 15000,
        "contact_email": "Not Found",
        "engagement_rate": 5.2,
        "bio": "Python AI dev",
        "sub_niche": "Artificial Intelligence"
    }
    result = classify_creator(missing_email)
    assert result["classification"] == "REVIEW"
    assert "Mandatory contact email missing" in result["filter_reason"]


def test_missing_engagement_routes_to_review():
    """Verify creators missing engagement rate are routed to REVIEW."""
    missing_eng = {
        "name": "Liam",
        "username": "liam_test",
        "platform": "Instagram",
        "followers": 12000,
        "contact_email": "liam@domain.com",
        "engagement_rate": None,
        "bio": "DevOps Architect",
        "sub_niche": "Developer Tools"
    }
    result = classify_creator(missing_eng)
    assert result["classification"] == "REVIEW"
    assert "Mandatory engagement rate missing" in result["filter_reason"]


def test_qualified_classification():
    """Verify creator with high score and all hard gates passes as QUALIFIED."""
    qualified_creator = {
        "name": "Sarah Chen",
        "username": "sarah_test",
        "platform": "Instagram",
        "followers": 28000,
        "contact_email": "sarah@aidev.io",
        "engagement_rate": 4.8,
        "bio": "AI Engineer & Founder | Cursor AI tips & LLM tools",
        "sub_niche": "Artificial Intelligence",
        "content_themes": ["AI coding tools", "Cursor AI"],
        "recent_content": ["Top 5 AI Coding Assistants"],
        "content_style": "Educational Code Breakdowns"
    }
    result = classify_creator(qualified_creator)
    assert result["classification"] == "QUALIFIED"
    assert result["total_score"] >= 75.0
