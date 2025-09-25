# src/utils/helpers.py
# Shared helpers for scraping pipeline (config-driven)

import os
import re
import json
import time
import hashlib
import pathlib
import urllib.parse as up
from typing import Optional, Dict, List, Any

import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

# ---------- Paths (project-standard) ----------
RAW_HTML_DIR = "data/raw/html"
RAW_PDF_DIR = "data/raw/pdfs"
RAW_META_DIR = "data/raw/metadata"

# ---------- Runtime-configurable network settings ----------
CURRENT_CFG: Dict[str, Any] = {
    "USER_AGENT": "AgenticRAG-DevScraper/0.1 (+local dev)",
    "THROTTLE_SECONDS": 0.75,
    "REQUEST_TIMEOUT": 20,
}

def apply_runtime_config(user_agent: str, throttle: float, timeout: int):
    """
    Called by html_crawler/pdf_collector after loading YAML config.
    """
    CURRENT_CFG["USER_AGENT"] = user_agent or CURRENT_CFG["USER_AGENT"]
    CURRENT_CFG["THROTTLE_SECONDS"] = float(throttle) if throttle is not None else CURRENT_CFG["THROTTLE_SECONDS"]
    CURRENT_CFG["REQUEST_TIMEOUT"] = int(timeout) if timeout is not None else CURRENT_CFG["REQUEST_TIMEOUT"]

def get_headers() -> Dict[str, str]:
    return {"User-Agent": CURRENT_CFG["USER_AGENT"]}

def polite_wait():
    time.sleep(float(CURRENT_CFG["THROTTLE_SECONDS"]))

# ---------- Filesystem ----------
def ensure_dirs():
    for d in (RAW_HTML_DIR, RAW_PDF_DIR, RAW_META_DIR):
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

def write_binary(path: str, content: bytes):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)

def write_text(path: str, text: str):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def append_jsonl(path: str, record: Dict):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True
    )
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ---------- Hash / Filenames ----------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def safe_filename_from_url(url: str, ext_hint: Optional[str] = None) -> str:
    """
    Create a filesystem-safe filename from a URL, preserving extension if present.
    """
    parsed = up.urlparse(url)
    base = (parsed.netloc + parsed.path).strip("/")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    if not os.path.splitext(base)[1] and ext_hint:
        base += ext_hint
    return base or ("index" + (ext_hint or ""))

# ---------- URL / Robots / Requests ----------
def normalize_url(url: str) -> str:
    parsed = up.urlparse(url)
    cleaned = parsed._replace(fragment="", query=parsed.query.strip()).geturl()
    if cleaned.endswith("//"):
        cleaned = cleaned[:-1]
    return cleaned

def is_same_domain(url: str, base: str) -> bool:
    return up.urlparse(url).netloc == up.urlparse(base).netloc

def is_allowed_path(url: str, allow_paths: List[str]) -> bool:
    path = up.urlparse(url).path or "/"
    return any(path.startswith(p) for p in allow_paths)

def looks_like_pdf(url: str) -> bool:
    return up.urlparse(url).path.lower().endswith(".pdf")

def get_robots_parser(base: str) -> RobotFileParser:
    robots = up.urljoin(base, "/robots.txt")
    rp = RobotFileParser()
    try:
        r = requests.get(robots, headers=get_headers(), timeout=int(CURRENT_CFG["REQUEST_TIMEOUT"]))
        rp.parse(r.text.splitlines() if r.status_code == 200 else [])
    except Exception:
        rp.parse([])
    return rp

def fetch(url: str) -> Optional[requests.Response]:
    try:
        return requests.get(
            url,
            headers=get_headers(),
            timeout=int(CURRENT_CFG["REQUEST_TIMEOUT"]),
            allow_redirects=True,
        )
    except requests.RequestException:
        return None

# ---------- HTML parsing ----------
def extract_links(html: str, base_url: str) -> List[str]:
    """
    Extract absolute links from HTML, resolving relative links against base_url.
    """
    soup = BeautifulSoup(html, "html.parser")
    hrefs = set()
    for tag in soup.find_all(["a", "area"]):
        href = tag.get("href")
        if not href:
            continue
        abs_url = up.urljoin(base_url, href)
        hrefs.add(normalize_url(abs_url))
    return list(hrefs)
