import os, glob, json, time
from typing import Dict
from src.utils.helpers import (
    RAW_HTML_DIR, RAW_PDF_DIR, RAW_META_DIR, ensure_dirs,
    sha256_bytes, append_jsonl
)

def file_sha256(path: str) -> str:
    with open(path, "rb") as f:
        return sha256_bytes(f.read())

def main():
    ensure_dirs()
    manifest_path = os.path.join(RAW_META_DIR, "manifest.jsonl")
    # Clear existing manifest (optional)
    if os.path.exists(manifest_path):
        os.remove(manifest_path)

    # HTML files
    for fp in glob.glob(os.path.join(RAW_HTML_DIR, "*.html")):
        rec = {
            "kind": "html",
            "path": fp,
            "sha256": file_sha256(fp),
            "seen_at": int(time.time()),
        }
        append_jsonl(manifest_path, rec)

    # PDFs
    for fp in glob.glob(os.path.join(RAW_PDF_DIR, "*.pdf")):
        rec = {
            "kind": "pdf",
            "path": fp,
            "sha256": file_sha256(fp),
            "seen_at": int(time.time()),
        }
        append_jsonl(manifest_path, rec)

    print("Manifest built:", manifest_path)

if __name__ == "__main__":
    main()
