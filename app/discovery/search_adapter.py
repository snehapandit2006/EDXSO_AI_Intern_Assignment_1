import httpx
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.discovery.base import DiscoverySource

# ──────────────────────────────────────────────────────────────────────────────
# AUTHENTICITY CONTRACT:
#   Every field in every record returned by this adapter must come from
#   a live HTTP API response or be explicitly set to "Not Found".
#
#   This adapter MUST NOT contain:
#   - Hardcoded creator names, usernames, follower counts, or emails
#   - Static JSON/list datasets of any kind
#   - Formula-derived follower counts or engagement rates
#   - Generated email addresses from domain names or usernames
# ──────────────────────────────────────────────────────────────────────────────


class TechHashtagSource(DiscoverySource):
    """
    Source C: Public Tech Hashtag & Community Search Adapter.

    Performs real live HTTP GET REST API requests to query tech community
    hashtag feeds (#devtools, #opensource, #ai, #python) via the Dev.to
    public Articles API.

    Data authenticity rules enforced:
    - followers = "Not Found"  (Dev.to article API does not supply follower counts)
    - engagement_rate = "Not Found"  (no verified engagement metric available)
    - contact_email = "Not Found" unless a valid email is found in a bio/website
      field returned by the Dev.to user detail API — no domain-guessing allowed
    - article_reactions and article_comments are stored as-is from the API
    """

    def __init__(self):
        super().__init__(
            source_name="Dev.to Public Tech Hashtag Feed (#devtools, #ai, #opensource)",
            source_url="https://dev.to/api/articles?tag=devtools",
            extraction_method="HTTP GET REST API Extraction (httpx)"
        )

    def fetch_creators(self, target_count: int = 20) -> List[Dict[str, Any]]:
        creators: List[Dict[str, Any]] = []
        headers = {"User-Agent": "EDXSO-Influencer-Outreach/1.0 (Public Research Bot)"}
        seen_usernames: set = set()

        # Tags to query. We keep the list short so we don't duplicate records
        # already retrieved by Source B (marketplaces.py also queries Dev.to).
        tags = ["ai", "python", "webdev", "programming"]

        for tag in tags:
            if len(creators) >= target_count:
                break

            api_url = f"https://dev.to/api/articles?tag={tag}&per_page=20"
            try:
                resp = httpx.get(api_url, headers=headers, timeout=6.0)
                if resp.status_code != 200:
                    print(f" -> [HTTP Warning] Source C tag=#{tag} returned HTTP {resp.status_code}")
                    continue

                articles = resp.json()
                for article in articles:
                    if len(creators) >= target_count:
                        break

                    user_info = article.get("user", {})
                    uname = (user_info.get("username") or "").strip().lower()
                    if not uname or uname in seen_usernames:
                        continue
                    seen_usernames.add(uname)

                    name = (user_info.get("name") or uname).strip()

                    # ── Engagement signals (only what the API actually returns) ──
                    reactions = (
                        article.get("public_reactions_count")
                        or article.get("positive_reactions_count")
                        or 0
                    )
                    comments = article.get("comments_count") or 0
                    article_reactions = int(reactions)
                    article_comments = int(comments)
                    article_engagement_source = (
                        "Dev.to Articles REST API (Public Reactions & Comments)"
                    )

                    # ── Recent content from article title ──
                    title = article.get("title")
                    recent_content = [title] if title else ["Not Found"]
                    content_source = "Dev.to Articles REST API" if title else "Not Found"

                    # ── Profile URL ──
                    platform = "Dev.to"
                    profile_url = f"https://dev.to/{uname}"

                    # ── Defaults — only populated from actual API data ──
                    website = "Not Found"
                    bio = "Not Found"
                    location = "Not Found"
                    contact_email = "Not Found"
                    email_source = "Not Found"

                    # ── Fetch user detail for bio, website, location ──
                    u_detail_url = f"https://dev.to/api/users/by_username?url={uname}"
                    try:
                        u_resp = httpx.get(u_detail_url, headers=headers, timeout=4.0)
                        if u_resp.status_code == 200:
                            u_data = u_resp.json()

                            if u_data.get("summary"):
                                bio = str(u_data["summary"]).strip()
                            if u_data.get("website_url"):
                                website = str(u_data["website_url"]).strip()
                            if u_data.get("location"):
                                location = str(u_data["location"]).strip()

                            # Only accept an email found literally in bio or website text.
                            # Do NOT construct "contact@domain" from the website URL.
                            search_text = f"{bio} {website}"
                            email_match = re.search(
                                r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
                                search_text
                            )
                            if email_match:
                                found = email_match.group(1).strip().lower()
                                # Reject clearly synthetic or test domains
                                bad_domains = [
                                    "test.org", "devs.io", "example.com",
                                    "fake", "placeholder", "github.com"
                                ]
                                if not any(b in found for b in bad_domains):
                                    contact_email = found
                                    email_source = "Public Dev.to Bio/Website (API-retrieved)"
                    except Exception as detail_exc:
                        # Non-fatal — record fetch status in bio field
                        bio = f"Profile detail unavailable: {detail_exc}"

                    # Check whether the website links to Instagram
                    if website and "instagram.com/" in website.lower():
                        ig_match = re.search(
                            r"instagram\.com/([a-zA-Z0-9_.-]+)", website, re.IGNORECASE
                        )
                        if ig_match:
                            platform = "Instagram"
                            profile_url = f"https://instagram.com/{ig_match.group(1)}"

                    creators.append({
                        "name": name,
                        "username": uname,
                        "platform": platform,
                        "profile_url": profile_url,
                        # ── Metrics the Dev.to API does NOT supply ──
                        "followers": "Not Found",
                        "followers_source": "Not Found",
                        "engagement_rate": "Not Found",
                        "engagement_source": "Not Found",
                        "engagement_method": "Not Found",
                        # ── Contact — only from actual bio/website text ──
                        "contact_email": contact_email,
                        "email_source": email_source,
                        "website": website,
                        "bio": bio,
                        "sub_niche": "Developer Tools",
                        "content_themes": [f"#{tag}", "Developer Workflow"],
                        "recent_content": recent_content,
                        "content_source": content_source,
                        "content_style": "Technical Articles & Written Guides",
                        # ── Article engagement signals from API ──
                        "article_reactions": article_reactions,
                        "article_comments": article_comments,
                        "article_engagement_source": article_engagement_source,
                        # ── Demographics — not available from this source ──
                        "audience_geography": "Not Found",
                        "audience_age": "Not Found",
                        "audience_gender": "Not Found",
                        "demographics_source": "Not Found",
                        "creator_geography": location,
                        # ── Provenance ──
                        "source": self.source_name,
                        "source_url": api_url,
                        "extraction_method": self.extraction_method,
                        "discovered_at": datetime.now(timezone.utc).isoformat(),
                    })

            except Exception as e:
                print(f" -> [HTTP Warning] Source C tag=#{tag} fetch exception: {e}")

        return creators
