"""Unit tests for document ingestion and file format handling."""

from __future__ import annotations

from pathlib import Path

import docx
import pypdf
import pytest

from weirdclauses.ingest import (
    ScannedPDFError,
    UnsupportedFormatError,
    ingest_file,
    load_text,
)


def test_ingest_txt_file(tmp_path: Path) -> None:
    """Test loading a plain text file."""
    sample = tmp_path / "agreement.txt"
    sample.write_text("Clause 1. Rent is $1,000.", encoding="utf-8")
    assert ingest_file(sample) == "Clause 1. Rent is $1,000."


def test_ingest_markdown_file(tmp_path: Path) -> None:
    """Test loading a markdown file."""
    sample = tmp_path / "agreement.md"
    sample.write_text("# Rental Agreement\n\nTerm: 12 months.", encoding="utf-8")
    assert "# Rental Agreement" in ingest_file(sample)


def test_ingest_docx_file(tmp_path: Path) -> None:
    """Test loading a .docx file created with python-docx."""
    docx_path = tmp_path / "agreement.docx"
    doc = docx.Document()
    doc.add_paragraph("RESIDENTIAL LEASE")
    doc.add_paragraph("Clause 1. Base rent is $1,500.")
    doc.save(docx_path)

    loaded = ingest_file(docx_path)
    assert "RESIDENTIAL LEASE" in loaded
    assert "Clause 1. Base rent is $1,500." in loaded


def test_ingest_text_pdf(tmp_path: Path) -> None:
    """Test loading a valid text-based PDF using pypdf."""
    pdf_path = tmp_path / "agreement.pdf"
    # Valid minimal PDF structure with embedded text stream
    pdf_data = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length 78>>stream\n"
        b"BT\n/F1 12 Tf\n100 700 Td\n(Standard Residential Lease Agreement Clause One) Tj\nET\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n"
        b"0000000212 00000 n \n0000000281 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n410\n%%EOF"
    )
    pdf_path.write_bytes(pdf_data)

    extracted = ingest_file(pdf_path)
    assert "Standard Residential Lease Agreement Clause One" in extracted


def test_scanned_pdf_error_on_blank_pdf(tmp_path: Path) -> None:
    """Test that a PDF with insufficient text raises ScannedPDFError with clear message."""
    pdf_path = tmp_path / "scanned_doc.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=300, height=300)
    with open(pdf_path, "wb") as f:
        writer.write(f)

    with pytest.raises(ScannedPDFError) as exc_info:
        ingest_file(pdf_path)

    msg = str(exc_info.value)
    assert "insufficient extractable text" in msg
    assert "scanned image" in msg
    assert "OCR is out of scope" in msg


def test_unsupported_format_raises_error(tmp_path: Path) -> None:
    """Test that unsupported extensions raise UnsupportedFormatError."""
    dummy = tmp_path / "contract.bin"
    dummy.write_text("random content", encoding="utf-8")
    with pytest.raises(UnsupportedFormatError) as exc_info:
        ingest_file(dummy)
    assert "Unsupported file format '.bin'" in str(exc_info.value)


def test_missing_file_raises_not_found() -> None:
    """Test that nonexistent file path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        ingest_file(Path("/nonexistent/file.txt"))


def test_load_text_fallback() -> None:
    """Test load_text returns raw text if given raw string."""
    raw = "1. Simple clause without a file."
    assert load_text(raw) == raw
