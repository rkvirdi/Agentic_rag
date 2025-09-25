# src/parsing/html_to_chunks.py
import os
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

from src.utils.chunking import heading_aware_chunks


def _extract_title_and_sections(html: str) -> Dict:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title else ""
    heads = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
    section_path = " > ".join(heads[:3]) if heads else None
    return {"title": title, "section_path": section_path}


def _simple_main_text(html: str) -> str:
    """
    Minimal main-text extractor:
    - removes script/style/noscript
    - drops common layout blocks via selectors
    - returns visible text with normalized newlines
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    for sel in ["nav", "header", "footer", "form", "aside"]:
        for t in soup.select(sel):
            t.decompose()

    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def html_to_chunks(
    html_path: str,
    source_url: str,
    domain: str,
    max_tokens: int = 300,
    overlap_ratio: float = 0.15,
) -> List[Dict]:
    with open(html_path, "r", encoding="utf-8") as f:
        raw_html = f.read()

    meta = _extract_title_and_sections(raw_html)
    main_text = _simple_main_text(raw_html)

    paragraphs: List[str] = [p for p in (ln.strip() for ln in main_text.split("\n")) if p]
    chunks = heading_aware_chunks(
        paragraphs,
        max_tokens=max_tokens,
        overlap_ratio=overlap_ratio,
        section_path=meta["section_path"],
        page_no=None,
    )

    for ch in chunks:
        ch.update({
            "domain": domain,
            "doc_type": "html",
            "source_url": source_url,
            "title": meta["title"],
            "file_path": html_path,
        })
    return chunks
