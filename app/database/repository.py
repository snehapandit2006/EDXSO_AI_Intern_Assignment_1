import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.models import Campaign, Creator, FilterResult, Message, OutreachLog, SessionLocal, init_db
from app.config import (
    CAMPAIGN_TITLE, TARGET_NICHE, TARGET_PLATFORM, MIN_FOLLOWERS, MAX_FOLLOWERS, COLLABORATION_TYPE
)


def get_db():
    """Context manager / generator for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_campaign(
    db: Session,
    title: str = CAMPAIGN_TITLE,
    niche: str = TARGET_NICHE,
    platform: str = TARGET_PLATFORM,
    min_followers: int = MIN_FOLLOWERS,
    max_followers: int = MAX_FOLLOWERS,
    collaboration_type: str = COLLABORATION_TYPE
) -> Campaign:
    """Retrieve or create active campaign."""
    campaign = db.query(Campaign).filter_by(title=title, platform=platform).first()
    if not campaign:
        campaign = Campaign(
            title=title,
            target_niche=niche,
            platform=platform,
            min_followers=min_followers,
            max_followers=max_followers,
            collaboration_type=collaboration_type
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
    return campaign


def _safe_engagement_rate(value) -> float | None:
    """Coerce engagement_rate to float or None — prevents 'Not Found' string in Float DB column."""
    if value is None or value == "Not Found" or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def upsert_creator(db: Session, campaign_id: int, creator_data: dict) -> Creator:
    """Save or update creator record."""
    username = creator_data.get("username", "").lower().strip()
    platform = creator_data.get("platform", "Instagram")

    existing = db.query(Creator).filter_by(campaign_id=campaign_id, username=username, platform=platform).first()

    content_themes = creator_data.get("content_themes", [])
    if isinstance(content_themes, list):
        content_themes_str = json.dumps(content_themes)
    else:
        content_themes_str = str(content_themes)

    recent_content = creator_data.get("recent_content", [])
    if isinstance(recent_content, list):
        recent_content_str = json.dumps(recent_content)
    else:
        recent_content_str = str(recent_content)

    if existing:
        existing.name = creator_data.get("name", existing.name)
        existing.profile_url = creator_data.get("profile_url", existing.profile_url)
        existing.followers = creator_data.get("followers", existing.followers)
        existing.engagement_rate = _safe_engagement_rate(creator_data.get("engagement_rate", existing.engagement_rate))
        existing.engagement_method = creator_data.get("engagement_method", existing.engagement_method)
        existing.category = creator_data.get("category", existing.category)
        existing.sub_niche = creator_data.get("sub_niche", existing.sub_niche)
        existing.content_themes = content_themes_str
        existing.content_style = creator_data.get("content_style", existing.content_style)
        existing.bio = creator_data.get("bio", existing.bio)
        existing.recent_content = recent_content_str
        existing.contact_email = creator_data.get("contact_email", existing.contact_email)
        existing.email_source = creator_data.get("email_source", existing.email_source)
        existing.website = creator_data.get("website", existing.website)
        existing.creator_geography = creator_data.get("creator_geography", existing.creator_geography)
        existing.audience_age = creator_data.get("audience_age", existing.audience_age)
        existing.audience_gender = creator_data.get("audience_gender", existing.audience_gender)
        existing.audience_geography = creator_data.get("audience_geography", existing.audience_geography)
        existing.source = creator_data.get("source", existing.source)
        existing.source_url = creator_data.get("source_url", existing.source_url)
        existing.extraction_method = creator_data.get("extraction_method", existing.extraction_method)
        existing.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        creator = Creator(
            campaign_id=campaign_id,
            name=creator_data.get("name", "Unknown Creator"),
            platform=platform,
            username=username,
            profile_url=creator_data.get("profile_url", f"https://instagram.com/{username}"),
            followers=creator_data.get("followers", 0),
            engagement_rate=_safe_engagement_rate(creator_data.get("engagement_rate")),
            engagement_method=creator_data.get("engagement_method", "Sample post analysis"),
            engagement_sample_size=creator_data.get("engagement_sample_size", 10),
            category=creator_data.get("category", "Technology"),
            sub_niche=creator_data.get("sub_niche", "AI / Developer Tools"),
            content_themes=content_themes_str,
            content_style=creator_data.get("content_style", "Educational & Technical"),
            bio=creator_data.get("bio", ""),
            recent_content=recent_content_str,
            contact_email=creator_data.get("contact_email", "Not Found"),
            email_source=creator_data.get("email_source", "Public Profile Bio"),
            website=creator_data.get("website", "Not Found"),
            creator_geography=creator_data.get("creator_geography", "Not Found"),
            audience_age=creator_data.get("audience_age", "Not Found"),
            audience_gender=creator_data.get("audience_gender", "Not Found"),
            audience_geography=creator_data.get("audience_geography", "Not Found"),
            source=creator_data.get("source", "Public Tech Directory"),
            source_url=creator_data.get("source_url", "https://example.com"),
            extraction_method=creator_data.get("extraction_method", "Directory Adapter"),
            discovered_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(creator)
        db.commit()
        db.refresh(creator)
        return creator


def save_filter_result(db: Session, campaign_id: int, creator_id: int, filter_data: dict) -> FilterResult:
    """Save or update filtering and classification results."""
    existing = db.query(FilterResult).filter_by(campaign_id=campaign_id, creator_id=creator_id).first()

    failed_criteria = filter_data.get("failed_criteria", [])
    failed_criteria_str = json.dumps(failed_criteria) if isinstance(failed_criteria, list) else str(failed_criteria)

    if existing:
        existing.niche_score = filter_data.get("niche_score", 0.0)
        existing.content_score = filter_data.get("content_score", 0.0)
        existing.engagement_score = filter_data.get("engagement_score", 0.0)
        existing.brand_fit_score = filter_data.get("brand_fit_score", 0.0)
        existing.brand_fit_reason = filter_data.get("brand_fit_reason", "")
        existing.geography_score = filter_data.get("geography_score")
        existing.audience_fit_score = filter_data.get("audience_fit_score")
        existing.total_score = filter_data.get("total_score", 0.0)
        existing.classification = filter_data.get("classification", "REJECTED")
        existing.filter_reason = filter_data.get("filter_reason", "")
        existing.failed_criteria = failed_criteria_str
        db.commit()
        db.refresh(existing)
        return existing
    else:
        res = FilterResult(
            creator_id=creator_id,
            campaign_id=campaign_id,
            niche_score=filter_data.get("niche_score", 0.0),
            content_score=filter_data.get("content_score", 0.0),
            engagement_score=filter_data.get("engagement_score", 0.0),
            brand_fit_score=filter_data.get("brand_fit_score", 0.0),
            brand_fit_reason=filter_data.get("brand_fit_reason", ""),
            geography_score=filter_data.get("geography_score"),
            audience_fit_score=filter_data.get("audience_fit_score"),
            total_score=filter_data.get("total_score", 0.0),
            classification=filter_data.get("classification", "REJECTED"),
            filter_reason=filter_data.get("filter_reason", ""),
            failed_criteria=failed_criteria_str
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res


def save_message(db: Session, campaign_id: int, creator_id: int, message_data: dict) -> Message:
    """Save generated personalized pitch and DM."""
    signals = message_data.get("personalization_signals", {})
    signals_str = json.dumps(signals) if isinstance(signals, dict) else str(signals)

    msg = db.query(Message).filter_by(campaign_id=campaign_id, creator_id=creator_id).first()
    if not msg:
        msg = Message(campaign_id=campaign_id, creator_id=creator_id)
        db.add(msg)

    msg.email_subject = message_data.get("email_subject", "")
    msg.email_body = message_data.get("email_body", "")
    msg.email_word_count = message_data.get("email_word_count", 0)
    msg.dm_body = message_data.get("dm_body", "")
    msg.dm_word_count = message_data.get("dm_word_count", 0)
    msg.personalization_signals = signals_str
    msg.generation_model = message_data.get("generation_model", "gemini-2.5-flash")
    msg.generated_at = datetime.now(timezone.utc)
    msg.validation_status = message_data.get("validation_status", "PASSED")
    msg.approval_status = message_data.get("approval_status", "APPROVED")

    db.commit()
    db.refresh(msg)
    return msg


def save_outreach_log(db: Session, campaign_id: int, creator_id: int, outreach_data: dict) -> OutreachLog:
    """Save or update outreach status with duplicate prevention check."""
    existing = db.query(OutreachLog).filter_by(campaign_id=campaign_id, creator_id=creator_id).first()
    if existing:
        existing.email = outreach_data.get("email", existing.email)
        existing.message_id = outreach_data.get("message_id", existing.message_id)
        existing.status = outreach_data.get("status", existing.status)
        existing.sent = outreach_data.get("sent", existing.sent)
        if outreach_data.get("sent_at"):
            existing.sent_at = outreach_data.get("sent_at")
        existing.error = outreach_data.get("error", existing.error)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        outreach = OutreachLog(
            campaign_id=campaign_id,
            creator_id=creator_id,
            email=outreach_data.get("email", "Not Found"),
            message_id=outreach_data.get("message_id"),
            status=outreach_data.get("status", "DRAFT"),
            sent=outreach_data.get("sent", False),
            sent_at=outreach_data.get("sent_at"),
            error=outreach_data.get("error")
        )
        db.add(outreach)
        db.commit()
        db.refresh(outreach)
        return outreach


def get_all_creators(db: Session, campaign_id: int) -> list:
    return db.query(Creator).filter_by(campaign_id=campaign_id).all()
