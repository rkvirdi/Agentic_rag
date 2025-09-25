import os, json
from typing import Dict, List, Optional
from urllib.parse import urlparse

from src.scraping.raw_cataloger import build_log_meta_map
from src.utils.helpers import RAW_META_DIR
from src.parsing.pdf_to_chunks import pdf_to_chunks
from src.parsing.html_to_chunks import html_to_chunks

OUT_DIR = "data/processed/chunks"
os.makedirs(OUT_DIR, exist_ok=True)


def _detect_domain(source_url: Optional[str], file_path: str) -> str:
    if source_url:
        host = urlparse(source_url).netloc.lower()
        if "wellsfargo" in host:
            return "wells"
        if "lucidmotors" in host or "lucid" in host:
            return "lucid"
    name = os.path.basename(file_path).lower()
    if "wells" in name:
        return "wells"
    if "lucid" in name or "air" in name:
        return "lucid"
    return "unknown"


def _chunk_id(prefix: str, idx: int, page_no: Optional[int]) -> str:
    return f"{prefix}_p{page_no or 0}_c{idx}"


def _write_jsonl(path: str, rows: List[Dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    manifest_path = os.path.join(RAW_META_DIR, "manifest.jsonl")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Missing manifest at {manifest_path}. Run raw_cataloger first.")

    # manifest path -> record
    path2manifest: Dict[str, Dict] = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "path" in rec:
                path2manifest[os.path.normpath(rec["path"])] = rec

    # per-host log metadata (adds source_url, raw_id)
    log_meta = build_log_meta_map()

    pdf_rows: List[Dict] = []
    html_rows: List[Dict] = []

    for norm_path, mrec in path2manifest.items():
        if not os.path.exists(norm_path):
            continue

        kind = mrec.get("kind")
        sha256 = mrec.get("sha256")
        source_url = mrec.get("source_url") or (log_meta.get(norm_path) or {}).get("source_url")
        raw_id = (log_meta.get(norm_path) or {}).get("raw_id") or f"manual:{os.path.basename(norm_path)}"
        domain = _detect_domain(source_url, norm_path)

        if kind == "pdf":
            chunks = pdf_to_chunks(norm_path, domain=domain, source_url=source_url)
            for i, ch in enumerate(chunks, start=1):
                prefix = os.path.splitext(os.path.basename(norm_path))[0]
                ch["chunk_id"] = _chunk_id(prefix, i, ch.get("page_no"))
                ch["sha256"] = sha256
                ch["raw_id"] = raw_id
            pdf_rows.extend(chunks)

        elif kind == "html":
            chunks = html_to_chunks(norm_path, source_url=source_url or "", domain=domain)
            for i, ch in enumerate(chunks, start=1):
                prefix = os.path.splitext(os.path.basename(norm_path))[0]
                ch["chunk_id"] = _chunk_id(prefix, i, None)
                ch["sha256"] = sha256
                ch["raw_id"] = raw_id
            html_rows.extend(chunks)

    out_pdf = os.path.join(OUT_DIR, "pdf_chunks.jsonl")
    out_html = os.path.join(OUT_DIR, "html_chunks.jsonl")
    out_all = os.path.join(OUT_DIR, "all_chunks.jsonl")

    _write_jsonl(out_pdf, pdf_rows)
    _write_jsonl(out_html, html_rows)
    _write_jsonl(out_all, pdf_rows + html_rows)

    print(f"[OK] PDF chunks:  {out_pdf} ({len(pdf_rows)} rows)")
    print(f"[OK] HTML chunks: {out_html} ({len(html_rows)} rows)")
    print(f"[OK] All chunks:  {out_all} ({len(pdf_rows) + len(html_rows)} rows)")


if __name__ == "__main__":
    main()
