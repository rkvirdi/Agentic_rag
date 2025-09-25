# src/utils/chunking.py
# Chunking utilities backed by LangChain's RecursiveCharacterTextSplitter.
# Falls back to a simple word-based splitter if LangChain isn't available.

from typing import List, Dict, Optional

# ---- Try LangChain splitter; fallback if missing ----
_USE_LANGCHAIN = True
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except Exception:
    _USE_LANGCHAIN = False


def _fallback_word_chunks(
    text: str,
    max_tokens: int,
    overlap_ratio: float,
) -> List[str]:
    """
    Very simple word-based chunker: splits on whitespace with overlap.
    Used only if LangChain is not installed.
    """
    words = (text or "").split()
    if not words:
        return []

    overlap = max(0, int(max_tokens * overlap_ratio))
    step = max(1, max_tokens - overlap)

    out: List[str] = []
    for start in range(0, len(words), step):
        piece = words[start : start + max_tokens]
        if not piece:
            break
        out.append(" ".join(piece))
    return out


def _build_splitter(
    max_tokens: int = 300,
    overlap_ratio: float = 0.15,
    separators: Optional[List[str]] = None,
):
    """
    Build a LangChain RecursiveCharacterTextSplitter with sensible defaults.
    chunk_size ~= max_tokens (word-ish proxy), chunk_overlap = int(max_tokens * overlap_ratio).
    """
    if separators is None:
        # Prefer bigger semantic boundaries first, then finer
        separators = ["\n\n", "\n", ". ", " ", ""]

    chunk_overlap = max(0, int(max_tokens * overlap_ratio))
    return RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=chunk_overlap,
        separators=separators,
        keep_separator=False,
    )


def chunk_text(
    text: str,
    max_tokens: int = 300,
    overlap_ratio: float = 0.15,
    section_path: Optional[str] = None,
    page_no: Optional[int] = None,
) -> List[Dict]:
    """
    Split a single block of text into chunks.
    Returns a list of dicts with fields: text, page_no, section.
    """
    if not text:
        return []

    if _USE_LANGCHAIN:
        splitter = _build_splitter(max_tokens=max_tokens, overlap_ratio=overlap_ratio)
        pieces = splitter.split_text(text)
    else:
        pieces = _fallback_word_chunks(text, max_tokens=max_tokens, overlap_ratio=overlap_ratio)

    return [
        {
            "text": piece.strip(),
            "page_no": page_no,
            "section": section_path,
        }
        for piece in pieces
        if piece and piece.strip()
    ]


def heading_aware_chunks(
    paragraphs: List[str],
    max_tokens: int = 300,
    overlap_ratio: float = 0.15,
    section_path: Optional[str] = None,
    page_no: Optional[int] = None,
) -> List[Dict]:
    """
    Split a list of paragraphs/sections, preserving their boundaries by chunking within each.
    This mirrors your previous API so pdf/html parsers can call it unchanged.
    """
    out: List[Dict] = []
    if not paragraphs:
        return out

    if _USE_LANGCHAIN:
        splitter = _build_splitter(max_tokens=max_tokens, overlap_ratio=overlap_ratio)
        for para in paragraphs:
            if not para or not para.strip():
                continue
            for piece in splitter.split_text(para):
                if not piece or not piece.strip():
                    continue
                out.append(
                    {
                        "text": piece.strip(),
                        "page_no": page_no,
                        "section": section_path,
                    }
                )
    else:
        # Fallback: word-based per-paragraph chunks
        for para in paragraphs:
            if not para or not para.strip():
                continue
            for piece in _fallback_word_chunks(para, max_tokens=max_tokens, overlap_ratio=overlap_ratio):
                if not piece or not piece.strip():
                    continue
                out.append(
                    {
                        "text": piece.strip(),
                        "page_no": page_no,
                        "section": section_path,
                    }
                )

    return out


# Optional: quick self-test when run directly
# if __name__ == "__main__":
#     sample = (
#         "Bluetooth Pairing\n\n"
#         "To pair a device, open Settings > Connectivity on the center display. "
#         "Enable Bluetooth on your phone and select the vehicle from the list. "
#         "Confirm the pairing code matches on both devices.\n\n"
#         "Troubleshooting: If pairing fails, toggle Bluetooth off/on on both devices and retry."
#     )
#     chunks = chunk_text(sample, max_tokens=80, overlap_ratio=0.2, section_path="Connectivity > Bluetooth", page_no=12)
#     for i, ch in enumerate(chunks, 1):
#         print(f"[{i}] ({ch['section']}, p{ch['page_no']}): {ch['text'][:80]}...")
