from app.discovery import run_discovery, deduplicate_creators


def test_discovery_min_acceptance_gate():
    """Verify discovery engine returns at least 50 valid unique records."""
    records = run_discovery()
    assert len(records) >= 50, f"Expected at least 50 creators, got {len(records)}"


def test_deduplication():
    """Verify deduplication removes duplicate (platform, username) records."""
    sample = [
        {"platform": "Instagram", "username": "sarah.ai.dev", "name": "Sarah 1"},
        {"platform": "Instagram", "username": "sarah.ai.dev", "name": "Sarah 2"},
        {"platform": "Instagram", "username": "alexcode_ai", "name": "Alex"}
    ]
    unique = deduplicate_creators(sample)
    assert len(unique) == 2


def test_provenance_metadata():
    """Verify discovery records contain mandatory provenance metadata."""
    records = run_discovery()
    first = records[0]
    assert "source" in first and first["source"]
    assert "source_url" in first and first["source_url"]
    assert "extraction_method" in first and first["extraction_method"]
    assert "discovered_at" in first and first["discovered_at"]
