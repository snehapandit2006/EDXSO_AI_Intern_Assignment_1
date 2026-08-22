"""CLI Script: Run Creator Filtering & Explainability Stage."""
import json
from app.config import RAW_DATA_DIR
from app.discovery import run_discovery
from app.enrichment import run_enrichment
from app.filtering import run_filtering

if __name__ == "__main__":
    raw_path = RAW_DATA_DIR / "discovered_creators_raw.json"
    if raw_path.exists():
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_creators = json.load(f)
    else:
        raw_creators = run_discovery()

    enriched = run_enrichment(raw_creators)
    results = run_filtering(enriched)

    print(f"\n[CLI Filtering Summary]")
    print(f" - QUALIFIED: {len(results['QUALIFIED'])}")
    print(f" - REVIEW:    {len(results['REVIEW'])}")
    print(f" - REJECTED:  {len(results['REJECTED'])}")
