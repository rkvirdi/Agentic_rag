def intent_router_agent(state: dict) -> dict:
    query = state["query"]

    if "how to" in query.lower():
        intent = "procedural"
    elif "error" in query.lower():
        intent = "troubleshooting"
    else:
        intent = "retrieval_needed"

    return {"intent": intent, "query": query}
