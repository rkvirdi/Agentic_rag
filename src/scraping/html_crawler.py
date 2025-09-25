import os, queue, time, urllib.parse as up
from dataclasses import dataclass, field
from typing import List, Set, Dict, Any

from src.utils.config import load_config, get_crawler_cfg
from src.utils.helpers import (
    RAW_HTML_DIR, RAW_META_DIR, ensure_dirs, fetch, extract_links, append_jsonl,
    normalize_url, is_same_domain, is_allowed_path, get_robots_parser,
    sha256_bytes, safe_filename_from_url, polite_wait, apply_runtime_config, get_headers
)

@dataclass
class CrawlState:
    visited: Set[str] = field(default_factory=set)
    count: int = 0

def crawl_domain(target: Dict[str, Any], limits: Dict[str, int]):
    base: str = target["base"]
    allow_paths: List[str] = target["allow_paths"]
    start_urls: List[str] = target["start_urls"]
    max_depth = limits["max_depth"]
    max_pages = limits["max_pages"]

    rp = get_robots_parser(base)
    base_host = up.urlparse(base).netloc
    state = CrawlState()
    q = queue.Queue()
    for u in start_urls:
        q.put((normalize_url(u), 0))

    while not q.empty() and state.count < max_pages:
        url, depth = q.get()
        if url in state.visited:
            continue
        state.visited.add(url)

        if not is_same_domain(url, base) or not is_allowed_path(url, allow_paths):
            continue
        if not rp.can_fetch(get_headers()["User-Agent"], url):
            continue

        polite_wait()
        resp = fetch(url)
        if not resp or resp.status_code != 200:
            continue

        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "text/html" not in ctype and not resp.text.strip().lower().startswith("<!doctype html"):
            continue

        html = resp.text
        digest = sha256_bytes(html.encode("utf-8", errors="ignore"))
        fname = safe_filename_from_url(url, ".html")
        out_path = os.path.join(RAW_HTML_DIR, fname)
        if not os.path.exists(out_path):
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
        print(f"SAVED HTML: {url} -> {out_path}")

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

        if depth < max_depth:
            for link in extract_links(html, url):
                if link not in state.visited and is_same_domain(link, base) and is_allowed_path(link, allow_paths):
                    q.put((link, depth + 1))

        state.count += 1

def main(config_path: str = "configs/crawler.yaml"):
    cfg = load_config(config_path)
    c = get_crawler_cfg(cfg)
    apply_runtime_config(c.user_agent, c.throttle_seconds, c.request_timeout)
    ensure_dirs()

    for target in cfg.get("targets", []):
        crawl_domain(target, {"max_depth": c.max_depth, "max_pages": c.max_pages})
    print("HTML crawl complete.")

if __name__ == "__main__":
    main()
