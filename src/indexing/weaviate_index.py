# src/indexing/weaviate_index.py
import os, json, warnings
from typing import List, Dict
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from weaviate.collections.classes.data import DataObject
from sentence_transformers import SentenceTransformer

# Quiet CPU warnings
warnings.filterwarnings("ignore", message=".*pin_memory.*")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
CHUNKS_PATH  = os.getenv("CHUNKS_PATH", "data/processed/chunks/all_chunks.jsonl")
CLASS_NAME   = os.getenv("WEAVIATE_CLASS", "DocChunk")
BATCH_SIZE   = int(os.getenv("BATCH_SIZE", "64"))
EMB_MODEL_ID = os.getenv("EMB_MODEL_ID", "all-MiniLM-L6-v2")   # light + fast


def load_chunks(path: str) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def ensure_schema(client: weaviate.WeaviateClient):
    existing = client.collections.list_all()
    if CLASS_NAME in existing:
        return
    client.collections.create(
        name=CLASS_NAME,
        properties=[
            Property(name="chunk_id",   data_type=DataType.TEXT),
            Property(name="text",       data_type=DataType.TEXT),
            Property(name="domain",     data_type=DataType.TEXT),
            Property(name="doc_type",   data_type=DataType.TEXT),
            Property(name="source_url", data_type=DataType.TEXT),
            Property(name="file_path",  data_type=DataType.TEXT),
            Property(name="section",    data_type=DataType.TEXT),
            Property(name="title",      data_type=DataType.TEXT),
            Property(name="sha256",     data_type=DataType.TEXT),
            Property(name="raw_id",     data_type=DataType.TEXT),
            Property(name="page_no",    data_type=DataType.INT),
        ],
        vector_config=Configure.Vectorizer.none(),  # no auto-vectorizer
    )


def main():
    # REST-only to avoid gRPC port issues locally
    client = weaviate.connect_to_local(skip_init_checks=True)
    try:
        ensure_schema(client)

        rows = load_chunks(CHUNKS_PATH)
        if not rows:
            print(f"[ERR] No rows in {CHUNKS_PATH}")
            return
        print(f"[OK] Loaded {len(rows)} chunks")

        model = SentenceTransformer(EMB_MODEL_ID, device="cpu")
        col = client.collections.get(CLASS_NAME)

        batch_objs: List[Dict] = []

        def flush():
            if not batch_objs:
                return
            objs = [
                DataObject(properties=obj["properties"], vector=obj["vector"])
                for obj in batch_objs
            ]
            col.data.insert_many(objs)
            batch_objs.clear()

        for i, r in enumerate(rows, start=1):
            text = (r.get("text") or "").strip()
            if not text:
                continue

            props = {
                "chunk_id":   r.get("chunk_id"),
                "text":       text,
                "domain":     r.get("domain"),
                "doc_type":   r.get("doc_type"),
                "source_url": r.get("source_url"),
                "file_path":  r.get("file_path"),
                "section":    r.get("section"),
                "title":      r.get("title"),
                "sha256":     r.get("sha256"),
                "raw_id":     r.get("raw_id"),
                "page_no":    int(r.get("page_no") or 0),
            }

            vec = model.encode(
                [text], batch_size=8, convert_to_numpy=True,
                normalize_embeddings=True
            )[0].tolist()

            batch_objs.append({"properties": props, "vector": vec})

            if len(batch_objs) >= BATCH_SIZE:
                flush()
            if i % 500 == 0:
                print(f"  upserted {i}...")

        flush()
        print("[DONE] indexing complete")
    finally:
        client.close()


if __name__ == "__main__":
    main()
