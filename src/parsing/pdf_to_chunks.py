# src/parsing/pdf_to_chunks.py
"""
PDF → chunks
- Current mode: PyMuPDF only (fast, CPU-friendly).
- Docling code is kept but commented out for future use.
"""

from typing import Dict, List, Optional
import fitz  # PyMuPDF

from src.utils.chunking import heading_aware_chunks


# =========================
# PyMuPDF (active) extract
# =========================
def _pymupdf_extract(pdf_path: str) -> List[Dict]:
    out: List[Dict] = []
    doc = fitz.open(pdf_path)
    try:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            out.append({"page_no": i, "section": None, "text": text})
    finally:
        doc.close()
    return out


# ============================================================
# Docling (disabled for now) — keep for future GPU environments
# ============================================================
# try:
#     from docling.document_converter import DocumentConverter
#     _DOCLING_AVAILABLE = True
# except Exception:
#     _DOCLING_AVAILABLE = False
#
# def _docling_extract(pdf_path: str) -> List[Dict]:
#    """
#    Rich PDF extraction (headings/structure/tables) via Docling.
#    Requires heavy models; best on a GPU box.
#    """
#    dc = DocumentConverter()
#    result = dc.convert(pdf_path)
#    out: List[Dict] = []
#    for i, page in enumerate(result.document.pages, start=1):
#        # prefer plain_text; fallback to get_text if available
#        page_text = getattr(page, "plain_text", None) or (
#            page.get_text() if hasattr(page, "get_text") else ""
#        )
#        section = None
#        if hasattr(page, "headings") and page.headings:
#            section = " > ".join([h.text for h in page.headings if getattr(h, "text", None)])
#        out.append({"page_no": i, "section": section, "text": page_text or ""})
#    return out


def pdf_to_chunks(
    pdf_path: str,
    domain: str,
    source_url: Optional[str] = None,
    max_tokens: int = 300,
    overlap_ratio: float = 0.15,
) -> List[Dict]:
    """
    Convert a PDF into chunk dicts.
    Current behavior uses PyMuPDF. To re-enable Docling later:
      1) Uncomment the Docling import + _docling_extract above.
      2) Replace `_pymupdf_extract(pdf_path)` with `_docling_extract(pdf_path)`.
    """
    # --- ACTIVE PATH (fast): PyMuPDF ---
    pages = _pymupdf_extract(pdf_path)

    # --- FUTURE (rich) PATH: Docling ---
    # pages = _docling_extract(pdf_path) if _DOCLING_AVAILABLE else _pymupdf_extract(pdf_path)

    all_chunks: List[Dict] = []
    for rec in pages:
        page_no, section, text = rec["page_no"], rec["section"], rec["text"]
        chunks = heading_aware_chunks(
            [text],
            max_tokens=max_tokens,
            overlap_ratio=overlap_ratio,
            section_path=section,
            page_no=page_no,
        )
        for ch in chunks:
            ch.update({
                "domain": domain,
                "doc_type": "pdf",
                "file_path": pdf_path,
                "source_url": source_url,
            })
        all_chunks.extend(chunks)

    return all_chunks
