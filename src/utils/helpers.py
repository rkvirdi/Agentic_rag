import os, re, time, json, hashlib, pathlib
import urllib.parse as up
from typing import Optional, Dict, List
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

# ---------- Paths (default) ----------
RAW_HTML_DIR = "data/raw/html"
RAW_PDF_DIR = "data/raw/pdfs"
RAW_META_DIR = "data/raw/metadata"

# ---------- Politeness / Requests ----------
REQUEST_TIMEOUT = 20
THROTTLE_SECONDS = 0.75
USER_AGENT = "AgenticRAG-DevScraper/0.1 (+local dev)"
HEADERS = {"User-Agent": USER_AGENT}

def ensure_dirs():
    for d in (RAW_HTML_DIR, RAW_PDF_DIR, RAW_META_DIR):
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

# ---------- IO ----------
def write_binary(path: str, content: bytes):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)

def write_text(path: str, text: str):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def append_jsonl(path: str, record: Dict):
    pathlib.Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ---------- Hash / Filenames ----------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def safe_filename_from_url(url: str, ext_hint: Optional[str] = None) -> str:
    parsed = up.urlparse(url)
    base = (parsed.netloc + parsed.path).strip("/")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    if not os.path.splitext(base)[1] and ext_hint:
        base += ext_hint
    return base or "index" + (ext_hint or "")

# ---------- URL / Robots ----------
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
        r = requests.get(robots, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        rp.parse(r.text.splitlines() if r.status_code == 200 else [])
    except Exception:
        rp.parse([])
    return rp

# ---------- Networking ----------
def fetch(url: str) -> Optional[requests.Response]:
    try:
        return requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    except requests.RequestException:
        return None

def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    hrefs = set()
    for tag in soup.find_all(["a", "area"]):
        href = tag.get("href")
        if not href:
            continue
        hrefs.add(normalize_url(up.urljoin(base_url, href)))
    return list(hrefs)

def polite_wait():
    time.sleep(THROTTLE_SECONDS)
