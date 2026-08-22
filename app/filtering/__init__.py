from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from app.config import EXPORTS_DATA_DIR
from app.filtering.classifier import classify_creator


def run_filtering(enriched_creators: List[Dict[str, Any]], export_dir: Path = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run deterministic filtering engine over all enriched creator records.
    Returns dictionary with lists for 'QUALIFIED', 'REVIEW', and 'REJECTED'.
    Exports CSV datasets for each category to data/exports/ (or export_dir if provided).
    """
    out_dir = export_dir if export_dir is not None else EXPORTS_DATA_DIR
    print(f"[Filtering Engine] Running qualification & explainability engine over {len(enriched_creators)} creators...")

    results = {
        "QUALIFIED": [],
        "REVIEW": [],
        "REJECTED": []
    }

    for creator in enriched_creators:
        filter_res = classify_creator(creator)
        creator_with_filter = {**creator, **filter_res}

        classification = filter_res["classification"]
        results[classification].append(creator_with_filter)

    # Export CSVs for each classification (ALWAYS overwrite every status CSV)
    for status in ["QUALIFIED", "REVIEW", "REJECTED"]:
        items = results[status]
        csv_path = out_dir / f"{status.lower()}_creators.csv"
        if items:
            df = pd.DataFrame(items)
        else:
            df = pd.DataFrame(columns=[
                "name", "platform", "username", "profile_url", "followers",
                "engagement_rate", "contact_email", "source", "source_url",
                "extraction_method", "discovered_at", "total_score",
                "classification", "filter_reason", "failed_criteria"
            ])
        df.to_csv(csv_path, index=False)
        print(f" -> Exported {len(items)} {status} creator records to: {csv_path}")

    print(f"[Filtering Engine] Filtering complete: {len(results['QUALIFIED'])} QUALIFIED, {len(results['REVIEW'])} REVIEW, {len(results['REJECTED'])} REJECTED.")
    return results
