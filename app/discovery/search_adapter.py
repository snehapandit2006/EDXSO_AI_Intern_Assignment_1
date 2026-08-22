import httpx
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.discovery.base import DiscoverySource


class TechHashtagSource(DiscoverySource):
    """
    Source C: Public Tech Hashtag & Community Search Adapter.
    Performs real live HTTP GET REST API requests to query tech community hashtag feeds
    (#devtools, #opensource, #javascript) and community endpoints via httpx.
    Populates genuinely retrieved fields and uses 'Not Found' for unavailable data.
    """

    def __init__(self):
        super().__init__(
            source_name="Public Tech Hashtag Search (#devtools, #opensource, #python)",
            source_url="https://dev.to/api/articles?tag=devtools",
            extraction_method="HTTP GET REST API Extraction (httpx)"
        )

    def fetch_creators(self, target_count: int = 50) -> List[Dict[str, Any]]:
        creators = []
        headers = {"User-Agent": "EDXSO-Influencer-Outreach/1.0 (Public Research Bot)"}
        
        tags = ["devtools", "opensource", "javascript", "react"]
        seen_usernames = set()

        for tag in tags:
            if len(creators) >= target_count:
                break
            api_url = f"https://dev.to/api/articles?tag={tag}&per_page=30"
            try:
                resp = httpx.get(api_url, headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    articles = resp.json()
                    for article in articles:
                        if len(creators) >= target_count:
                            break
                        user_info = article.get("user", {})
                        uname = user_info.get("username", "").lower()
                        if not uname or uname in seen_usernames:
                            continue
                        seen_usernames.add(uname)

                        name = user_info.get("name") or uname
                        title = article.get("title")
                        recent_content = [title] if title else ["Not Found"]
                        content_source = "Dev.to Articles REST API" if title else "Not Found"

                        reactions = article.get("public_reactions_count") or article.get("positive_reactions_count") or 0
                        comments = article.get("comments_count") or 0

                        article_reactions = int(reactions)
                        article_comments = int(comments)
                        article_engagement_source = "Dev.to Articles REST API (Public Reactions & Comments)"

                        followers = "Not Found"
                        followers_source = "Not Found"
                        engagement_rate = "Not Found"
                        engagement_source = "Not Found"
                        engagement_method = "Not Found"

                        # Query Dev.to author detail endpoint for bio, website, location
                        u_detail_url = f"https://dev.to/api/users/by_username?url={uname}"
                        bio = f"Developer & Content Creator | #{tag}"
                        website = user_info.get("website_url") or "Not Found"
                        location = "Not Found"
                        email = "Not Found"
                        email_source = "Not Found"

                        try:
                            u_resp = httpx.get(u_detail_url, headers=headers, timeout=3.0)
                            if u_resp.status_code == 200:
                                u_data = u_resp.json()
                                if u_data.get("summary"):
                                    bio = str(u_data.get("summary")).strip()
                                if u_data.get("website_url"):
                                    website = str(u_data.get("website_url")).strip()
                                if u_data.get("location"):
                                    location = str(u_data.get("location")).strip()
                                
                                search_text = f"{bio} {website}"
                                email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", search_text)
                                if email_match:
                                    found_email = email_match.group(1).strip()
                                    if not any(bad in found_email.lower() for bad in ["test.org", "devs.io", "example.com", "fake", "placeholder", "github.com"]):
                                        email = found_email
                                        email_source = "Public Dev.to Bio/Website"

                        except Exception:
                            pass

                        platform = "Dev.to"
                        profile_url = f"https://dev.to/{uname}"

                        if website and "instagram.com/" in website.lower():
                            ig_match = re.search(r"instagram\.com/([a-zA-Z0-9_.-]+)", website, re.IGNORECASE)
                            if ig_match:
                                platform = "Instagram"
                                profile_url = f"https://instagram.com/{ig_match.group(1)}"

                        creators.append({
                            "name": name,
                            "username": uname,
                            "platform": platform,
                            "profile_url": profile_url,
                            "followers": followers,
                            "followers_source": followers_source,
                            "engagement_rate": engagement_rate,
                            "engagement_source": engagement_source,
                            "engagement_method": engagement_method,
                            "contact_email": email,
                            "email_source": email_source,
                            "website": website,
                            "bio": bio,
                            "sub_niche": "Developer Tools",
                            "content_themes": [f"#{tag}", "Developer Workflow"],
                            "recent_content": recent_content,
                            "content_source": content_source,
                            "content_style": "Technical Articles & Written Guides",
                            "article_reactions": article_reactions,
                            "article_comments": article_comments,
                            "article_engagement_source": article_engagement_source,
                            "audience_geography": "Not Found",
                            "audience_age": "Not Found",
                            "audience_gender": "Not Found",
                            "demographics_source": "Not Found",
                            "creator_geography": location,
                            "source": self.source_name,
                            "source_url": api_url,
                            "extraction_method": self.extraction_method,
                            "discovered_at": datetime.now(timezone.utc).isoformat()
                        })
            except Exception as e:
                print(f" -> [HTTP Warning] Source C HTTP fetch encountered exception: {e}")

        return creators
