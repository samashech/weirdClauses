"""Unit tests for standard baseline pack, embeddings, and conditional surprisal scoring."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from weirdclauses.baseline import (
    BaselineMatch,
    BaselinePack,
    FakeBaselinePack,
)
from weirdclauses.cli import app
from weirdclauses.fake_lm import FakeLM
from weirdclauses.lm import CausalLMScorer
from weirdclauses.scoring import build_conditional_prompt, score_clauses
from weirdclauses.segment import segment_clauses

BASELINE_DIR = Path(__file__).parent.parent / "baseline_packs" / "rental"
SAMPLES_DIR = Path(__file__).parent.parent / "samples"


def test_baseline_pack_loading() -> None:
    """Verify loading standard rental baseline pack files and metadata."""
    pack = FakeBaselinePack(pack_dir=BASELINE_DIR)
    pack.load()
    assert len(pack.clauses) >= 60

    topics = {c.topic for c in pack.clauses}
    assert "rent" in topics
    assert "deposit" in topics
    assert "repairs" in topics
    assert "termination" in topics
    assert "utilities" in topics

    for c in pack.clauses:
        assert c.title
        assert len(c.text.strip()) > 20
        assert c.synthetic is True
        assert c.jurisdiction == "generic-synthetic"


def test_fake_embedder_retrieval() -> None:
    """Verify mock retrieval using word overlap similarity."""
    pack = FakeBaselinePack(pack_dir=BASELINE_DIR)
    matches = pack.retrieve_nearest("The tenant must pay rent on the first day of each month", k=3)
    assert len(matches) == 3
    assert all(isinstance(m, BaselineMatch) for m in matches)
    assert any("rent" in m.clause.topic for m in matches)
    assert matches[0].similarity >= matches[1].similarity


def test_context_budget_truncation() -> None:
    """Verify build_conditional_prompt truncates neighbours to fit budget."""
    pack = FakeBaselinePack(pack_dir=BASELINE_DIR)
    matches = pack.retrieve_nearest("Tenant rent obligation", k=3)
    clause_text = "Tenant agrees to pay $1,500 monthly."

    prompt, c_start = build_conditional_prompt(clause_text, matches, max_neighbour_chars=150)
    assert "Standard clauses of this type:" in prompt
    assert "Clause under review:" in prompt
    assert prompt[c_start:] == clause_text
    assert len(prompt) < 400


def test_conditional_scoring_with_fake_lm() -> None:
    """Verify conditional scoring attaches nearest matches, similarity, and gain."""
    text = (
        "1. RENT\n"
        "The Tenant agrees to pay base rent on the first day of each month.\n\n"
        "2. ACCORDION\n"
        "The Tenant must practice polka accordion at midnight.\n"
    )
    clauses = segment_clauses(text)
    engine = FakeLM()
    pack = FakeBaselinePack(pack_dir=BASELINE_DIR)
    tokens = engine.token_surprisals(text)

    scored = score_clauses(
        clauses,
        tokens,
        mode="conditional",
        baseline_pack=pack,
        engine=engine,
    )

    assert len(scored) == 2
    for sc in scored:
        assert len(sc.nearest_matches) == 3
        assert sc.nearest_similarity is not None
        assert sc.conditional_surprisal is not None
        assert sc.raw_surprisal is not None
        assert sc.gain is not None


def test_verbatim_vs_unusual_conditional_scoring_acceptance() -> None:
    """Acceptance: a verbatim copy of a baseline clause scores lower than an unusual version."""
    pack = FakeBaselinePack(pack_dir=BASELINE_DIR)
    pack.load()
    engine = FakeLM()

    verbatim_text = pack.clauses[0].text
    unusual_text = (
        "The Tenant covenants to play loud nocturnal acoustic accordion "
        "and harmonize psychic building energy on alternate full moon cycles."
    )

    doc = f"1. STANDARD\n{verbatim_text}\n\n2. UNUSUAL\n{unusual_text}\n"
    clauses = segment_clauses(doc)
    tokens = engine.token_surprisals(doc)

    scored = score_clauses(
        clauses,
        tokens,
        mode="conditional",
        baseline_pack=pack,
        engine=engine,
    )

    # Scored clauses sorted by weirdness descending: unusual must be first (#1)
    assert scored[0].clause.content == unusual_text
    assert scored[1].clause.content == verbatim_text
    assert scored[1].score < scored[0].score


@pytest.mark.slow
def test_real_baseline_pack_and_embeddings(tmp_path: Path) -> None:
    """Verify sentence-transformers encoding and caching with real model on CPU."""
    pack = BaselinePack(pack_dir=BASELINE_DIR)
    pack.load()
    assert len(pack.clauses) >= 60

    embs = pack._ensure_embeddings()
    assert isinstance(embs, np.ndarray)
    assert embs.shape[0] == len(pack.clauses)
    assert embs.shape[1] == 384

    # Verify cosine normalization (norm == 1.0)
    norms = np.linalg.norm(embs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)

    matches = pack.retrieve_nearest("Late fee of $50 for rent delinquent after 5 days", k=3)
    assert len(matches) == 3
    assert any("late" in m.clause.topic or "rent" in m.clause.topic for m in matches)


@pytest.mark.slow
def test_verbatim_vs_unusual_real_causal_lm() -> None:
    """Verify acceptance criterion with real open-weight causal LM on CPU."""
    pack = BaselinePack(pack_dir=BASELINE_DIR)
    pack.load()
    scorer = CausalLMScorer()

    verbatim_text = (
        "The Tenant agrees to pay the Landlord a fixed base rent in advance on or before the first "
        "calendar day of each month during the term, without prior demand or setoff."
    )
    unusual_text = (
        "The Tenant covenants and agrees to practice the acoustic polka accordion in the kitchen "
        "between 1:30 AM and 3:00 AM every Tuesday morning to harmonize the atmospheric energy."
    )

    doc = f"1. STANDARD\n{verbatim_text}\n\n2. UNUSUAL\n{unusual_text}\n"
    clauses = segment_clauses(doc)
    tokens = scorer.token_surprisals(doc)

    scored = score_clauses(
        clauses,
        tokens,
        aggregator="topq",
        mode="conditional",
        baseline_pack=pack,
        engine=scorer,
    )

    assert scored[0].clause.content == unusual_text
    assert scored[1].clause.content == verbatim_text
    # Verbatim baseline clause scores lower than unusual rewritten clause
    assert scored[1].score < scored[0].score


def test_cli_scoring_modes(cli_runner: CliRunner) -> None:
    """Verify CLI accepts --mode raw and --mode conditional."""
    sample = str(SAMPLES_DIR / "unusual_rental.txt")

    res_raw = cli_runner.invoke(
        app, ["score", sample, "--mock", "--mode", "raw", "--top", "3"], env={"COLUMNS": "160"}
    )
    assert res_raw.exit_code == 0
    assert "Mode: raw" in res_raw.stdout

    args_cond = ["score", sample, "--mock", "--mode", "conditional", "--top", "3"]
    res_cond = cli_runner.invoke(app, args_cond, env={"COLUMNS": "160"})
    assert res_cond.exit_code == 0
    assert "Mode: conditional" in res_cond.stdout
    assert "Gain" in res_cond.stdout
