from typing import List, Dict, Any
import pandas as pd
from app.config import EXPORTS_DATA_DIR
from app.filtering.classifier import classify_creator


def run_filtering(enriched_creators: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run deterministic filtering engine over all enriched creator records.
    Returns dictionary with lists for 'QUALIFIED', 'REVIEW', and 'REJECTED'.
    Exports CSV datasets for each category to data/exports/.
    """
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

    # Export CSVs for each classification
    for status, items in results.items():
        if items:
            df = pd.DataFrame(items)
            csv_path = EXPORTS_DATA_DIR / f"{status.lower()}_creators.csv"
            df.to_csv(csv_path, index=False)
            print(f" -> Exported {len(items)} {status} creator records to: {csv_path}")

    print(f"[Filtering Engine] Filtering complete: {len(results['QUALIFIED'])} QUALIFIED, {len(results['REVIEW'])} REVIEW, {len(results['REJECTED'])} REJECTED.")
    return results
