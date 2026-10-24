"""Unit tests for rule-based key facts extraction."""

from __future__ import annotations

from weirdclauses.facts import FactExtractor, attach_facts_to_clauses, extract_facts
from weirdclauses.segment import segment_clauses


def test_money_extraction() -> None:
    text = (
        "The monthly rent is $1,650.00 and deposit is $500, plus a late charge of 50 euros or £25."
    )
    facts = extract_facts(text)
    money_facts = [f for f in facts if f.kind == "money"]
    assert len(money_facts) >= 3
    values = [f.value for f in money_facts]
    assert "$1,650.00" in values
    assert "$500" in values
    # Verify character accuracy
    for f in money_facts:
        assert text[f.start : f.end] == f.value
        assert f.source_label == "rule-based"


def test_percent_extraction() -> None:
    text = (
        "A late fee of 5% applies after the due date, "
        "and twenty percent of deposit is non-refundable."
    )
    facts = extract_facts(text)
    pct_facts = [f for f in facts if f.kind == "percentage"]
    values = [f.value for f in pct_facts]
    assert "5%" in values
    assert "twenty percent" in values
    for f in pct_facts:
        assert text[f.start : f.end] == f.value
        assert f.source_label == "rule-based"


def test_date_extraction() -> None:
    text = (
        "Agreement dated October 1, 2026. Lease term commences on 2027-01-15 until August 31, 2027."
    )
    facts = extract_facts(text)
    date_facts = [f for f in facts if f.kind == "date"]
    values = [f.value for f in date_facts]
    assert "October 1, 2026" in values
    assert "2027-01-15" in values
    assert "August 31, 2027" in values
    for f in date_facts:
        assert text[f.start : f.end] == f.value


def test_notice_period_and_duration_no_subspan_overlap() -> None:
    text = (
        "Tenant must give at least 30 days written notice. "
        "Landlord requires 24 hours prior written notice. "
        "The lease has a term of 12 months."
    )
    facts = extract_facts(text)
    notices = [f for f in facts if f.kind == "notice_period"]
    durations = [f for f in facts if f.kind == "duration"]

    assert len(notices) == 2
    assert any("30 days" in n.value for n in notices)
    assert any("24 hours" in n.value for n in notices)

    # Durations should not overlap the notice spans
    assert len(durations) == 1
    assert "12 months" in durations[0].value

    for f in facts:
        assert text[f.start : f.end] == f.value


def test_auto_renewal_extraction() -> None:
    text = (
        "This Agreement shall automatically renew for successive terms of one year "
        "unless either party provides notice, and shall continue on a month-to-month basis."
    )
    facts = extract_facts(text)
    auto_renewals = [f for f in facts if f.kind == "auto_renewal"]
    assert len(auto_renewals) >= 1
    values = [f.value.lower() for f in auto_renewals]
    assert any("automatically renew" in v or "month-to-month" in v for v in values)
    for f in auto_renewals:
        assert text[f.start : f.end] == f.value
        assert f.source_label == "rule-based"


def test_attach_facts_to_clauses_accuracy() -> None:
    raw_doc = (
        "1. LEASE TERM\n"
        "The lease begins on September 1, 2026 and continues for twelve calendar months.\n\n"
        "2. RENT\n"
        "Monthly rent is $1,500.00 due on the first, subject to a late fee of 5%.\n"
    )
    clauses = segment_clauses(raw_doc)
    facts_by_clause = attach_facts_to_clauses(clauses)

    all_facts = [f for f_list in facts_by_clause.values() for f in f_list]
    assert len(all_facts) >= 4

    # Every fact's start and end must match raw_doc exactly
    for f in all_facts:
        assert raw_doc[f.start : f.end] == f.value
        assert f.source_label == "rule-based"


def test_fact_extractor_class_methods() -> None:
    extractor = FactExtractor()
    sample = "Rent: $1,200.00; Late fee: 10%; Term: 1 year."
    results = extractor.extract(sample, base_offset=100)
    assert len(results) == 3
    assert results[0].start >= 100
    assert results[0].source_label == "rule-based"
