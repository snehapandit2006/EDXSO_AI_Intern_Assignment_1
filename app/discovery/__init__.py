import json
from typing import List, Dict, Any
from app.config import DISCOVERY_TARGET, MIN_ACCEPTANCE_GATE, RAW_DATA_DIR
from app.discovery.directories import PublicDirectoriesSource
from app.discovery.marketplaces import MarketplaceListingsSource
from app.discovery.search_adapter import TechHashtagSource
from app.discovery.open_creator_index import OpenCreatorIndexSource


def deduplicate_creators(creators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate creator records by (platform, username)."""
    seen = set()
    unique_records = []
    for record in creators:
        key = (record.get("platform", "Instagram").lower(), record.get("username", "").lower().strip())
        if key[1] and key not in seen:
            seen.add(key)
            unique_records.append(record)
    return unique_records


def run_discovery(target_count: int = DISCOVERY_TARGET, min_acceptance_gate: int = MIN_ACCEPTANCE_GATE, save_raw: bool = True) -> List[Dict[str, Any]]:
    """
    Execute multi-source live discovery pipeline across real public API adapters.
    Strictly queries real public sources and enforces >= min_acceptance_gate real unique records.
    Fails explicitly if fewer than min_acceptance_gate real records exist.
    If save_raw=False, skips saving the raw JSON (useful in mock-based unit tests).
    """
    print(f"[Discovery Engine] Starting multi-source discovery pipeline (Target: {target_count}, Min Acceptance Gate: {min_acceptance_gate})...")

    discovered = []

    # Source A (Primary: Public Directories)
    source_a = PublicDirectoriesSource()
    a_records = source_a.fetch_creators(target_count=target_count)
    discovered.extend(a_records)
    print(f" -> Source A ('{source_a.source_name}') fetched {len(a_records)} real records.")

    unique_discovered = deduplicate_creators(discovered)

    # Source B (Secondary: UGC Marketplaces Spotlight)
    if len(unique_discovered) < target_count or len(unique_discovered) < min_acceptance_gate:
        print(f" -> Unique records ({len(unique_discovered)}) below target ({target_count}). Triggering Source B...")
        source_b = MarketplaceListingsSource()
        b_records = source_b.fetch_creators(target_count=30)
        discovered.extend(b_records)
        unique_discovered = deduplicate_creators(discovered)
        print(f" -> Source B ('{source_b.source_name}') fetched {len(b_records)} real records. Total unique: {len(unique_discovered)}")

    # Source C (Tertiary: Public Tech Creator Index & Hashtag Feed)
    print(f" -> Triggering Source C ('Public Tech Creator Index & Hashtags')...")
    source_c = TechHashtagSource()
    c_records = source_c.fetch_creators(target_count=20)
    discovered.extend(c_records)
    unique_discovered = deduplicate_creators(discovered)
    print(f" -> Source C ('{source_c.source_name}') fetched {len(c_records)} real records. Total unique: {len(unique_discovered)}")

    # Source D (Quaternary: Open Technology Creator & Community Index)
    print(f" -> Triggering Source D ('Open Technology Creator & Community Index')...")
    source_d = OpenCreatorIndexSource()
    d_records = source_d.fetch_creators(target_count=15)
    discovered.extend(d_records)
    unique_discovered = deduplicate_creators(discovered)
    print(f" -> Source D ('{source_d.source_name}') fetched {len(d_records)} real records. Total unique: {len(unique_discovered)}")

    # Hard Acceptance Gate Check
    if len(unique_discovered) < min_acceptance_gate:
        raise ValueError(
            f"DISCOVERY GATE FAILURE: Total unique real creators collected ({len(unique_discovered)}) "
            f"is below the minimum acceptance gate ({min_acceptance_gate}). System will NOT fabricate synthetic records."
        )

    # Save raw discovery dataset (skip in unit tests using save_raw=False)
    if save_raw:
        raw_path = RAW_DATA_DIR / "discovered_creators_raw.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(unique_discovered, f, indent=2)
        print(f"[Discovery Engine] Successfully collected and deduplicated {len(unique_discovered)} real, traceable creator records.")
        print(f" -> Raw dataset saved to: {raw_path}")
    else:
        print(f"[Discovery Engine] Successfully collected and deduplicated {len(unique_discovered)} real, traceable creator records (dry-run, not saved).")

    return unique_discovered
