"""
parser.py
---------
Extract raw text from PDF and DOCX resume files.

Supported formats:
    - **.pdf**  — extracted via `PyMuPDF` (``fitz``)
    - **.docx** — extracted via `python-docx`

The public entry point is :func:`extract_text`, which dispatches
automatically based on the file extension.
"""

from pathlib import Path

import fitz                       # PyMuPDF
from docx import Document         # python-docx


# ── PDF ───────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(path: str | Path) -> str:
    """
    Extract all text from a PDF file.

    Parameters
    ----------
    path : str | Path
        Path to the PDF file.

    Returns
    -------
    str
        Concatenated text from every page, separated by newlines.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file is not a valid PDF or cannot be opened.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise ValueError(f"Could not open PDF '{path}': {exc}") from exc

    pages: list[str] = []
    for page in doc:
        text = page.get_text("text")
        if text:
            pages.append(text.strip())
    doc.close()

    return "\n".join(pages)


# ── DOCX ──────────────────────────────────────────────────────────────────────

def extract_text_from_docx(path: str | Path) -> str:
    """
    Extract all text from a DOCX file.

    Parameters
    ----------
    path : str | Path
        Path to the DOCX file.

    Returns
    -------
    str
        Concatenated paragraph text, separated by newlines.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ValueError
        If the file cannot be parsed as DOCX.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")

    try:
        doc = Document(str(path))
    except Exception as exc:
        raise ValueError(f"Could not open DOCX '{path}': {exc}") from exc

    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


# ── Dispatcher ────────────────────────────────────────────────────────────────

_EXTRACTORS = {
    ".pdf":  extract_text_from_pdf,
    ".docx": extract_text_from_docx,
}


def extract_text(path: str | Path) -> str:
    """
    Extract text from a resume file (PDF or DOCX).

    Dispatches to the appropriate extractor based on the file extension.

    Parameters
    ----------
    path : str | Path
        Path to the resume file.

    Returns
    -------
    str
        Extracted raw text.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    """
    path = Path(path)
    ext = path.suffix.lower()

    extractor = _EXTRACTORS.get(ext)
    if extractor is None:
        supported = ", ".join(sorted(_EXTRACTORS.keys()))
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported: {supported}"
        )

    return extractor(path)
