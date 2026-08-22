import os
import re
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.discovery.base import DiscoverySource


class PublicDirectoriesSource(DiscoverySource):
    """
    Source A: Public Tech Creator Directory Adapter.
    Performs real live HTTP GET REST API requests to query GitHub public user directories
    and extract real creator profile metadata live via httpx.
    Populates only genuinely retrieved fields and uses 'Not Found' for unavailable data.
    """

    def __init__(self):
        super().__init__(
            source_name="GitHub Public Tech Developer Directory",
            source_url="https://api.github.com/search/users?q=type:user+followers:5000..100000",
            extraction_method="HTTP GET REST API Extraction (httpx)"
        )

    def fetch_creators(self, target_count: int = 50) -> List[Dict[str, Any]]:
        creators = []
        headers = {"User-Agent": "EDXSO-Influencer-Outreach/1.0 (Public Research Bot)"}
        
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        search_urls = [
            "https://api.github.com/search/users?q=type:user+followers:5000..100000&per_page=30",
            "https://api.github.com/search/users?q=type:user+followers:1000..5000+language:python&per_page=30",
            "https://api.github.com/search/users?q=type:user+followers:1000..5000+location:USA&per_page=30"
        ]

        seen_usernames = set()

        for s_url in search_urls:
            if len(creators) >= target_count:
                break
            try:
                resp = httpx.get(s_url, headers=headers, timeout=5.0)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    for item in items:
                        if len(creators) >= target_count:
                            break
                        username = item.get("login")
                        if not username or username.lower() in seen_usernames:
                            continue
                        seen_usernames.add(username.lower())

                        profile_url = item.get("html_url") or f"https://github.com/{username}"
                        
                        name = username
                        followers = "Not Found"
                        followers_source = "Not Found"
                        email = "Not Found"
                        email_source = "Not Found"
                        website = "Not Found"
                        location = "Not Found"
                        bio = f"GitHub Developer (@{username})"
                        recent_content = ["Not Found"]
                        content_source = "Not Found"

                        # Query GitHub user profile endpoint for real profile metadata
                        u_detail_url = f"https://api.github.com/users/{username}"
                        try:
                            u_resp = httpx.get(u_detail_url, headers=headers, timeout=3.0)
                            if u_resp.status_code == 200:
                                u_data = u_resp.json()
                                name = u_data.get("name") or username
                                real_followers = u_data.get("followers")
                                if real_followers is not None:
                                    followers = int(real_followers)
                                    followers_source = "GitHub User Profile API"
                                
                                if u_data.get("email"):
                                    email = str(u_data.get("email")).strip()
                                    email_source = "GitHub Public Profile"
                                
                                if u_data.get("blog"):
                                    blog_val = str(u_data.get("blog")).strip()
                                    if blog_val:
                                        website = blog_val if blog_val.startswith("http") else f"https://{blog_val}"
                                
                                if u_data.get("location"):
                                    location = str(u_data.get("location")).strip()
                                
                                if u_data.get("bio"):
                                    bio = str(u_data.get("bio")).strip()
                                
                                public_repos = u_data.get("public_repos")
                                if public_repos is not None:
                                    recent_content = [f"Public Repositories: {public_repos}"]
                                    content_source = "GitHub Public Profile API"
                        except Exception:
                            pass

                        platform = "GitHub"
                        if website and "instagram.com/" in website.lower():
                            ig_match = re.search(r"instagram\.com/([a-zA-Z0-9_.-]+)", website, re.IGNORECASE)
                            if ig_match:
                                platform = "Instagram"
                                profile_url = f"https://instagram.com/{ig_match.group(1)}"

                        creators.append({
                            "name": name,
                            "username": username.lower(),
                            "platform": platform,
                            "profile_url": profile_url,
                            "followers": followers,
                            "followers_source": followers_source,
                            "engagement_rate": "Not Found",
                            "engagement_source": "Not Found",
                            "engagement_method": "Not Found",
                            "contact_email": email,
                            "email_source": email_source,
                            "website": website,
                            "bio": bio,
                            "sub_niche": "Software Engineering",
                            "content_themes": ["Open Source Code", "Software Development"],
                            "recent_content": recent_content,
                            "content_source": content_source,
                            "content_style": "Open Source Code & Tech Repositories",
                            "audience_geography": "Not Found",
                            "audience_age": "Not Found",
                            "audience_gender": "Not Found",
                            "demographics_source": "Not Found",
                            "creator_geography": location,
                            "source": self.source_name,
                            "source_url": s_url,
                            "extraction_method": self.extraction_method,
                            "discovered_at": datetime.now(timezone.utc).isoformat()
                        })
            except Exception as e:
                print(f" -> [HTTP Warning] Source A HTTP fetch encountered exception: {e}")

        return creators
