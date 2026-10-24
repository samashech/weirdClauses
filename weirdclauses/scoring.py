"""Scoring and aggregation module for token surprisal values."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from weirdclauses.segment import Clause


@dataclass
class ScoredClause:
    clause: Clause
    score: float
    z_score: float
    token_count: int


def aggregate_mean(values: Sequence[float]) -> float:
    """Compute arithmetic mean of scores."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def aggregate_max(values: Sequence[float]) -> float:
    """Compute maximum score."""
    if not values:
        return 0.0
    return max(values)


def aggregate_top_quartile_mean(values: Sequence[float]) -> float:
    """Compute mean of the top 25% highest values."""
    if not values:
        return 0.0
    k = max(1, math.ceil(len(values) * 0.25))
    top_k = sorted(values, reverse=True)[:k]
    return sum(top_k) / len(top_k)


AGGREGATORS: dict[str, Callable[[Sequence[float]], float]] = {
    "mean": aggregate_mean,
    "max": aggregate_max,
    "topq": aggregate_top_quartile_mean,
    "top_quartile": aggregate_top_quartile_mean,
    "top_quartile_mean": aggregate_top_quartile_mean,
}


def z_normalize(scores: Sequence[float]) -> list[float]:
    """Z-score normalise a sequence of scores within a document."""
    if not scores:
        return []
    n = len(scores)
    mean = sum(scores) / n
    variance = sum((x - mean) ** 2 for x in scores) / n
    std = math.sqrt(variance)
    if std < 1e-9:
        return [0.0 for _ in scores]
    return [(x - mean) / std for x in scores]


def score_clauses(
    clauses: Sequence[Clause],
    token_surprisals: Sequence[tuple[int, int, float]],
    aggregator: str = "topq",
) -> list[ScoredClause]:
    """Aggregate token surprisals into scored clauses and rank by weirdness.

    Only clauses with kind == 'clause' are scored. Headings and frames are excluded.
    Token surprisals are mapped to clauses by character span midpoint.
    """
    agg_fn = AGGREGATORS.get(aggregator.lower())
    if agg_fn is None:
        valid = ", ".join(repr(k) for k in ("mean", "topq", "max"))
        raise ValueError(f"Unknown aggregator '{aggregator}'. Valid options are: {valid}")

    # Map each clause id to its assigned token surprisals
    clause_tokens: dict[int, list[float]] = {c.id: [] for c in clauses if c.kind == "clause"}

    # Assign token surprisals to clause spans via token midpoint
    for t_start, t_end, bits in token_surprisals:
        mid = (t_start + t_end) // 2
        for c in clauses:
            if c.kind == "clause" and c.start <= mid < c.end:
                clause_tokens[c.id].append(bits)
                break

    # Calculate raw aggregation score for each scored clause
    scored_list: list[tuple[Clause, float, int]] = []
    for c in clauses:
        if c.kind != "clause":
            continue
        scores = clause_tokens.get(c.id, [])
        score = agg_fn(scores) if scores else 0.0
        scored_list.append((c, score, len(scores)))

    # Compute z-scores across all evaluated clauses in the document
    raw_scores = [s for _, s, _ in scored_list]
    z_scores = z_normalize(raw_scores)

    results: list[ScoredClause] = []
    for (clause, score, count), z in zip(scored_list, z_scores, strict=True):
        results.append(
            ScoredClause(
                clause=clause,
                score=round(score, 4),
                z_score=round(z, 4),
                token_count=count,
            )
        )

    # Rank descending by score (most surprising first)
    results.sort(key=lambda sc: sc.score, reverse=True)
    return results
