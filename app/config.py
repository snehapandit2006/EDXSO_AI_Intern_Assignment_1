import os
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config() -> dict:
    """Load configuration from config.yaml with fallback defaults."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    return config


_cfg = load_config()

# Campaign Configuration
CAMPAIGN_TITLE = _cfg.get("campaign", {}).get("title", "AI Developer Productivity Tool Campaign")
TARGET_NICHE = _cfg.get("campaign", {}).get("niche", "Technology")
SUB_NICHES = _cfg.get("campaign", {}).get("sub_niches", [
    "Artificial Intelligence", "Generative AI", "Developer Tools",
    "Programming", "Software Engineering", "SaaS", "Tech Education"
])
TARGET_PLATFORM = _cfg.get("campaign", {}).get("platform", "Instagram")
MIN_FOLLOWERS = _cfg.get("campaign", {}).get("min_followers", 5000)
MAX_FOLLOWERS = _cfg.get("campaign", {}).get("max_followers", 100000)
COLLABORATION_TYPE = _cfg.get("campaign", {}).get("collaboration_type", "UGC + Sponsored Content")

# Discovery Thresholds
DISCOVERY_TARGET = _cfg.get("discovery", {}).get("discovery_target", 100)
MIN_ACCEPTANCE_GATE = _cfg.get("discovery", {}).get("min_acceptance_gate", 50)

# Filtering & Scoring Thresholds
QUALIFIED_THRESHOLD = _cfg.get("filtering", {}).get("qualified_threshold", 75)
REVIEW_THRESHOLD = _cfg.get("filtering", {}).get("review_threshold", 50)
SCORING_WEIGHTS = _cfg.get("filtering", {}).get("scoring_weights", {
    "tech_relevance": 0.30,
    "content_relevance": 0.25,
    "engagement": 0.20,
    "brand_fit": 0.15,
    "audience_fit": 0.10
})

# Personalization Settings
EMAIL_MIN_WORDS = _cfg.get("personalization", {}).get("email_word_count_min", 60)
EMAIL_MAX_WORDS = _cfg.get("personalization", {}).get("email_word_count_max", 90)
DM_MIN_WORDS = _cfg.get("personalization", {}).get("dm_word_count_min", 15)
DM_MAX_WORDS = _cfg.get("personalization", {}).get("dm_word_count_max", 30)
MAX_RETRIES = _cfg.get("personalization", {}).get("max_retries", 3)
MODEL_NAME = _cfg.get("personalization", {}).get("model_name", "gemini-2.5-flash")

# Environment Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SEND_MODE = os.getenv("SEND_MODE", _cfg.get("outreach", {}).get("send_mode", "simulation"))

# Database & Paths
DB_PATH = BASE_DIR / _cfg.get("storage", {}).get("db_path", "data/app.db")
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXPORTS_DATA_DIR = DATA_DIR / "exports"

# Create directories if they do not exist
for folder in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPORTS_DATA_DIR, DB_PATH.parent]:
    folder.mkdir(parents=True, exist_ok=True)
