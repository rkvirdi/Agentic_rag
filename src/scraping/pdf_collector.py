import os, glob, time
import urllib.parse as up
from typing import List, Dict

from src.utils.helpers import (
    RAW_HTML_DIR, RAW_PDF_DIR, RAW_META_DIR, ensure_dirs, fetch, append_jsonl,
    extract_links, is_same_domain, is_allowed_path, looks_like_pdf, polite_wait,
    sha256_bytes, safe_filename_from_url, HEADERS
)

# --------- CONFIGURE YOUR TARGETS HERE ----------
ALLOWED = {
    "www.lucidmotors.com": ["/ownership/air-essentials", "/ownership/knowledge-base"],
    "www.wellsfargo.com": ["/help"],
}

SEED_PDF_URLS: List[str] = [
    # Add direct PDF links if you already know a few
    # "https://www.example.com/path/to/manual.pdf",
]

def collect_pdf_links_from_html() -> List[str]:
    pdf_urls = set()
    for html_path in glob.glob(os.path.join(RAW_HTML_DIR, "*.html")):
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        # derive a base_url from saved filename? not stored, so we re-extract via links only
        # Instead of base_url, links were saved absolute by html_crawler (normalize_url + join)
        for link in extract_links(html, base_url=""):
            if looks_like_pdf(link):
                pdf_urls.add(link)
    return list(pdf_urls)

def allowed_pdf(url: str) -> bool:
    host = up.urlparse(url).netloc
    paths = ALLOWED.get(host)
    if not paths:
        return False
    return is_allowed_path(url, paths)

def download_pdf(url: str):
    host = up.urlparse(url).netloc
    if not allowed_pdf(url):
        return
    polite_wait()
    resp = fetch(url)
    if not resp or resp.status_code != 200:
        return
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "pdf" not in ctype and not looks_like_pdf(url):
        return
    data = resp.content
    digest = sha256_bytes(data)
    fname = safe_filename_from_url(url, ".pdf")
    out_path = os.path.join(RAW_PDF_DIR, fname)
    if not os.path.exists(out_path):
        with open(out_path, "wb") as f:
            f.write(data)
    append_jsonl(
        os.path.join(RAW_META_DIR, f"{host}.jsonl"),
        {
            "type": "pdf",
            "url": url,
            "path": out_path,
            "sha256": digest,
            "status": resp.status_code,
            "content_type": ctype,
            "fetched_at": int(time.time()),
        },
    )

def main():
    ensure_dirs()
    urls = set(SEED_PDF_URLS)
    urls.update(collect_pdf_links_from_html())
    print(f"Found {len(urls)} candidate PDF links.")
    for u in sorted(urls):
        download_pdf(u)
    print("PDF collection complete.")

if __name__ == "__main__":
    main()
