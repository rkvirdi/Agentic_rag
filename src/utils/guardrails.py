import re

def apply_guardrails(query: str) -> str:
    # Redact emails
    query = re.sub(r"\S+@\S+", "[REDACTED_EMAIL]", query)

    # Basic blocklist
    if any(word in query.lower() for word in ["kill", "terror", "bomb"]):
        return "[BLOCKED_QUERY]"

    return query
