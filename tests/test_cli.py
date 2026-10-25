"""CLI and bootstrap verification tests."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from weirdclauses import LEGAL_DISCLAIMER, __version__
from weirdclauses.cli import app
from weirdclauses.facts import FactExtractor
from weirdclauses.report import format_text_report
from weirdclauses.scoring import (
    aggregate_max,
    aggregate_mean,
    aggregate_top_quartile_mean,
    z_normalize,
)


def _strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from terminal output."""
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)


def test_cli_version(cli_runner: CliRunner) -> None:
    """Verify --version returns package version and legal disclaimer."""
    result = cli_runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    clean = _strip_ansi(result.stdout)
    assert __version__ in clean
    assert "NOT legal advice" in clean


def test_cli_doctor(cli_runner: CliRunner) -> None:
    """Verify weirdclauses doctor runs offline, checks system, and exits 0."""
    result = cli_runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    clean = _strip_ansi(result.stdout)
    assert "Legal Disclaimer" in clean
    assert "Python Version" in clean
    assert "PyTorch" in clean
    assert "Cache Directory" in clean
    assert "System is ready" in clean


def test_cli_doctor_mock(cli_runner: CliRunner) -> None:
    """Verify weirdclauses doctor --mock indicates mock mode enabled."""
    result = cli_runner.invoke(app, ["doctor", "--mock"])
    assert result.exit_code == 0
    clean = _strip_ansi(result.stdout)
    assert "Mock Mode" in clean
    assert "ENABLED" in clean
    assert "System is ready" in clean


def test_legal_disclaimer_constant() -> None:
    """Ensure the legal disclaimer is explicitly formulated."""
    assert "NOT legal advice" in LEGAL_DISCLAIMER
    assert "attorney" in LEGAL_DISCLAIMER.lower()


def test_scoring_aggregations() -> None:
    """Test basic math of mean, max, top-quartile, and z-norm."""
    vals = [1.0, 2.0, 3.0, 4.0]
    assert aggregate_mean(vals) == 2.5
    assert aggregate_max(vals) == 4.0
    # 25% of 4 is top 1 element -> 4.0
    assert aggregate_top_quartile_mean(vals) == 4.0

    zn = z_normalize(vals)
    assert len(zn) == 4
    # Mean of z-normalized values should be ~0
    assert abs(sum(zn)) < 1e-6


def test_fact_extraction() -> None:
    """Test rule-based fact extractor on rental terms."""
    extractor = FactExtractor()
    sample = "Rent is $1,500 due on 1st. Late fee is 5%. Tenant must give 30 days notice."
    facts = extractor.extract(sample)
    types = [f.fact_type for f in facts]
    assert "money" in types
    assert "percentage" in types
    assert "notice_period" in types
    assert all(f.source_label == "rule-based" for f in facts)


def test_report_includes_disclaimer() -> None:
    """Test report output explicitly contains legal disclaimer."""
    report = format_text_report([], [])
    assert LEGAL_DISCLAIMER in report
