import os, time, json, glob, urllib.parse as up
from typing import List, Dict, Any

from src.utils.config import load_config, get_crawler_cfg
from src.utils.helpers import (
    RAW_HTML_DIR, RAW_PDF_DIR, RAW_META_DIR, ensure_dirs, fetch, append_jsonl,
    extract_links, is_allowed_path, looks_like_pdf, polite_wait,
    sha256_bytes, safe_filename_from_url, apply_runtime_config
)

def iter_html_records_from_logs():
    for log_path in glob.glob(os.path.join(RAW_META_DIR, "*.jsonl")):
        host = os.path.splitext(os.path.basename(log_path))[0]
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") == "html" and "url" in rec and "path" in rec:
                    yield rec["url"], rec["path"], host

def allowed_pdf(url: str, allowed_map: Dict[str, List[str]]) -> bool:
    host = up.urlparse(url).netloc
    paths = allowed_map.get(host)
    if not paths:
        return False
    return is_allowed_path(url, paths)

def collect_pdf_links(allowed_map: Dict[str, List[str]]) -> List[str]:
    pdf_urls = set()
    count_pages = 0
    for page_url, html_path, host in iter_html_records_from_logs():
        count_pages += 1
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
        except FileNotFoundError:
            continue
        for link in extract_links(html, base_url=page_url):
            if looks_like_pdf(link) and allowed_pdf(link, allowed_map):
                pdf_urls.add(link)
    print(f"Scanned {count_pages} HTML pages; found {len(pdf_urls)} PDF links.")
    for u in list(sorted(pdf_urls))[:5]:
        print("PDF CANDIDATE:", u)
    return sorted(pdf_urls)

def download_pdf(url: str, allowed_map: Dict[str, List[str]]):
    import urllib.parse as up
    host = up.urlparse(url).netloc
    if not allowed_pdf(url, allowed_map):
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

def main(config_path: str = "configs/crawler.yaml"):
    cfg = load_config(config_path)
    c = get_crawler_cfg(cfg)
    apply_runtime_config(c.user_agent, c.throttle_seconds, c.request_timeout)
    ensure_dirs()

    allowed_map = cfg.get("pdf_allowed_hosts", {})
    urls = set(cfg.get("seed_pdf_urls", []))
    urls.update(collect_pdf_links(allowed_map))

    print(f"Found {len(urls)} candidate PDF links.")
    for u in urls:
        download_pdf(u, allowed_map)
    print("PDF collection complete.")

if __name__ == "__main__":
    main()
