from typing import Dict, Any
from app.config import EMAIL_MIN_WORDS, EMAIL_MAX_WORDS, DM_MIN_WORDS, DM_MAX_WORDS


def build_personalization_prompt(creator: Dict[str, Any], campaign_title: str, collaboration_type: str) -> str:
    """Build structured prompt for Gemini LLM personalization."""
    name = creator.get("name", "Creator")
    first_name = name.split()[0] if name else "there"
    username = creator.get("username", "")
    bio = creator.get("bio", "")
    sub_niche = creator.get("sub_niche", "Technology")
    themes = creator.get("content_themes", [])
    recent = creator.get("recent_content", [])
    style = creator.get("content_style", "")

    themes_str = ", ".join(themes) if isinstance(themes, list) else str(themes)
    recent_str = ", ".join(recent) if isinstance(recent, list) else str(recent)

    prompt = f"""
You are an expert AI Influencer Outreach Strategist representing the '{campaign_title}' ({collaboration_type}).

Write a personalized Email pitch AND an Instagram Direct Message (DM) for creator {name} (@{username}).

CREATOR PROFILE SIGNALS:
- First Name: {first_name}
- Bio: {bio}
- Sub-niche: {sub_niche}
- Content Themes: {themes_str}
- Content Style: {style}
- Recent Posts / Topics: {recent_str}

STRICT FACTUAL GROUNDING MANDATE:
- Use ONLY supplied factual signals from the creator's profile above.
- NEVER invent recent posts, audience demographics, achievements, metrics, or non-existent content.
- If a signal is unavailable or marked 'Not Found', omit it gracefully and focus on confirmed sub-niche/theme signals.

STRICT WORD COUNT & FORMATTING CONSTRAINTS:
1. EMAIL SUBJECT LINE: High-converting, non-spammy subject line.
2. EMAIL BODY: Exactly between {EMAIL_MIN_WORDS} and {EMAIL_MAX_WORDS} words.
   - Must address {first_name} by name.
   - Must reference a specific confirmed topic or theme from their profile ({recent_str}).
   - Clearly state the value proposition of collaborating on our AI developer tools.
   - End with a low-friction CTA (e.g. 15-minute quick chat).
3. INSTAGRAM DM: Exactly between {DM_MIN_WORDS} and {DM_MAX_WORDS} words.
   - Concise, friendly, and informal tone.
   - Reference their work on {sub_niche} or {recent_str}.
   - Invite them to check their email or reply if open to collab.

OUTPUT FORMAT (Respond EXACTLY in this JSON structure):
{{
  "email_subject": "<Subject line>",
  "email_body": "<Email body string>",
  "dm_body": "<DM string>",
  "personalization_signals_used": [
    "<Specific post signal 1>",
    "<Specific profile signal 2>"
  ]
}}
"""
    return prompt.strip()
