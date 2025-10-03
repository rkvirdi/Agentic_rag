import re

def apply_guardrails(query: str) -> str:
    

    # Basic blocklist
    if any(word in query.lower() for word in ["kill", "terror", "bomb"]):
        return "[BLOCKED_QUERY]"

    return query
