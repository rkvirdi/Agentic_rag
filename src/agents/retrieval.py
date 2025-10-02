from models.reranker import cross_encoder
from models.embeddings import embedding_model
from utils.weaviate_client import client
import operator

CLASS_NAME = "DocChunk"

def hybrid_retrieval_agent(state: dict) -> dict:
    query = state["query"]

    # Encode query to vector
    qvec = embedding_model.encode(
        [query], normalize_embeddings=True, convert_to_numpy=True
    )[0].tolist()

    # Query Weaviate collection
    col = client.collections.get(CLASS_NAME)
    response = col.query.near_vector(near_vector=qvec, limit=20)

    candidates = [
        {
            "doc_id": r.properties.get("chunk_id"),
            "text": r.properties.get("text", ""),
            "title": r.properties.get("title", ""),
        }
        for r in response.objects
    ]

    if not candidates:
        return {"retrieved_docs": [], "query": query}

    # Rerank with cross-encoder
    pairs = [(query, r["text"]) for r in candidates]
    scores = cross_encoder.predict(pairs)

    for i, r in enumerate(candidates):
        r["score"] = float(scores[i])

    reranked = sorted(candidates, key=operator.itemgetter("score"), reverse=True)
    top_k = reranked[:5]

    return {"retrieved_docs": top_k, "query": query}
