from fastapi import FastAPI
from pydantic import BaseModel
from src.main import build_graph
from src.utils.weaviate_client import client

# Build graph once at startup
graph = build_graph()

app = FastAPI(title="Agentic RAG API")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    final_answer: str | None
    error: str | None = None


@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    try:
        result = graph.invoke({"query": request.query})
        return QueryResponse(
            final_answer=result.get("final_answer"),
            error=result.get("error")
        )
    except Exception as e:
        return QueryResponse(final_answer=None, error=str(e))


@app.on_event("shutdown")
def shutdown_event():
    # Cleanly close weaviate client
    client.close()
