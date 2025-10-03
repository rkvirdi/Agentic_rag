from src.models.generator import generator

def synthesizer_agent(state: dict) -> dict:
    docs = state.get("retrieved_docs", [])
    query = state["query"]

    context = "\n".join([f"[{d['doc_id']}] {d['text']}" for d in docs])

    prompt = f"""
    Answer the question using only the context below.
    Cite sources with [doc_id].
    If you cannot find the answer, say "Not enough information."

    Context:
    {context}

    Question:
    {query}
    """

    output = generator(prompt, max_new_tokens=256)[0]["generated_text"]

    return {"answer": output}
