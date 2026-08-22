def parse_demographics(raw_record: dict) -> dict:
    """
    Parse optional demographic and geography fields.
    Sets unavailable fields strictly to 'Not Found'.
    """
    return {
        "creator_geography": str(raw_record.get("creator_geography") or "Not Found").strip(),
        "audience_age": str(raw_record.get("audience_age") or "Not Found").strip(),
        "audience_gender": str(raw_record.get("audience_gender") or "Not Found").strip(),
        "audience_geography": str(raw_record.get("audience_geography") or "Not Found").strip(),
        "website": str(raw_record.get("website") or "Not Found").strip()
    }
