from src.utils.guardrails import apply_guardrails

def orchestrator_agent(state: dict) -> dict:
    query = state["query"]
    safe_query = apply_guardrails(query)
    return {"query": safe_query}
