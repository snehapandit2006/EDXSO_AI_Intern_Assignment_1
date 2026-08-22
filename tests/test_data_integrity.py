import pytest
from app.discovery import run_discovery
from app.filtering.classifier import classify_creator
from scripts.validate_dataset import SYNTHETIC_PATTERNS
import re


def test_zero_synthetic_data_in_discovery():
    """Verify that no synthetic creator patterns exist in discovery output."""
    creators = run_discovery()
    assert len(creators) >= 50
    for i, c in enumerate(creators):
        c_str = f"{c.get('name')} {c.get('username')} {c.get('contact_email')} {c.get('website')}".lower()
        for pattern in SYNTHETIC_PATTERNS:
            assert not re.search(pattern, c_str), f"Creator #{i+1} matches synthetic pattern '{pattern}'"


def test_discovery_gate_failure_state(monkeypatch):
    """Verify that if sources return fewer than 50 real records, discovery gate fails explicitly."""
    def empty_fetch(self, target_count=50):
        return []

    monkeypatch.setattr("app.discovery.directories.PublicDirectoriesSource.fetch_creators", empty_fetch)
    monkeypatch.setattr("app.discovery.marketplaces.MarketplaceListingsSource.fetch_creators", empty_fetch)
    monkeypatch.setattr("app.discovery.search_adapter.TechHashtagSource.fetch_creators", empty_fetch)

    with pytest.raises(ValueError) as exc_info:
        run_discovery(target_count=50, min_acceptance_gate=50)
    
    assert "DISCOVERY GATE FAILURE" in str(exc_info.value)


def test_missing_data_uses_not_found():
    """Verify that missing fields use 'Not Found' explicitly rather than fake placeholders."""
    creator_with_missing = {
        "name": "Liam O'Connor",
        "username": "liam_dev_ops",
        "platform": "Instagram",
        "profile_url": "https://instagram.com/liam_dev_ops",
        "followers": 7800,
        "engagement_rate": "Not Found",
        "engagement_method": "Not Found",
        "contact_email": "liam@cloudops.net",
        "website": "Not Found",
        "source": "Public Directory",
        "source_url": "https://github.com",
        "extraction_method": "Curated Directory",
        "discovered_at": "2026-08-21T00:00:00Z"
    }

    result = classify_creator(creator_with_missing)
    # Missing engagement rate must route to REVIEW
    assert result["classification"] == "REVIEW"
    assert "Mandatory engagement rate missing" in result["filter_reason"]


def test_complete_provenance_on_all_creators():
    """Verify all discovered creators have complete source provenance metadata."""
    creators = run_discovery()
    for c in creators:
        assert "source" in c and c["source"], "Missing source field"
        assert "source_url" in c and c["source_url"], "Missing source_url field"
        assert "extraction_method" in c and c["extraction_method"], "Missing extraction_method field"
        assert "discovered_at" in c and c["discovered_at"], "Missing discovered_at field"
        assert "profile_url" in c and c["profile_url"].startswith("http"), "Missing or invalid profile_url"
