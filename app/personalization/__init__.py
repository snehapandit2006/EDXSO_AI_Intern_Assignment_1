from typing import List, Dict, Any
from app.personalization.generator import generate_personalized_message


def run_personalization(qualified_creators: List[Dict[str, Any]], campaign_title: str) -> List[Dict[str, Any]]:
    """Run AI personalization engine for all qualified creators."""
    print(f"[Personalization Engine] Generating personalized Email & DM pitches for {len(qualified_creators)} qualified creators...")

    personalized_list = []
    for creator in qualified_creators:
        msg = generate_personalized_message(creator, campaign_title=campaign_title)
        combined = {**creator, "message": msg}
        personalized_list.append(combined)
        print(f" -> Generated pitches for @{creator.get('username')} (Email: {msg['email_word_count']} words, DM: {msg['dm_word_count']} words).")

    print(f"[Personalization Engine] Personalization complete for {len(personalized_list)} creators.")
    return personalized_list
