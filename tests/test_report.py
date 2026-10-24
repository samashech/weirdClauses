"""Unit and acceptance tests for report generation, validation, and exporters."""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from weirdclauses import LEGAL_DISCLAIMER
from weirdclauses.cli import app
from weirdclauses.pipeline import run_pipeline
from weirdclauses.report import (
    build_report,
    export_html,
    export_json,
    export_markdown,
    validate_report,
)
from weirdclauses.report_html import _render_tokens_heat_map

runner = CliRunner()


def test_report_schema_validation(samples_dir: Path) -> None:
    """Report dictionary must strictly validate against docs/report.schema.json."""
    sample_path = samples_dir / "normal_rental.txt"
    res = run_pipeline(sample_path, mock=True)
    report = build_report(
        raw_text=res.text,
        clauses=res.clauses,
        scored_clauses=res.scored_clauses,
        facts_by_clause=res.facts_by_clause,
        file_path=sample_path,
        lm_model="mock-lm",
        embed_model="mock-embed",
        device="cpu",
        mode=res.mode,
        aggregator=res.aggregator,
    )

    # Validate against JSON schema
    validate_report(report)
    assert report["version"] == "0.1.0"
    assert report["disclaimer"] == LEGAL_DISCLAIMER
    assert len(report["clauses"]) == len(res.clauses)
    assert len(report["key_facts"]) > 0


def test_html_report_self_contained_and_offline(samples_dir: Path, tmp_path: Path) -> None:
    """HTML report must have zero external web requests, support dark mode, and open offline."""
    sample_path = samples_dir / "normal_rental.txt"
    res = run_pipeline(sample_path, mock=True)
    report = build_report(
        raw_text=res.text,
        clauses=res.clauses,
        scored_clauses=res.scored_clauses,
        facts_by_clause=res.facts_by_clause,
        file_path=sample_path,
    )

    out_file = tmp_path / "report.html"
    html_content = export_html(report, path=out_file)
    assert out_file.exists()
    assert len(html_content) > 1000

    # No external stylesheet or script references
    assert '<link rel="stylesheet" href="http' not in html_content
    assert '<script src="http' not in html_content
    assert "googleapis" not in html_content
    assert "cdn" not in html_content

    # Light and dark mode support present
    assert "data-theme" in html_content
    assert "prefers-color-scheme" in html_content
    assert "toggleTheme" in html_content

    # Prominent disclaimer present
    assert LEGAL_DISCLAIMER in html_content
    assert "rule-based" in html_content


def test_character_accurate_token_highlights() -> None:
    """Stripping HTML tags from heat-mapped output must reproduce clause text exactly."""
    clause_dict = {
        "id": 1,
        "text": "The Tenant agrees to pay a monthly base rent of $1,650.00 on the first.",
        "start": 100,
        "end": 171,
        "kind": "clause",
        "tokens": [
            {"start": 100, "end": 103, "bits": 4.5},
            {"start": 104, "end": 110, "bits": 6.2},
            {"start": 111, "end": 117, "bits": 5.1},
            {"start": 148, "end": 157, "bits": 8.9},
        ],
        "facts": [
            {
                "kind": "money",
                "value": "$1,650.00",
                "start": 148,
                "end": 157,
                "source_label": "rule-based",
            }
        ],
    }

    rendered_html = _render_tokens_heat_map(clause_dict)
    # Strip HTML tags
    clean_text = re.sub(r"<[^>]+>", "", rendered_html)
    # Must match original text exactly without loss or offset shifts
    assert clean_text == clause_dict["text"]


def test_markdown_and_json_exporters(samples_dir: Path, tmp_path: Path) -> None:
    """Markdown and JSON reports generate cleanly with metadata and disclaimer."""
    sample_path = samples_dir / "normal_rental.txt"
    res = run_pipeline(sample_path, mock=True)
    report = build_report(
        raw_text=res.text,
        clauses=res.clauses,
        scored_clauses=res.scored_clauses,
        facts_by_clause=res.facts_by_clause,
        file_path=sample_path,
    )

    md_path = tmp_path / "report.md"
    md_content = export_markdown(report, path=md_path)
    assert md_path.exists()
    assert "# WeirdClauses Analysis Report" in md_content
    assert "Key Facts (Rule-Based Extraction)" in md_content
    assert LEGAL_DISCLAIMER in md_content

    json_path = tmp_path / "report.json"
    json_content = export_json(report, path=json_path)
    assert json_path.exists()
    parsed = json.loads(json_content)
    assert parsed["summary"]["scored_clauses"] == len(res.scored_clauses)


def test_snapshot_acceptance_on_unusual_sample(samples_dir: Path) -> None:
    """Snapshot acceptance test verifying ranking and fact extraction on unusual sample."""
    sample_path = samples_dir / "unusual_rental.txt"
    res = run_pipeline(sample_path, mock=True)
    report = build_report(
        raw_text=res.text,
        clauses=res.clauses,
        scored_clauses=res.scored_clauses,
        facts_by_clause=res.facts_by_clause,
        file_path=sample_path,
    )

    validate_report(report)

    # Unusual clauses must be ranked at the top
    top_ranks = [c for c in report["clauses"] if c.get("rank") in (1, 2, 3)]
    assert len(top_ranks) == 3
    top_headings = [c.get("parent_heading") or "" for c in top_ranks]
    assert any("ACCORDION" in h or "FELINE" in h or "THERMODYNAMIC" in h for h in top_headings)

    # Key facts must include money and percentage
    fact_kinds = {f["kind"] for f in report["key_facts"]}
    assert "money" in fact_kinds
    assert "percentage" in fact_kinds
    assert all(f["source_label"] == "rule-based" for f in report["key_facts"])


def test_cli_review_command(samples_dir: Path, tmp_path: Path) -> None:
    """CLI 'weirdclauses review' runs end-to-end and creates report file."""
    sample_path = samples_dir / "normal_rental.txt"
    html_out = tmp_path / "output_report.html"

    result = runner.invoke(
        app,
        ["review", str(sample_path), "--out", str(html_out), "--top", "10%", "--mock"],
        env={"COLUMNS": "160"},
    )
    assert result.exit_code == 0
    assert html_out.exists()
    assert "Analysis complete" in result.stdout
    assert "Top Unusual Clauses" in result.stdout
    assert "NOT legal advice" in result.stdout
    assert "attorney" in result.stdout.lower()
