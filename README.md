Agentic RAG Project (Open Source)

This project implements an Agentic RAG pipeline using LangGraph
, Weaviate
, and open-source HuggingFace models only (no billing, no external APIs).
Each agent is modular, making the system easy to extend.

⚙️ Features

Orchestrator Agent → Guardrails (PII redaction, blocklist).

Intent Router → Simple query classification.

Planner / Decomposer → Breaks down multi-step queries.

Retrieval Agent → Weaviate dense vector search + Cross-Encoder reranking.

Synthesizer Agent → Generates grounded answers using open-source LLM (Flan-T5).

Validator Agent → Checks grounding (citations present).

All components are modular and live in agents/, models/, utils/.

📂 Project Structure
agentic_rag_project/
│
├── configs
├── docs
├── evals
├── notebooks
├── indexing
├── parsing
├── scraping
├── src/
    ├──main.py

|    ├── agents/
│   ├── orchestrator.py
│   ├── intent_router.py
│   ├── planner.py
│   ├── retrieval.py
│   ├── synthesizer.py
│   ├── validator.py
│
    ├──  models/
│   ├── embeddings.py
│   ├── reranker.py
│   ├── generator.py
│
    ├──  utils/
    ├── chunking.py
    ├── config.py
    ├── helpers.py
│   ├── weaviate_client.py
│   ├── guardrails.py
│   └── logger.py
│   
    ├──api/
    route.py

└── requirements.txt

🛠️ Installation
1. Clone repo
git clone <repo>
cd agentic_rag_project

2. Create environment
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Run Weaviate locally

If you don’t already have Weaviate running:

docker-compose.yml

OR

docker run -d --name weaviate \
  -p 8080:8080 \
  semitechnologies/weaviate:1.25.3 \
  --host 0.0.0.0 --port 8080 \
  --persistency.data-path /var/lib/weaviate

📥 Indexing Documents

Prepare your chunks (JSONL).
Run indexing:

python src/indexing/weaviate_index.py


This will embed chunks with all-MiniLM-L6-v2 and insert them into the DocChunk class.

🚀 Running the Agents

Once chunks are indexed:


🌐 Run as API (FastAPI + Uvicorn)
1. Make sure src/ has an __init__.py so it is importable:
src/
 ├── __init__.py   # empty file
 ├── api/
    ├── route.py
 ├── main.py
 ...

2. Start the API server

From project root:

uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

3. Test in Browser

Open http://localhost:8000/docs
 → Swagger UI.

Or use curl:

curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Compare treatment A with treatment B"}'


Response:

{
  "final_answer": "Answer [chunk_23]. Answer[chunk_41].",
  "error": null



🔧 Customization

Change Generator Model → in models/generator.py (default = flan-t5-base, replace with zephyr, falcon, etc).

Change Reranker Model → in models/reranker.py (cross-encoder/ms-marco-MiniLM-L-6-v2 is fast, you can upgrade to electra-base for more accuracy).

Change Embedding Model → in models/embeddings.py.

Schema → matches weaviate_index.py (DocChunk class).

✅ Roadmap

Add RAGAS Evaluator for automatic faithfulness scoring.

Extend Intent Router with HuggingFace zero-shot classifier.

Add conversation memory for multi-turn queries.

📝 License

MIT License — free to use, modify, extend.