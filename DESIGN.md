agentic_rag_project/
│
├── data/
│   ├── raw/
│   │   ├── html/          # raw scraped HTML pages
│   │   ├── pdfs/          # downloaded PDFs (e.g., Lucid manuals)
│   │   └── metadata/      # crawl logs, sitemap json, etag/last-modified
│   ├── processed/
│   │   ├── chunks/        # JSONL/Parquet with cleaned + chunked docs
│   │   └── assets/        # extracted images, diagrams from PDFs
│   └── index/             # optional backup of embeddings/vector index
│
├── src/
│   ├── scraping/          # crawlers & downloaders
│   ├── parsing/           # html/pdf parsers, chunking utilities
│   ├── indexing/          # code to push docs → Weaviate
│   ├── agents/            # LangGraph nodes (router, planner, retriever, etc.)
│   ├── api/               # FastAPI endpoints (/ask, /healthz, etc.)
│   └── utils/             # shared utils (logging, config, validation)
│
├── notebooks/             # quick experiments, evals, RAGAS runs
│
├── evals/
│   ├── queries/           # test queries for Lucid & Wells Fargo
│   ├── results/           # ragas / trulens metrics JSON
│   └── reports/           # markdown/pdf summaries
│
├── configs/
│   ├── weaviate.yaml      # schema/class definitions
│   ├── models.yaml        # llm + embedding choices
│   └── crawler.yaml       # domain allowlists, sitemap roots
│
├── docs/
│   ├── architecture_diagram.png
│   ├── design_notes.md
│   └── api_examples.md
│
├── tests/                 # pytest or unit tests (scraper, parser, retriever)
│
├── docker-compose.yml     # Weaviate + Ollama (if needed)
├── requirements.txt       # Python deps
├── README.md              # setup + usage guide
└── .env.example           # placeholder for local config (keys, ports)
