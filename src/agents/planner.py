def planner_agent(state: dict) -> dict:
    query = state["query"]
    if state["intent"] == "retrieval_needed" and "compare" in query.lower():
        sub_queries = query.split("compare")
        return {"sub_queries": sub_queries, "query": query}
    return {"sub_queries": [query], "query": query}
