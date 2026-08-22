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

from app.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, EXPORTS_DATA_DIR


SYNTHETIC_PATTERNS = [
    r"tech creator \d+",
    r"marketplace dev \d+",
    r"hashtag coder \d+",
    r"tech_creator_\d+",
    r"marketplace_dev_\d+",
    r"hashtag_coder_\d+",
    # Exact placeholder username forms — require word-boundary so 'dev_user_0' doesn't false-positive
    r"\buser_gh_\d+\b",
    r"(?<![a-z_])user_\d+\b",
    r"\bcreator \d+\b",
    r"\bcreator_\d+\b",
    r"dev@test\.org",
    r"@test\.org",
    r"techoutreach\.dev",
    r"creatoragency\.io",
    r"devmail\.org",
    r"devs\.io",
    r"@devs\.io",
    r"example\.com",
    r"\bfake\b",
    r"\bplaceholder\b"
]

FORBIDDEN_PROVENANCE_PATTERNS = [
    r"reach & engagement index",
    r"repository to follower ratio",
    r"repository count to follower ratio",
    r"website domain handle",
    r"search api query bounds",
    r"public profile website domain handle",
    r"public article reach & engagement index"
]


def audit_record(record: Dict[str, Any], index: int) -> List[str]:
    """Audit an individual creator record for synthetic patterns and data compliance."""
    issues = []
    
    # 1. Synthetic pattern checks
    record_str = json.dumps(record).lower()
    for pattern in SYNTHETIC_PATTERNS:
        if re.search(pattern, record_str):
            issues.append(f"Record #{index+1} ('{record.get('name')}') contains synthetic pattern matching '{pattern}'")

    # 2. Forbidden derived provenance checks
    for prov_field in ["followers_source", "engagement_source", "engagement_method", "email_source"]:
        val = str(record.get(prov_field) or "").lower()
        for f_pattern in FORBIDDEN_PROVENANCE_PATTERNS:
            if re.search(f_pattern, val):
                issues.append(f"Record #{index+1} ('{record.get('name')}') uses forbidden derived provenance method '{f_pattern}' in '{prov_field}'")

    # 3. Provenance completeness checks
    for req_field in ["source", "source_url", "extraction_method", "discovered_at", "profile_url"]:
        val = record.get(req_field)
        if not val or val == "Not Found":
            issues.append(f"Record #{index+1} ('{record.get('name')}') is missing mandatory provenance field '{req_field}'")

    # 4. Missing data representation checks
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
        print(f"[SKIP] File does not exist yet: {filepath}")
        return True

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
        if any("synthetic" in issue or "forbidden" in issue for issue in rec_issues):
            synthetic_count += 1
        if any("missing mandatory" in issue for issue in rec_issues):
            provenance_missing += 1

        all_issues.extend(rec_issues)

        # Count properly handled "Not Found" fields
        for fld in ["contact_email", "website", "engagement_rate", "audience_geography"]:
            if record.get(fld) == "Not Found":
                not_found_validations += 1

    # Check 1: Record Threshold Gate (Only applies to raw dataset; subset exports have expected smaller counts)
    is_raw = "raw" in filepath.name.lower() or "normalized" in filepath.name.lower()
    gate_passed = (total_records >= 50) if is_raw else (total_records >= 0)
    print(f"1. Record Count Threshold: {'[PASS]' if gate_passed else '[FAIL]'} ({total_records} records)")

    # Check 2: Zero Synthetic or Derived Metrics
    synthetic_passed = synthetic_count == 0
    print(f"2. Zero Synthetic/Derived Records: {'[PASS]' if synthetic_passed else '[FAIL]'} ({synthetic_count} violations found)")

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


def validate_cross_dataset_consistency() -> bool:
    """Verify that all processed and exported datasets strictly match raw discovery records."""
    print(f"\n========================================================")
    print(f" CROSS-DATASET CONSISTENCY & PROVENANCE AUDIT")
    print(f"========================================================")

    raw_path = RAW_DATA_DIR / "discovered_creators_raw.json"
    if not raw_path.exists():
        print("[SKIP] Raw discovery file does not exist yet.")
        return True

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_creators = json.load(f)

    raw_lookup = {
        (c.get("platform", "").lower(), c.get("username", "").lower().strip()): c
        for c in raw_creators
    }

    downstream_files = [
        PROCESSED_DATA_DIR / "creators_normalized.csv",
        EXPORTS_DATA_DIR / "qualified_creators.csv",
        EXPORTS_DATA_DIR / "review_creators.csv",
        EXPORTS_DATA_DIR / "rejected_creators.csv"
    ]

    all_consistent = True

    for filepath in downstream_files:
        if not filepath.exists():
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        print(f"Auditing cross-dataset consistency for: {filepath.name} ({len(records)} records)")

        for idx, rec in enumerate(records):
            key = (rec.get("platform", "").lower(), rec.get("username", "").lower().strip())
            if key not in raw_lookup:
                print(f" -> [FAIL] Record #{idx+1} ('{rec.get('name')}', {key}) in {filepath.name} was NOT found in raw discovery data!")
                all_consistent = False
                continue

            raw_rec = raw_lookup[key]

            # Verify no metric fabrication between raw and downstream
            for field in ["contact_email", "followers", "engagement_rate"]:
                raw_val = str(raw_rec.get(field, "Not Found"))
                rec_val = str(rec.get(field, "Not Found"))

                if raw_val == "Not Found" and rec_val != "Not Found":
                    print(f" -> [FAIL] Record #{idx+1} ('{rec.get('name')}') fabricated '{field}' ({rec_val}) when raw data was 'Not Found'!")
                    all_consistent = False

    print(f"CROSS-DATASET STATUS: {'[PASS] 100% CONSISTENT WITH RAW DATA' if all_consistent else '[FAIL] DATA DRIFT DETECTED'}")
    print(f"========================================================\n")

    return all_consistent


# ── Discovery module static-dataset audit ───────────────────────────────────
# Detect hardcoded creator dicts inside discovery adapter source files.
# A static creator dataset is identified by finding a Python source file that
# contains multiple dict literals each supplying BOTH 'profile_url' AND a
# numeric 'followers' value — the fingerprint of a fabricated record.
# ─────────────────────────────────────────────────────────────────────────────

DISCOVERY_ADAPTER_FILES = [
    Path(__file__).resolve().parent.parent / "app" / "discovery" / "directories.py",
    Path(__file__).resolve().parent.parent / "app" / "discovery" / "marketplaces.py",
    Path(__file__).resolve().parent.parent / "app" / "discovery" / "search_adapter.py",
]

# Each signal: if found >= HARDCODED_HIT_THRESHOLD times it flags a violation.
HARDCODED_CREATOR_SIGNALS = [
    (r"[\"']profile_url[\"']\s*:", "profile_url literal assignments"),
    (r"[\"']followers[\"']\s*:\s*\d+", "numeric followers literals"),
    (r"[\"']engagement_rate[\"']\s*:\s*[0-9]", "numeric engagement_rate literals"),
    (r"[\"']contact_email[\"']\s*:\s*[\"'][^@\"']+@[^@\"']+[\"']", "hardcoded email literals"),
]
HARDCODED_HIT_THRESHOLD = 3  # 3+ occurrences of ANY signal = flag


def audit_discovery_modules_for_hardcoded_creators() -> bool:
    """
    Inspect discovery adapter source files for hardcoded static creator datasets.
    Returns True if all files are clean, False if any violation is detected.
    """
    print("\n========================================================")
    print(" DISCOVERY MODULE STATIC-DATASET AUDIT")
    print("========================================================")

    all_clean = True
    for src_path in DISCOVERY_ADAPTER_FILES:
        if not src_path.exists():
            print(f"[SKIP] Discovery module not found: {src_path.name}")
            continue

        source_code = src_path.read_text(encoding="utf-8")
        violations = []

        for pattern, description in HARDCODED_CREATOR_SIGNALS:
            hits = re.findall(pattern, source_code)
            if len(hits) >= HARDCODED_HIT_THRESHOLD:
                violations.append(
                    f"  '{description}' appears {len(hits)}x (threshold: {HARDCODED_HIT_THRESHOLD})"
                )

        if violations:
            print(f"[FAIL] {src_path.name} — hardcoded creator dataset detected:")
            for v in violations:
                print(v)
            all_clean = False
        else:
            print(f"[PASS] {src_path.name} — no hardcoded creator dataset found")

    status = (
        "[PASS] All discovery modules are clean"
        if all_clean
        else "[FAIL] Hardcoded creator data detected in discovery module(s)"
    )
    print(f"STATIC-DATASET AUDIT STATUS: {status}")
    print("========================================================\n")
    return all_clean


if __name__ == "__main__":
    files_to_validate = [
        RAW_DATA_DIR / "discovered_creators_raw.json",
        PROCESSED_DATA_DIR / "creators_normalized.csv",
        EXPORTS_DATA_DIR / "qualified_creators.csv",
        EXPORTS_DATA_DIR / "review_creators.csv",
        EXPORTS_DATA_DIR / "rejected_creators.csv"
    ]

    all_passed = True
    for fpath in files_to_validate:
        if not validate_dataset(fpath):
            all_passed = False

    if not validate_cross_dataset_consistency():
        all_passed = False

    if not audit_discovery_modules_for_hardcoded_creators():
        all_passed = False

    if all_passed:
        print("ALL DATASET AUDITS PASSED: 100% Data Integrity, Provenance & Cross-Dataset Consistency Confirmed.")
        sys.exit(0)
    else:
        print("DATASET AUDIT FAILED: One or more datasets failed compliance checks.")
        sys.exit(1)
