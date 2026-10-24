"""Document ingestion module supporting .txt, .md, .docx, and text-based .pdf."""

from __future__ import annotations

from pathlib import Path


class IngestError(Exception):
    """Base exception for document ingestion errors."""


class ScannedPDFError(IngestError):
    """Raised when a PDF contains insufficient extractable text (likely a scan)."""


class UnsupportedFormatError(IngestError):
    """Raised when a file extension is not supported."""


def ingest_file(path: str | Path) -> str:
    """Ingest agreement text from a supported file path.

    Supports .txt, .md, .docx, and text-based .pdf files.
    Detects scanned PDFs with insufficient text and raises ScannedPDFError.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix in (".txt", ".md"):
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="latin-1")

    if suffix == ".docx":
        import docx

        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    if suffix == ".pdf":
        import pypdf

        reader = pypdf.PdfReader(file_path)
        pages_text: list[str] = []
        total_chars = 0
        num_pages = len(reader.pages)

        for page in reader.pages:
            raw_text = page.extract_text() or ""
            cleaned = raw_text.strip()
            total_chars += len(cleaned)
            if cleaned:
                pages_text.append(cleaned)

        # Scanned PDF check: insufficient extractable text
        if num_pages > 0 and (total_chars < 40 or (total_chars / num_pages < 20)):
            raise ScannedPDFError(
                f"PDF '{file_path}' contains insufficient extractable text "
                f"({total_chars} characters across {num_pages} pages). "
                "The document appears to be a scanned image. OCR is out of scope for WeirdClauses."
            )

        return "\n\n".join(pages_text)

    raise UnsupportedFormatError(
        f"Unsupported file format '{suffix}'. Supported formats are: .txt, .md, .docx, .pdf"
    )


def load_text(path_or_str: str | Path) -> str:
    """Load text content from a file path or raw string."""
    candidate = Path(path_or_str)
    if candidate.is_file():
        return ingest_file(candidate)
    return str(path_or_str)
