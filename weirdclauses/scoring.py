"""Scoring and aggregation module supporting raw and baseline-conditional surprisal."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal

from weirdclauses.baseline import BaselineMatch, BaselinePack, FakeBaselinePack
from weirdclauses.lm import SurprisalEngine
from weirdclauses.segment import Clause

ScoringMode = Literal["raw", "conditional"]


@dataclass
class ScoredClause:
    clause: Clause
    score: float
    z_score: float
    token_count: int
    raw_surprisal: float | None = None
    conditional_surprisal: float | None = None
    nearest_similarity: float | None = None
    gain: float | None = None
    nearest_matches: list[BaselineMatch] = field(default_factory=list)
    tokens: list[tuple[int, int, float]] = field(default_factory=list)


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


def build_conditional_prompt(
    clause_text: str,
    matches: Sequence[BaselineMatch],
    max_neighbour_chars: int = 1200,
) -> tuple[str, int]:
    """Build conditional prompt with standard baseline neighbours and return clause start index."""
    lines = ["Standard clauses of this type:"]
    budget = max_neighbour_chars
    for m in matches:
        text = m.clause.text.strip()
        if len(text) > budget:
            text = text[:budget] + "..."
        lines.append(f"- {text}")
        budget -= len(text)
        if budget <= 100:
            break

    lines.extend(["", "Clause under review:", ""])
    prefix = "\n".join(lines)
    full_prompt = prefix + clause_text.strip()
    clause_char_start = len(prefix)
    return full_prompt, clause_char_start


def score_clauses(
    clauses: Sequence[Clause],
    token_surprisals: Sequence[tuple[int, int, float]],
    aggregator: str = "topq",
    mode: ScoringMode = "raw",
    baseline_pack: BaselinePack | FakeBaselinePack | None = None,
    engine: SurprisalEngine | None = None,
    k_nearest: int = 3,
) -> list[ScoredClause]:
    """Score clauses in raw or conditional mode and rank descending by weirdness."""
    agg_fn = AGGREGATORS.get(aggregator.lower())
    if agg_fn is None:
        valid = ", ".join(repr(k) for k in ("mean", "topq", "max"))
        raise ValueError(f"Unknown aggregator '{aggregator}'. Valid options are: {valid}")

    # Map raw token surprisals to clause spans via token midpoint
    clause_tokens: dict[int, list[tuple[int, int, float]]] = {
        c.id: [] for c in clauses if c.kind == "clause"
    }
    for t_start, t_end, bits in token_surprisals:
        mid = (t_start + t_end) // 2
        for c in clauses:
            if c.kind == "clause" and c.start <= mid < c.end:
                clause_tokens[c.id].append((t_start, t_end, bits))
                break

    scored_items: list[ScoredClause] = []

    for c in clauses:
        if c.kind != "clause":
            continue

        raw_toks = clause_tokens.get(c.id, [])
        raw_bits = [b for _, _, b in raw_toks]
        raw_score = round(agg_fn(raw_bits) if raw_bits else 0.0, 4)

        # Retrieve nearest standard clauses from baseline pack
        matches: list[BaselineMatch] = []
        if baseline_pack is not None:
            matches = baseline_pack.retrieve_nearest(c.content, k=k_nearest)

        nearest_sim = matches[0].similarity if matches else None
        cond_score: float | None = None
        gain: float | None = None

        if mode == "conditional" and engine is not None and matches:
            prompt, c_start = build_conditional_prompt(c.content, matches)
            cond_tokens = engine.token_surprisals(prompt)
            target_bits = [bits for s, _, bits in cond_tokens if s >= c_start]
            cond_score = round(agg_fn(target_bits) if target_bits else raw_score, 4)
            gain = round(raw_score - cond_score, 4)

        if mode == "conditional" and cond_score is not None:
            primary_score = cond_score
        else:
            primary_score = raw_score
        scored_items.append(
            ScoredClause(
                clause=c,
                score=primary_score,
                z_score=0.0,  # Computed below
                token_count=len(raw_bits),
                raw_surprisal=raw_score,
                conditional_surprisal=cond_score,
                nearest_similarity=nearest_sim,
                gain=gain,
                nearest_matches=matches,
                tokens=raw_toks,
            )
        )

    # Compute z-scores across all evaluated clauses in document
    scores = [item.score for item in scored_items]
    z_scores = z_normalize(scores)
    for item, z in zip(scored_items, z_scores, strict=True):
        item.z_score = round(z, 4)

    # Rank descending by primary score
    scored_items.sort(key=lambda item: item.score, reverse=True)
    return scored_items
