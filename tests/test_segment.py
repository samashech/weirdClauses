"""Unit tests for clause segmentation and lossless span partitioning."""

from __future__ import annotations

from pathlib import Path

from weirdclauses.segment import Clause, segment_clauses

SAMPLES_DIR = Path(__file__).parent.parent / "samples"


def _verify_lossless_partition(text: str, clauses: list[Clause]) -> None:
    """Helper verifying that clauses partition text with zero gaps and zero overlaps."""
    assert len(clauses) > 0, "Segmentation produced no clauses"
    assert clauses[0].start == 0, f"First clause start is {clauses[0].start}, expected 0"
    assert clauses[-1].end == len(text), (
        f"Last clause end is {clauses[-1].end}, expected {len(text)}"
    )

    for i in range(len(clauses) - 1):
        curr, nxt = clauses[i], clauses[i + 1]
        assert curr.end == nxt.start, (
            f"Gap or overlap at clause {curr.id} -> {nxt.id}: "
            f"curr.end={curr.end}, nxt.start={nxt.start}"
        )
        assert text[curr.start : curr.end] == curr.text, (
            f"Clause {curr.id} text does not match span slice"
        )

    assert text[clauses[-1].start : clauses[-1].end] == clauses[-1].text
    reconstructed = "".join(c.text for c in clauses)
    assert reconstructed == text, "Concatenating clauses failed to reproduce document"


def test_segment_normal_rental_sample() -> None:
    """Verify segmentation on standard residential lease sample."""
    path = SAMPLES_DIR / "normal_rental.txt"
    text = path.read_text(encoding="utf-8")
    clauses = segment_clauses(text)

    _verify_lossless_partition(text, clauses)

    kinds = [c.kind for c in clauses]
    assert "frame" in kinds, "Expected title/signature frame"
    assert "heading" in kinds, "Expected headings"
    assert "clause" in kinds, "Expected substantive clauses"

    # Check parent headings are assigned to clauses
    scored_clauses = [c for c in clauses if c.kind == "clause"]
    assert any(c.parent_heading is not None for c in scored_clauses)


def test_segment_unusual_rental_sample() -> None:
    """Verify segmentation on lease with weird clauses."""
    path = SAMPLES_DIR / "unusual_rental.txt"
    text = path.read_text(encoding="utf-8")
    clauses = segment_clauses(text)

    _verify_lossless_partition(text, clauses)

    # Check accordion clause is captured
    clause_texts = [c.text for c in clauses]
    assert any("nocturnal accordion" in t.lower() or "polka" in t.lower() for t in clause_texts)
    assert any("feline" in t.lower() for t in clause_texts)


def test_segment_messy_numbering_sample() -> None:
    """Verify segmentation on messy numbering layout (Sections, Articles, Roman numerals)."""
    path = SAMPLES_DIR / "messy_numbering_rental.txt"
    text = path.read_text(encoding="utf-8")
    clauses = segment_clauses(text)

    _verify_lossless_partition(text, clauses)

    clause_texts = [c.text for c in clauses]
    assert any(
        "Article II" in (c.parent_heading or "") or "Financial" in (c.parent_heading or "")
        for c in clauses
    )
    assert any("3.1.2" in t or "utility" in t.lower() for t in clause_texts)


def test_segment_pure_unnumbered_layout() -> None:
    """Verify segmentation fallback on purely unnumbered paragraphs."""
    doc = (
        "RESIDENTIAL LEASE AGREEMENT\n\n"
        "This Agreement is entered into between Landlord Jane Doe and Tenant Alex Mercer.\n\n"
        "The Tenant agrees to pay base rent of $1,200 per calendar month on the first day.\n\n"
        "The Tenant shall keep the leased dwelling in a clean, habitable, and "
        "sanitary condition.\n\n"
        "The Landlord shall perform necessary structural repairs within thirty days of notice.\n\n"
        "IN WITNESS WHEREOF, the parties sign below:\n"
        "Landlord: ____________\n"
        "Tenant: ____________\n"
    )
    clauses = segment_clauses(doc)
    _verify_lossless_partition(doc, clauses)

    # Scored clauses should exist
    scored = [c for c in clauses if c.kind == "clause"]
    assert len(scored) >= 3


def test_segment_lettered_clauses() -> None:
    """Verify segmentation of lettered sub-clauses (a), (b), (c)."""
    doc = (
        "SECTION 1: RULES\n\n"
        "(a) No loud music after 10 PM on weekdays or midnight on weekends.\n"
        "(b) Recycling and trash must be placed in appropriate sorting bins.\n"
        "(c) Subletting requires prior written authorization from the owner.\n"
    )
    clauses = segment_clauses(doc)
    _verify_lossless_partition(doc, clauses)


def test_fragment_merging() -> None:
    """Verify that fragments under ~12 tokens merge into adjacent clauses."""
    doc = (
        "1. MAINTENANCE\n\n"
        "The Tenant shall keep the entire interior of the premises clean and sanitary.\n"
        "No pets.\n"
    )
    clauses = segment_clauses(doc, min_tokens=12)
    _verify_lossless_partition(doc, clauses)

    # 'No pets.' has only 2 tokens, so merges into the previous clause under '1. MAINTENANCE'
    body_clauses = [c for c in clauses if c.kind == "clause"]
    assert len(body_clauses) == 1
    assert "No pets." in body_clauses[0].text
