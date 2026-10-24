"""Unit tests for the surprisal engine, cache, aggregators, and window consistency."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from weirdclauses.cache import get_cache_path, get_cached_surprisals, save_cached_surprisals
from weirdclauses.cli import app
from weirdclauses.fake_lm import FakeLM
from weirdclauses.ingest import load_text
from weirdclauses.lm import CausalLMScorer, get_surprisal_engine
from weirdclauses.scoring import score_clauses
from weirdclauses.segment import segment_clauses

SAMPLES_DIR = Path(__file__).parent.parent / "samples"


def test_token_offsets_align_with_clause_spans() -> None:
    """Verify that token offsets map directly into original document characters and clauses."""
    sample_path = SAMPLES_DIR / "normal_rental.txt"
    text = load_text(sample_path)
    clauses = segment_clauses(text)
    lm = FakeLM()
    tokens = lm.token_surprisals(text)

    assert len(tokens) > 0

    for start, end, bits in tokens:
        assert 0 <= start < end <= len(text)
        assert bits > 0.0
        # Token midpoint must fall inside a valid clause
        mid = (start + end) // 2
        matching = [c for c in clauses if c.start <= mid < c.end]
        assert len(matching) == 1
        assert matching[0].text == text[matching[0].start : matching[0].end]


@pytest.mark.slow
def test_window_consistency_long_vs_short(tmp_path: Path) -> None:
    """Verify that sliding window evaluation yields consistent scores for paragraphs."""
    target_clause = "The Tenant shall practice the acoustic polka accordion every Tuesday morning."

    short_doc = f"1. RULES\n{target_clause}\n"
    # Long prefix designed to push the target clause across multiple sliding windows
    long_prefix = "Standard residential rental agreement terms. " * 30
    long_doc = f"{long_prefix}\n2. RULES\n{target_clause}\n"

    scorer = CausalLMScorer(model_name="Qwen/Qwen2.5-0.5B")
    toks_short = scorer.token_surprisals(short_doc, window_size=64)
    toks_long = scorer.token_surprisals(long_doc, window_size=64)

    # Filter tokens in target clause
    short_target_start = short_doc.index(target_clause)
    short_target_end = short_target_start + len(target_clause)
    clause_toks_short = [
        bits for s, e, bits in toks_short if s >= short_target_start and e <= short_target_end
    ]

    long_target_start = long_doc.index(target_clause)
    long_target_end = long_target_start + len(target_clause)
    clause_toks_long = [
        bits for s, e, bits in toks_long if s >= long_target_start and e <= long_target_end
    ]

    assert len(clause_toks_short) > 0
    assert len(clause_toks_long) > 0
    # Overlapping window ensures late tokens match within tolerance
    assert abs(clause_toks_short[-1] - clause_toks_long[-1]) < 2.0


def test_disk_cache_roundtrip(tmp_path: Path) -> None:
    """Verify saving and retrieving token surprisals from disk cache."""
    test_text = "Clause 1. Base rent is $1,200 due on the first."
    model_id = "test-model-v1"
    surprisals = [(0, 6, 3.1234), (7, 9, 2.5678), (10, 14, 4.8912)]

    # Initial state: not cached
    assert get_cached_surprisals(model_id, test_text, cache_root=tmp_path) is None

    # Save to cache
    save_cached_surprisals(model_id, test_text, surprisals, cache_root=tmp_path)

    # Cache file exists
    cache_file = get_cache_path(model_id, test_text, cache_root=tmp_path)
    assert cache_file.is_file()

    # Retrieve from cache
    loaded = get_cached_surprisals(model_id, test_text, cache_root=tmp_path)
    assert loaded is not None
    assert len(loaded) == len(surprisals)
    for (s1, e1, b1), (s2, e2, b2) in zip(surprisals, loaded, strict=True):
        assert s1 == s2
        assert e1 == e2
        assert abs(b1 - b2) < 1e-4


def test_scoring_aggregators_and_z_normalization() -> None:
    """Verify that mean, max, and topq aggregators compute expected scores and z-scores."""
    text = (
        "1. CLAUSE A\n"
        "Tenant pays rent on the first day.\n\n"
        "2. CLAUSE B\n"
        "Tenant plays loud polka accordion at midnight.\n"
    )
    clauses = segment_clauses(text)
    engine = FakeLM()
    tokens = engine.token_surprisals(text)

    for agg in ("mean", "topq", "max"):
        scored = score_clauses(clauses, tokens, aggregator=agg)
        assert len(scored) == 2  # Only the 2 clauses, headings excluded
        # Accordion clause has unusual terms and must rank higher
        assert scored[0].score > scored[1].score
        assert "accordion" in scored[0].clause.text
        # Z-scores should sum to approximately zero
        z_sum = sum(sc.z_score for sc in scored)
        assert abs(z_sum) < 1e-4


def test_cli_score_mock(cli_runner: CliRunner) -> None:
    """Verify weirdclauses score executes in mock mode offline."""
    sample = str(SAMPLES_DIR / "unusual_rental.txt")
    args = ["score", sample, "--mock", "--aggregator", "topq", "--top", "5"]
    result = cli_runner.invoke(app, args)
    assert result.exit_code == 0
    assert "Legal Disclaimer" in result.stdout
    assert "WeirdClauses Ranking" in result.stdout
    assert "FELINE" in result.stdout or "ACCORDION" in result.stdout
    assert "NOT legal advice" in result.stdout


def test_get_surprisal_engine_lazy_loading() -> None:
    """Verify get_surprisal_engine returns FakeLM when mock=True without loading torch."""
    engine = get_surprisal_engine(mock=True)
    assert isinstance(engine, FakeLM)
    surprisals = engine.token_surprisals("Test clause text.")
    assert len(surprisals) > 0
