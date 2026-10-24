"""Scoring and aggregation module for token surprisal values."""

from __future__ import annotations

import math
from collections.abc import Sequence


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
