import re


def extract_contact_email(raw_email: any, bio: str = "") -> str:
    """
    Extract public contact email from raw input or bio text.
    If no valid email exists, strictly returns 'Not Found'.
    Never infers or fabricates email addresses.
    """
    if raw_email and isinstance(raw_email, str) and raw_email.strip().lower() != "not found":
        email_str = raw_email.strip()
        if re.match(r"[^@]+@[^@]+\.[^@]+", email_str):
            return email_str

    if bio:
        match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", bio)
        if match:
            return match.group(1)

    return "Not Found"
