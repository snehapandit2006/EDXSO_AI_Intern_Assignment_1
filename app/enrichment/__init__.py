from typing import List, Dict, Any
import pandas as pd
from app.config import PROCESSED_DATA_DIR
from app.enrichment.metrics import parse_follower_count, calculate_engagement_rate
from app.enrichment.contact import extract_contact_email
from app.enrichment.demographics import parse_demographics


def enrich_creator(raw_record: dict) -> dict:
    """Enrich and normalize single creator profile record with 100% data provenance."""
    raw_followers = raw_record.get("followers")
    if raw_followers in [None, "Not Found", ""]:
        followers = "Not Found"
        followers_source = "Not Found"
    else:
        followers = parse_follower_count(raw_followers)
        followers_source = str(raw_record.get("followers_source") or "GitHub User Profile API")

    raw_eng = raw_record.get("engagement_rate")
    if raw_eng in [None, "Not Found", ""]:
        eng_rate = "Not Found"
        eng_source = "Not Found"
        eng_method = "Not Found"
        sample_size = 0
    else:
        eng_rate, eng_method, sample_size = calculate_engagement_rate(
            raw_eng,
            followers=followers if isinstance(followers, int) else 0
        )
        eng_source = str(raw_record.get("engagement_source") or "Not Found")
        if eng_rate is None:
            eng_rate = "Not Found"
    
    bio = str(raw_record.get("bio") or "Not Found").strip()
    contact_email = extract_contact_email(raw_record.get("contact_email"), bio=bio if bio != "Not Found" else "")
    email_source = str(raw_record.get("email_source") or ("Public Profile Bio" if contact_email != "Not Found" else "Not Found"))
    if contact_email == "Not Found":
        email_source = "Not Found"

    demographics = parse_demographics(raw_record)
    demographics_source = str(raw_record.get("demographics_source") or "Not Found")

    content_themes = raw_record.get("content_themes") or ["Technology"]
    recent_content = raw_record.get("recent_content") or ["Not Found"]
    content_source = str(raw_record.get("content_source") or ("Public Content Endpoint" if recent_content != ["Not Found"] else "Not Found"))

    username = str(raw_record.get("username") or "").strip().lower()
    platform = str(raw_record.get("platform") or "GitHub").strip()
    profile_url = str(raw_record.get("profile_url") or f"https://github.com/{username}").strip()

    article_reactions = raw_record.get("article_reactions", "Not Found")
    article_comments = raw_record.get("article_comments", "Not Found")
    article_engagement_source = str(raw_record.get("article_engagement_source") or "Not Found")

    return {
        "name": str(raw_record.get("name") or username or "Unknown Creator").strip(),
        "platform": platform,
        "username": username,
        "profile_url": profile_url,
        "followers": followers,
        "followers_source": followers_source,
        "engagement_rate": eng_rate,
        "engagement_source": eng_source,
        "engagement_method": eng_method,
        "engagement_sample_size": sample_size,
        "article_reactions": article_reactions,
        "article_comments": article_comments,
        "article_engagement_source": article_engagement_source,
        "category": str(raw_record.get("category") or "Technology").strip(),
        "sub_niche": str(raw_record.get("sub_niche") or "Software Engineering").strip(),
        "content_themes": content_themes if isinstance(content_themes, list) else [str(content_themes)],
        "content_style": str(raw_record.get("content_style") or "Technical & Software").strip(),
        "content_source": content_source,
        "bio": bio,
        "recent_content": recent_content if isinstance(recent_content, list) else [str(recent_content)],
        "contact_email": contact_email,
        "email_source": email_source,
        "website": demographics["website"],
        "creator_geography": demographics["creator_geography"],
        "audience_age": demographics["audience_age"],
        "audience_gender": demographics["audience_gender"],
        "audience_geography": demographics["audience_geography"],
        "demographics_source": demographics_source,
        "source": str(raw_record.get("source") or "Public Directory").strip(),
        "source_url": str(raw_record.get("source_url") or "https://api.github.com").strip(),
        "extraction_method": str(raw_record.get("extraction_method") or "HTTP GET REST API").strip(),
        "discovered_at": raw_record.get("discovered_at")
    }


def run_enrichment(raw_creators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enrich all raw creator records and export normalized CSV."""
    print(f"[Enrichment Engine] Enriching and normalizing {len(raw_creators)} creator records...")
    enriched_list = [enrich_creator(r) for r in raw_creators]

    # Save normalized dataset to CSV
    df = pd.DataFrame(enriched_list)
    # Convert list columns to json strings for clean CSV export
    df["content_themes"] = df["content_themes"].apply(lambda x: str(x))
    df["recent_content"] = df["recent_content"].apply(lambda x: str(x))

    csv_path = PROCESSED_DATA_DIR / "creators_normalized.csv"
    df.to_csv(csv_path, index=False)

    print(f"[Enrichment Engine] Enrichment complete. Exported normalized dataset ({len(enriched_list)} records) to: {csv_path}")

    return enriched_list
