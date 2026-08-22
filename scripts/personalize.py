"""CLI Script: Run AI Personalization Stage for Qualified Creators."""
import json
from app.config import RAW_DATA_DIR, CAMPAIGN_TITLE
from app.discovery import run_discovery
from app.enrichment import run_enrichment
from app.filtering import run_filtering
from app.personalization import run_personalization

if __name__ == "__main__":
    raw_path = RAW_DATA_DIR / "discovered_creators_raw.json"
    if raw_path.exists():
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_creators = json.load(f)
    else:
        raw_creators = run_discovery()

    enriched = run_enrichment(raw_creators)
    filter_res = run_filtering(enriched)
    qualified = filter_res["QUALIFIED"]

    personalized = run_personalization(qualified, campaign_title=CAMPAIGN_TITLE)
    print(f"\n[CLI Personalization] Generated personalized pitches for {len(personalized)} qualified creators.")
