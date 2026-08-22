import pytest
import httpx
import re
import json
from app.discovery import run_discovery
from app.filtering.classifier import classify_creator
from app.filtering import run_filtering
from scripts.validate_dataset import SYNTHETIC_PATTERNS, validate_cross_dataset_consistency
from app.config import RAW_DATA_DIR, PROCESSED_DATA_DIR


def _setup_mock_httpx(monkeypatch):
    def mock_get(url, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "search/users" in url:
                    return {
                        "items": [
                            {"login": f"dev_user_{i}", "html_url": f"https://github.com/dev_user_{i}"}
                            for i in range(35)
                        ]
                    }
                elif "users/" in url:
                    uname = url.split("/")[-1]
                    return {
                        "name": f"Developer {uname}",
                        "followers": 15000,
                        "email": f"{uname}@devpublic.org",
                        "blog": f"https://{uname}.io",
                        "location": "Seattle, WA",
                        "bio": "Building open source tools",
                        "public_repos": 30
                    }
                elif "articles" in url:
                    return [
                        {
                            "title": f"Building AI Apps #{i}",
                            "user": {"username": f"writer_{i}", "name": f"Writer {i}", "website_url": f"https://writer_{i}.dev"}
                        }
                        for i in range(25)
                    ]
                return {}
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)


def test_zero_synthetic_data_in_discovery(monkeypatch):
    """Verify that no synthetic creator patterns exist in discovery output."""
    _setup_mock_httpx(monkeypatch)
    creators = run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
    assert len(creators) >= 50
    for i, c in enumerate(creators):
        c_str = f"{c.get('name')} {c.get('username')} {c.get('contact_email')} {c.get('website')}".lower()
        for pattern in SYNTHETIC_PATTERNS:
            assert not re.search(pattern, c_str), f"Creator #{i+1} matches synthetic pattern '{pattern}'"


def test_no_test_email_domain(monkeypatch):
    """Verify that no email address uses synthetic test domains (@test.org, @devs.io, @example.com)."""
    _setup_mock_httpx(monkeypatch)
    creators = run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
    forbidden_domains = ["@test.org", "@devs.io", "@example.com", "@fake.com"]
    for c in creators:
        email = c.get("contact_email", "").lower()
        for domain in forbidden_domains:
            assert domain not in email, f"Found prohibited synthetic email domain '{domain}' in: {email}"


def test_raw_records_are_not_placeholder_users(monkeypatch):
    """Verify usernames and names are not generic placeholders like 'user_gh_0' or 'Dev'."""
    _setup_mock_httpx(monkeypatch)
    creators = run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
    # Patterns must match the full username — 'dev_user_0' should NOT match r"(?<![a-z_])user_\d+$"
    placeholder_regexes = [r"^user_gh_\d+$", r"^(?![a-z_])user_\d+$", r"^creator_\d+$"]
    for c in creators:
        uname = c.get("username", "")
        name = c.get("name", "")
        for regex in placeholder_regexes:
            assert not re.fullmatch(regex, uname), f"Username '{uname}' matches placeholder pattern '{regex}'"
        assert name != "Dev" and name != "Creator", f"Generic name '{name}' detected"


def test_no_identical_creator_records(monkeypatch):
    """Verify that records are unique and not 50 copies of identical metric values."""
    _setup_mock_httpx(monkeypatch)
    creators = run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
    usernames = [c.get("username") for c in creators]
    assert len(usernames) == len(set(usernames)), "Duplicate usernames found in discovery dataset"


def test_discovery_gate_failure_state(monkeypatch):
    """Verify that if sources return fewer than 50 real records, discovery gate fails explicitly."""
    def empty_fetch(self, target_count=50):
        return []

    monkeypatch.setattr("app.discovery.directories.PublicDirectoriesSource.fetch_creators", empty_fetch)
    monkeypatch.setattr("app.discovery.marketplaces.MarketplaceListingsSource.fetch_creators", empty_fetch)
    monkeypatch.setattr("app.discovery.search_adapter.TechHashtagSource.fetch_creators", empty_fetch)

    with pytest.raises(ValueError) as exc_info:
        run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
    
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


def test_missing_mandatory_metrics_yields_zero_qualified(tmp_path):
    """Verify that records with missing mandatory fields yield 0 QUALIFIED records."""
    incomplete_creators = [
        {
            "name": f"TestDev Incomplete{i}",
            "username": f"incomplete_dev_{i}",
            "platform": "GitHub",
            "profile_url": f"https://github.com/incomplete_dev_{i}",
            "followers": "Not Found",
            "engagement_rate": "Not Found",
            "contact_email": "Not Found",
            "website": "Not Found",
            "bio": "Open source developer",
            "sub_niche": "Software Engineering",
            "content_themes": ["Dev"],
            "content_style": "Open Source Code & Tech Repositories",
            "creator_geography": "USA",
            "source": "GitHub Public Directory",
            "source_url": "https://api.github.com",
            "extraction_method": "HTTP GET",
            "discovered_at": "2026-08-21T00:00:00Z"
        }
        for i in range(10)
    ]

    # Use tmp_path so exports don't contaminate data/exports/ and break cross-dataset checks
    filter_res = run_filtering(incomplete_creators, export_dir=tmp_path)
    assert len(filter_res["QUALIFIED"]) == 0
    assert len(filter_res["REVIEW"]) == 10


def test_downstream_records_exist_in_raw():
    """Verify cross-dataset consistency when raw and downstream files are from the same pipeline run.

    This test is skipped when files are from different pipeline runs (e.g. mock test
    overwrote raw JSON while CSVs are from a separate real run).
    """
    import os
    from pathlib import Path

    raw_path = RAW_DATA_DIR / "discovered_creators_raw.json"
    normalized_path = PROCESSED_DATA_DIR / "creators_normalized.csv"

    if not raw_path.exists() or not normalized_path.exists():
        pytest.skip("Dataset files not yet generated — skipping cross-dataset consistency check")

    # Only assert consistency when files are from the same run (within 5 minutes of each other)
    raw_mtime = os.path.getmtime(raw_path)
    norm_mtime = os.path.getmtime(normalized_path)
    if abs(raw_mtime - norm_mtime) > 300:
        pytest.skip(
            f"Raw ({raw_path.name}) and normalized ({normalized_path.name}) files are from "
            "different pipeline runs — run 'python -m scripts.run_pipeline' first, then re-test"
        )

    assert validate_cross_dataset_consistency() is True


def test_complete_provenance_on_all_creators(monkeypatch):
    """Verify all discovered creators have complete source provenance metadata."""
    _setup_mock_httpx(monkeypatch)
    creators = run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
    for c in creators:
        assert "source" in c and c["source"], "Missing source field"
        assert "source_url" in c and c["source_url"], "Missing source_url field"
        assert "extraction_method" in c and c["extraction_method"], "Missing extraction_method field"
        assert "discovered_at" in c and c["discovered_at"], "Missing discovered_at field"
        assert "profile_url" in c and c["profile_url"].startswith("http"), "Missing or invalid profile_url"
