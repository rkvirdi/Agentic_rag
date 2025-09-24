import os, queue, time
import urllib.parse as up
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field

from src.utils.helpers import (
    RAW_HTML_DIR, RAW_META_DIR, ensure_dirs, fetch, extract_links, append_jsonl,
    normalize_url, is_same_domain, is_allowed_path, get_robots_parser,
    sha256_bytes, safe_filename_from_url, polite_wait, looks_like_pdf
)

# --------- CONFIGURE YOUR TARGETS HERE ----------
MAX_DEPTH = 3
MAX_PAGES = 250

TARGETS = [
    {
        "base": "https://www.lucidmotors.com",
        "allow_paths": ["/ownership/air-essentials", "/ownership/knowledge-base"],
        "start_urls": [
            "https://www.lucidmotors.com/ownership/air-essentials",
            "https://www.lucidmotors.com/ownership/knowledge-base",
        ],
    },
    {
        "base": "https://www.wellsfargo.com",
        "allow_paths": ["/help"],
        "start_urls": ["https://www.wellsfargo.com/help/"],
    },
]

@dataclass
class CrawlState:
    visited: Set[str] = field(default_factory=set)
    count: int = 0

def crawl_domain(base: str, allow_paths: List[str], start_urls: List[str]):
    rp = get_robots_parser(base)
    base_host = up.urlparse(base).netloc
    state = CrawlState()
    q = queue.Queue()
    for u in start_urls:
        q.put((normalize_url(u), 0))

    while not q.empty() and state.count < MAX_PAGES:
        url, depth = q.get()
        if url in state.visited:
            continue
        state.visited.add(url)

        if not is_same_domain(url, base) or not is_allowed_path(url, allow_paths):
            continue
        if not rp.can_fetch("AgenticRAG-DevScraper/0.1 (+local dev)", url):
            continue

        polite_wait()
        resp = fetch(url)
        if not resp or resp.status_code != 200:
            continue

        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "text/html" not in ctype and not resp.text.strip().lower().startswith("<!doctype html"):
            continue  # skip non-HTML here (PDFs handled by pdf_collector.py)

        html = resp.text
        digest = sha256_bytes(html.encode("utf-8", errors="ignore"))
        fname = safe_filename_from_url(url, ".html")
        out_path = os.path.join(RAW_HTML_DIR, fname)
        if not os.path.exists(out_path):
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)

        append_jsonl(
            os.path.join(RAW_META_DIR, f"{base_host}.jsonl"),
            {
                "type": "html",
                "url": url,
                "path": out_path,
                "sha256": digest,
                "status": resp.status_code,
                "content_type": ctype,
                "fetched_at": int(time.time()),
                "depth": depth,
            },
        )

        if depth < MAX_DEPTH:
            for link in extract_links(html, url):
                if (
                    link not in state.visited
                    and is_same_domain(link, base)
                    and is_allowed_path(link, allow_paths)
                ):
                    q.put((link, depth + 1))

        state.count += 1

def main():
    ensure_dirs()
    for t in TARGETS:
        crawl_domain(t["base"], t["allow_paths"], t["start_urls"])
    print("HTML crawl complete.")

if __name__ == "__main__":
    main()
