"""Unit tests for Phase 6 benchmark generation, baselines, and evaluation metrics."""

from __future__ import annotations

import random
from pathlib import Path

from eval.baselines import (
    TFIDFBaselineRanker,
    get_clause_ranks_from_scores,
    score_by_heuristic,
    score_by_length,
)
from eval.chart import generate_benchmark_svg
from eval.make_benchmark import (
    build_agreement,
    generate_benchmark,
    load_pool_data,
)
from eval.metrics import (
    EvaluationReport,
    bootstrap_metric,
    compute_mean_percentile_rank,
    compute_percentile_rank,
    compute_recall_at_pct,
    compute_reciprocal_rank,
    evaluate_document_runs,
)


def test_load_pool_data_and_structure() -> None:
    """Pool datasets must load valid held-out standards and planted unusual clauses."""
    standards, unusual = load_pool_data()
    assert len(standards) >= 30
    assert len(unusual) >= 20
    assert all("id" in s and "text" in s for s in standards)
    assert all("id" in u and "text" in u and "category" in u for u in unusual)


def test_build_agreement_reproducibility() -> None:
    """Agreement generation with fixed seed must be 100% deterministic."""
    standards, unusual = load_pool_data()
    rng1 = random.Random(999)
    rng2 = random.Random(999)

    doc1 = build_agreement(0, rng1, standards, unusual)
    doc2 = build_agreement(0, rng2, standards, unusual)

    assert doc1.text == doc2.text
    assert len(doc1.clauses) == len(doc2.clauses)
    assert doc1.num_planted_clauses == doc2.num_planted_clauses
    assert 2 <= doc1.num_planted_clauses <= 4
    assert any(c.is_planted for c in doc1.clauses)
    assert any(not c.is_planted for c in doc1.clauses)


def test_generate_benchmark_sample(tmp_path: Path) -> None:
    """generate_benchmark writes valid json and preserves ground truth."""
    out_file = tmp_path / "test_benchmark.json"
    docs = generate_benchmark(count=3, seed=123, output_path=out_file)
    assert len(docs) == 3
    assert out_file.exists()


def test_baseline_rankers() -> None:
    """Verify non-LM baseline rankers assign expected score distributions."""
    clauses = [
        {"text": "Short normal standard clause."},
        {"text": "Extremely long clause that describes normal maintenance duties in high detail."},
        {"text": "Tenant shall incur a $500 penalty and forfeit all rights to jury trial."},
    ]

    # Length ranker
    len_scores = score_by_length(clauses)
    assert len_scores[1] > len_scores[0]

    # Heuristic ranker
    heur_scores = score_by_heuristic(clauses)
    assert heur_scores[2] > heur_scores[0]
    assert heur_scores[2] > heur_scores[1]

    # TF-IDF ranker
    tfidf_ranker = TFIDFBaselineRanker(baseline_texts=["Short normal standard clause."])
    tfidf_scores = tfidf_ranker.score_document(clauses)
    assert len(tfidf_scores) == 3
    # Clause 0 is identical to baseline so distance should be near 0
    assert tfidf_scores[0] < tfidf_scores[2]

    # Rank conversion
    scores = [10.0, 50.0, 20.0]
    ranks = get_clause_ranks_from_scores(scores)
    assert ranks == [3, 1, 2]  # Index 1 has score 50.0 -> rank 1


def test_metrics_calculations() -> None:
    """Verify recall@pct, percentile rank, and MRR calculations."""
    # 10 clauses, planted at rank 1 and rank 5
    ranks = [1, 5]
    total_clauses = 10

    # Recall at 10%: cutoff is ceil(10 * 0.10) = 1. Only rank 1 is <= 1 -> 1 / 2 = 0.50
    assert compute_recall_at_pct(ranks, total_clauses, pct=0.10) == 0.50

    # Percentile ranks:
    # rank 1 out of 10: (10 - 1) / 9 = 1.0
    # rank 5 out of 10: (10 - 5) / 9 = 5 / 9 = 0.5555...
    assert compute_percentile_rank(1, 10) == 1.0
    assert compute_percentile_rank(10, 10) == 0.0
    mean_pct = compute_mean_percentile_rank(ranks, total_clauses)
    assert abs(mean_pct - ((1.0 + (5 / 9)) / 2)) < 1e-4

    # MRR: first planted clause is at rank 1 -> 1 / 1 = 1.0
    assert compute_reciprocal_rank(ranks) == 1.0
    assert compute_reciprocal_rank([3, 7]) == 1.0 / 3.0


def test_bootstrap_metric() -> None:
    """Bootstrap CI must bracket the empirical mean."""
    values = [0.2, 0.4, 0.6, 0.8, 1.0]
    summary = bootstrap_metric(values, n_bootstraps=500, ci=0.95, seed=42)
    assert summary.mean == 0.6
    assert summary.ci_lower <= summary.mean <= summary.ci_upper
    assert "0.600" in summary.format_ci()


def test_evaluate_document_runs_and_chart(tmp_path: Path) -> None:
    """evaluate_document_runs produces valid report and SVG chart renders correctly."""
    runs = [
        {"doc_id": "doc1", "total_clauses": 10, "ranks": [1, 2]},
        {"doc_id": "doc2", "total_clauses": 10, "ranks": [2, 4]},
    ]
    report = evaluate_document_runs("TestRanker", runs, n_bootstraps=100)
    assert isinstance(report, EvaluationReport)
    assert report.ranker_name == "TestRanker"
    assert report.num_documents == 2

    # Chart generation
    chart_path = tmp_path / "test_chart.svg"
    generate_benchmark_svg([report], chart_path)
    assert chart_path.exists()
    svg_text = chart_path.read_text(encoding="utf-8")
    assert "<svg" in svg_text
    assert "</svg>" in svg_text
    assert "TestRanker" in svg_text
