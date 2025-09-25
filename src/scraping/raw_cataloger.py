# src/scraping/raw_cataloger.py
import os, glob, json, time
from typing import Dict

from src.utils.helpers import (
    RAW_HTML_DIR, RAW_PDF_DIR, RAW_META_DIR, ensure_dirs,
    sha256_bytes, append_jsonl
)

def file_sha256(path: str) -> str:
    with open(path, "rb") as f:
        return sha256_bytes(f.read())

def file_info(path: str) -> Dict:
    st = os.stat(path)
    return {
        "size_bytes": st.st_size,
        "mtime": int(st.st_mtime),
    }

def build_path_to_url_map() -> Dict[str, str]:
    """
    Read all per-host logs in data/raw/metadata/*.jsonl and map saved file path -> source URL.
    Skips the combined manifest file.
    """
    path2url: Dict[str, str] = {}
    for log_path in glob.glob(os.path.join(RAW_META_DIR, "*.jsonl")):
        host = os.path.splitext(os.path.basename(log_path))[0]
        if host == "manifest":
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                p = rec.get("path")
                u = rec.get("url")
                if p and u:
                    path2url[os.path.normpath(p)] = u
    return path2url

def build_log_meta_map() -> Dict[str, Dict]:
    """
    Map normalized raw file path -> {"source_url": <url>, "raw_id": "<host>.jsonl:<line_no>"}.
    Uses per-domain crawl logs in data/raw/metadata/*.jsonl. Skips manifest.
    """
    path2meta: Dict[str, Dict] = {}
    for log_path in glob.glob(os.path.join(RAW_META_DIR, "*.jsonl")):
        host = os.path.splitext(os.path.basename(log_path))[0]
        if host == "manifest":
            continue
        with open(log_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                p = rec.get("path")
                u = rec.get("url")
                if not p:
                    continue
                norm = os.path.normpath(p)
                path2meta[norm] = {
                    "source_url": u,
                    "raw_id": f"{host}.jsonl:{i}",
                }
    return path2meta

def main():
    ensure_dirs()
    manifest_path = os.path.join(RAW_META_DIR, "manifest.jsonl")
    if os.path.exists(manifest_path):
        os.remove(manifest_path)

    path2url = build_path_to_url_map()
    seen_hashes = set()
    total = 0

    def emit(kind: str, fp: str):
        nonlocal total
        norm_fp = os.path.normpath(fp)
        h = file_sha256(norm_fp)
        if h in seen_hashes:
            return
        seen_hashes.add(h)
        info = file_info(norm_fp)
        rec = {
            "kind": kind,
            "path": norm_fp,
            "sha256": h,
            "seen_at": int(time.time()),
            "size_bytes": info["size_bytes"],
            "mtime": info["mtime"],
        }
        # attach source URL if we have it (from crawl logs)
        if norm_fp in path2url:
            rec["source_url"] = path2url[norm_fp]
        append_jsonl(manifest_path, rec)
        total += 1

    for fp in glob.glob(os.path.join(RAW_HTML_DIR, "*.html")):
        emit("html", fp)
    for fp in glob.glob(os.path.join(RAW_PDF_DIR, "*.pdf")):
        emit("pdf", fp)

    print(f"Manifest built: {manifest_path} ({total} records)")

if __name__ == "__main__":
    main()
