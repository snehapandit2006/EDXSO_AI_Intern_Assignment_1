from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from app.config import DB_PATH

Base = declarative_base()


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    target_niche = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False)
    min_followers = Column(Integer, default=5000)
    max_followers = Column(Integer, default=100000)
    collaboration_type = Column(String(100), default="UGC + Sponsored Content")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    creators = relationship("Creator", back_populates="campaign", cascade="all, delete-orphan")
    filter_results = relationship("FilterResult", back_populates="campaign", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="campaign", cascade="all, delete-orphan")
    outreach_logs = relationship("OutreachLog", back_populates="campaign", cascade="all, delete-orphan")


class Creator(Base):
    __tablename__ = "creators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False, default="GitHub")
    username = Column(String(100), nullable=False)
    profile_url = Column(String(500), nullable=False)
    followers = Column(Integer, nullable=True)
    followers_source = Column(String(100), default="Not Found")
    engagement_rate = Column(Float, nullable=True)
    engagement_source = Column(String(100), default="Not Found")
    engagement_method = Column(String(255), default="Sample post analysis")
    engagement_sample_size = Column(Integer, default=10)
    article_reactions = Column(String(50), default="Not Found")
    article_comments = Column(String(50), default="Not Found")
    article_engagement_source = Column(String(100), default="Not Found")
    category = Column(String(100), default="Technology")
    sub_niche = Column(String(100), default="Software Engineering")
    content_themes = Column(Text, default="[]")  # JSON List
    content_style = Column(String(100), default="Technical & Software")
    content_source = Column(String(100), default="Not Found")
    bio = Column(Text, default="")
    recent_content = Column(Text, default="[]")  # JSON List
    contact_email = Column(String(255), default="Not Found")
    email_source = Column(String(100), default="Not Found")
    website = Column(String(500), default="Not Found")
    creator_geography = Column(String(100), default="Not Found")
    audience_age = Column(String(100), default="Not Found")
    audience_gender = Column(String(100), default="Not Found")
    audience_geography = Column(String(100), default="Not Found")
    demographics_source = Column(String(100), default="Not Found")
    source = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=False)
    extraction_method = Column(String(100), default="HTTP GET REST API")
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    campaign = relationship("Campaign", back_populates="creators")
    filter_result = relationship("FilterResult", back_populates="creator", uselist=False, cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="creator", cascade="all, delete-orphan")
    outreach_log = relationship("OutreachLog", back_populates="creator", uselist=False, cascade="all, delete-orphan")

    def get_content_themes(self) -> list:
        try:
            return json.loads(self.content_themes) if self.content_themes else []
        except Exception:
            return []

    def set_content_themes(self, themes: list):
        self.content_themes = json.dumps(themes)

    def get_recent_content(self) -> list:
        try:
            return json.loads(self.recent_content) if self.recent_content else []
        except Exception:
            return []

    def set_recent_content(self, items: list):
        self.recent_content = json.dumps(items)


class FilterResult(Base):
    __tablename__ = "filter_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False, unique=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    niche_score = Column(Float, default=0.0)
    content_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    brand_fit_score = Column(Float, default=0.0)
    brand_fit_reason = Column(Text, default="")
    geography_score = Column(Float, nullable=True)
    audience_fit_score = Column(Float, nullable=True)
    total_score = Column(Float, default=0.0)
    classification = Column(String(20), nullable=False)  # QUALIFIED, REVIEW, REJECTED
    filter_reason = Column(Text, nullable=False)
    failed_criteria = Column(Text, default="[]")  # JSON List

    creator = relationship("Creator", back_populates="filter_result")
    campaign = relationship("Campaign", back_populates="filter_results")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    email_subject = Column(String(255), default="")
    email_body = Column(Text, default="")
    email_word_count = Column(Integer, default=0)
    dm_body = Column(Text, default="")
    dm_word_count = Column(Integer, default=0)
    personalization_signals = Column(Text, default="{}")  # JSON Dict
    generation_model = Column(String(50), default="gemini-2.5-flash")
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    validation_status = Column(String(20), default="PASSED")  # PASSED, FAILED
    approval_status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED

    creator = relationship("Creator", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")


class OutreachLog(Base):
    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(Integer, ForeignKey("creators.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    email = Column(String(255), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    status = Column(String(20), default="DRAFT")  # DRAFT, READY, SENT, FAILED, SKIPPED, DUPLICATE
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("campaign_id", "creator_id", name="uq_campaign_creator_outreach"),
    )

    creator = relationship("Creator", back_populates="outreach_log")
    campaign = relationship("Campaign", back_populates="outreach_logs")


# Database engine and session setup
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def reset_db():
    """Drop all existing tables and recreate them to purge stale synthetic records."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
