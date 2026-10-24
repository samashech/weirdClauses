"""Evaluation metrics for benchmark anomaly ranking and confidence intervals."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class MetricSummary:
    """Summary of a metric with mean and 95% bootstrap confidence interval."""

    mean: float
    ci_lower: float
    ci_upper: float

    def to_dict(self) -> dict[str, float]:
        return {
            "mean": round(self.mean, 4),
            "ci_lower": round(self.ci_lower, 4),
            "ci_upper": round(self.ci_upper, 4),
        }

    def format_ci(self) -> str:
        return f"{self.mean:.3f} [{self.ci_lower:.3f}, {self.ci_upper:.3f}]"


@dataclass
class EvaluationReport:
    """Consolidated evaluation metrics for a single ranker across the benchmark."""

    ranker_name: str
    recall_at_10: MetricSummary
    mean_percentile_rank: MetricSummary
    mrr: MetricSummary
    num_documents: int

    def to_dict(self) -> dict[str, object]:
        return {
            "ranker_name": self.ranker_name,
            "recall_at_10": self.recall_at_10.to_dict(),
            "mean_percentile_rank": self.mean_percentile_rank.to_dict(),
            "mrr": self.mrr.to_dict(),
            "num_documents": self.num_documents,
        }


def compute_recall_at_pct(ranks: Sequence[int], total_clauses: int, pct: float = 0.10) -> float:
    """Fraction of planted clauses that appear in the top pct of clauses."""
    if not ranks or total_clauses <= 0:
        return 0.0
    cutoff = max(1, math.ceil(total_clauses * pct))
    hits = sum(1 for r in ranks if r <= cutoff)
    return hits / len(ranks)


def compute_percentile_rank(rank: int, total_clauses: int) -> float:
    """Compute percentile position in ranking (1.0 = top anomalous, 0.0 = bottom)."""
    if total_clauses <= 1:
        return 1.0
    # Clamped to [0.0, 1.0]
    raw = (total_clauses - rank) / (total_clauses - 1)
    return max(0.0, min(1.0, raw))


def compute_mean_percentile_rank(ranks: Sequence[int], total_clauses: int) -> float:
    """Compute average percentile rank of all planted clauses in document."""
    if not ranks:
        return 0.0
    return sum(compute_percentile_rank(r, total_clauses) for r in ranks) / len(ranks)


def compute_reciprocal_rank(ranks: Sequence[int]) -> float:
    """Compute reciprocal rank of the first planted clause encountered."""
    if not ranks:
        return 0.0
    first_rank = min(ranks)
    return 1.0 / first_rank if first_rank > 0 else 0.0


def bootstrap_metric(
    values: Sequence[float],
    n_bootstraps: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> MetricSummary:
    """Compute empirical mean and bootstrap percentile confidence interval."""
    if not values:
        return MetricSummary(0.0, 0.0, 0.0)

    n = len(values)
    rng = random.Random(seed)
    actual_mean = sum(values) / n

    sample_means: list[float] = []
    for _ in range(n_bootstraps):
        resample = [values[rng.randrange(n)] for _ in range(n)]
        sample_means.append(sum(resample) / n)

    sample_means.sort()
    alpha = (1.0 - ci) / 2.0
    lower_idx = int(alpha * n_bootstraps)
    upper_idx = int((1.0 - alpha) * n_bootstraps) - 1

    ci_lower = sample_means[max(0, lower_idx)]
    ci_upper = sample_means[min(n_bootstraps - 1, upper_idx)]

    return MetricSummary(mean=actual_mean, ci_lower=ci_lower, ci_upper=ci_upper)


def evaluate_document_runs(
    ranker_name: str,
    doc_results: Sequence[dict[str, object]],
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> EvaluationReport:
    """Aggregate per-document ranking results into an EvaluationReport with bootstrap CIs."""
    recalls: list[float] = []
    percentiles: list[float] = []
    mrrs: list[float] = []

    for item in doc_results:
        ranks: list[int] = item["ranks"]  # type: ignore
        total: int = item["total_clauses"]  # type: ignore
        recalls.append(compute_recall_at_pct(ranks, total, pct=0.10))
        percentiles.append(compute_mean_percentile_rank(ranks, total))
        mrrs.append(compute_reciprocal_rank(ranks))

    rec_ci = bootstrap_metric(recalls, n_bootstraps=n_bootstraps, seed=seed)
    pct_ci = bootstrap_metric(percentiles, n_bootstraps=n_bootstraps, seed=seed + 1)
    mrr_ci = bootstrap_metric(mrrs, n_bootstraps=n_bootstraps, seed=seed + 2)

    return EvaluationReport(
        ranker_name=ranker_name,
        recall_at_10=rec_ci,
        mean_percentile_rank=pct_ci,
        mrr=mrr_ci,
        num_documents=len(doc_results),
    )
