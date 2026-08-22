import httpx
from app.discovery import run_discovery, deduplicate_creators


def test_discovery_min_acceptance_gate(monkeypatch):
    """Verify discovery engine returns at least 50 valid unique records with mocked HTTP response."""
    def mock_get(url, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "search/users" in url:
                    return {
                        "items": [
                            {"login": f"devuser_{i}", "html_url": f"https://github.com/devuser_{i}"}
                            for i in range(35)
                        ]
                    }
                elif "users/" in url:
                    uname = url.split("/")[-1]
                    return {
                        "name": f"Developer {uname}",
                        "followers": 12500,
                        "email": f"{uname}@devpublic.org",
                        "blog": f"https://{uname}.dev",
                        "location": "San Francisco, CA",
                        "bio": "Open Source Tech Advocate",
                        "public_repos": 42
                    }
                elif "articles" in url:
                    return [
                        {
                            "title": f"Article {i} on Tech",
                            "user": {"username": f"devto_writer_{i}", "name": f"DevTo User {i}", "website_url": f"https://devto_writer_{i}.dev"}
                        }
                        for i in range(25)
                    ]
                return {}
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)

    # save_raw=False prevents polluting data/raw/ with mock data
    records = run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
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


def test_provenance_metadata(monkeypatch):
    """Verify discovery records contain mandatory provenance metadata."""
    def mock_get(url, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                if "search/users" in url:
                    return {"items": [{"login": f"devuser_{i}", "html_url": f"https://github.com/devuser_{i}"} for i in range(50)]}
                elif "users/" in url:
                    uname = url.split("/")[-1]
                    return {
                        "name": f"Developer {uname}",
                        "followers": 8000,
                        "email": f"{uname}@devpublic.org",
                        "public_repos": 10
                    }
                return []
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)

    # save_raw=False prevents polluting data/raw/ with mock data
    records = run_discovery(target_count=50, min_acceptance_gate=50, save_raw=False)
    first = records[0]
    assert "source" in first and first["source"]
    assert "source_url" in first and first["source_url"]
    assert "extraction_method" in first and first["extraction_method"]
    assert "discovered_at" in first and first["discovered_at"]
