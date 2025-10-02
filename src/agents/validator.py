def validator_agent(state: dict) -> dict:
    answer = state.get("answer", "")

    if not answer or "[" not in answer:
        return {"final_answer": None, "error": "Ungrounded or empty answer"}

    return {"final_answer": answer}
