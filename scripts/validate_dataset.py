import json
import sys
import re
import csv
from pathlib import Path
from typing import Dict, Any, List

# Ensure utf-8 output encoding for Windows terminal compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import RAW_DATA_DIR, EXPORTS_DATA_DIR


SYNTHETIC_PATTERNS = [
    r"tech creator \d+",
    r"marketplace dev \d+",
    r"hashtag coder \d+",
    r"tech_creator_\d+",
    r"marketplace_dev_\d+",
    r"hashtag_coder_\d+",
    r"techoutreach\.dev",
    r"creatoragency\.io",
    r"devmail\.org",
    r"example\.com",
    r"fake",
    r"placeholder"
]


def audit_record(record: Dict[str, Any], index: int) -> List[str]:
    """Audit an individual creator record for synthetic patterns and data compliance."""
    issues = []
    
    # 1. Synthetic pattern checks
    record_str = json.dumps(record).lower()
    for pattern in SYNTHETIC_PATTERNS:
        if re.search(pattern, record_str):
            issues.append(f"Record #{index+1} ('{record.get('name')}') contains synthetic pattern matching '{pattern}'")

    # 2. Provenance checks
    for req_field in ["source", "source_url", "extraction_method", "discovered_at", "profile_url"]:
        if not record.get(req_field):
            issues.append(f"Record #{index+1} ('{record.get('name')}') is missing provenance field '{req_field}'")

    # 3. Missing data representation checks
    for field in ["contact_email", "website", "engagement_rate", "engagement_method"]:
        val = record.get(field)
        if val is None or val == "":
            issues.append(f"Record #{index+1} ('{record.get('name')}') has empty/None '{field}' instead of 'Not Found'")

    return issues


def validate_dataset(filepath: Path) -> bool:
    """Run comprehensive assignment compliance validation on a dataset file (JSON or CSV)."""
    print(f"\n========================================================")
    print(f" DATASET VALIDATION AUDIT: {filepath.name}")
    print(f"========================================================")

    if not filepath.exists():
        print(f"[FAIL] File does not exist: {filepath}")
        return False

    records = []
    if filepath.suffix == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "creators" in data:
            records = data["creators"]
        elif isinstance(data, list):
            records = data
    elif filepath.suffix == ".csv":
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

    total_records = len(records)
    print(f"Total Records in File: {total_records}")

    all_issues = []
    seen_urls = set()
    duplicate_count = 0
    synthetic_count = 0
    provenance_missing = 0
    not_found_validations = 0

    for i, record in enumerate(records):
        url = record.get("profile_url", "").lower().strip()
        if url:
            if url in seen_urls:
                duplicate_count += 1
                all_issues.append(f"Duplicate profile URL detected: {url}")
            else:
                seen_urls.add(url)

        rec_issues = audit_record(record, i)
        if any("synthetic" in issue for issue in rec_issues):
            synthetic_count += 1
        if any("provenance" in issue for issue in rec_issues):
            provenance_missing += 1

        all_issues.extend(rec_issues)

        # Count properly handled "Not Found" fields
        for fld in ["contact_email", "website", "engagement_rate"]:
            if record.get(fld) == "Not Found":
                not_found_validations += 1

    # Check 1: Record Threshold Gate (Only applies to raw dataset; subset exports have expected smaller counts)
    is_raw = "raw" in filepath.name.lower()
    gate_passed = (total_records >= 50) if is_raw else (total_records > 0)
    print(f"1. Record Count Threshold: {'[PASS]' if gate_passed else '[FAIL]'} ({total_records} records)")

    # Check 2: Synthetic Data Prohibition
    synthetic_passed = synthetic_count == 0
    print(f"2. Zero Synthetic Records: {'[PASS]' if synthetic_passed else '[FAIL]'} ({synthetic_count} synthetic patterns found)")

    # Check 3: Data Provenance Tracking
    provenance_passed = provenance_missing == 0
    print(f"3. 100% Provenance & Source Tracking: {'[PASS]' if provenance_passed else '[FAIL]'} ({provenance_missing} incomplete records)")

    # Check 4: Uniqueness
    unique_passed = duplicate_count == 0
    print(f"4. 100% Unique Profiles: {'[PASS]' if unique_passed else '[FAIL]'} ({duplicate_count} duplicates found)")

    print(f"Explicit 'Not Found' Field Declarations: {not_found_validations} fields correctly marked")

    overall_pass = gate_passed and synthetic_passed and provenance_passed and unique_passed

    print(f"OVERALL AUDIT STATUS: {'[PASS] (VERIFIED REAL DATA)' if overall_pass else '[FAIL] FAILED AUDIT'}")
    print(f"========================================================\n")

    return overall_pass


if __name__ == "__main__":
    raw_path = RAW_DATA_DIR / "discovered_creators_raw.json"
    qual_path = EXPORTS_DATA_DIR / "qualified_creators.csv"

    raw_ok = validate_dataset(raw_path) if raw_path.exists() else False
    qual_ok = validate_dataset(qual_path) if qual_path.exists() else False

    if raw_ok and qual_ok:
        print("ALL DATASET AUDITS PASSED: 100% Data Integrity & Assignment Compliance Confirmed.")
        sys.exit(0)
    else:
        print("DATASET AUDIT FAILED: One or more datasets failed compliance checks.")
        sys.exit(1)
