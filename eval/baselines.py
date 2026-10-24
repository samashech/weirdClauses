"""Non-LM baseline rankers: random, length, TF-IDF baseline distance, and heuristic."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from weirdclauses.baseline import get_baseline_pack

HEURISTIC_PATTERNS = [
    re.compile(r"\b(?:penalty|liquidated\s+damages|fine)\b", re.IGNORECASE),
    re.compile(r"\b(?:forfeit|forfeited|forfeiture)\b", re.IGNORECASE),
    re.compile(r"\b(?:waive|waives|waiver|relinquish)\b", re.IGNORECASE),
    re.compile(r"\b(?:unilateral|unrestricted\s+right|at\s+will)\b", re.IGNORECASE),
    re.compile(r"\b(?:without\s+prior\s+(?:notice|notification)|24/7)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:social\s+media|password|credential|surveillance|smart\s+speaker)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:python|exotic\s+animal|predator)\b", re.IGNORECASE),
    re.compile(r"\b(?:gross\s+negligence|willful\s+misconduct|theft)\b", re.IGNORECASE),
    re.compile(r"\b(?:non-refundable|compulsory|gag|disparagement)\b", re.IGNORECASE),
    re.compile(r"\b(?:security\s+lien|possessory\s+lien)\b", re.IGNORECASE),
    re.compile(r"\b(?:attorney\s+fees|litigation\s+expenses)\b", re.IGNORECASE),
]


def score_random(clauses: Sequence[dict[str, Any]], rng: Any) -> list[float]:
    """Assign uniform random scores to clauses."""
    return [rng.random() for _ in clauses]


def score_by_length(clauses: Sequence[dict[str, Any]]) -> list[float]:
    """Score clauses by character length (longer clauses ranked more anomalous)."""
    return [float(len(c["text"])) for c in clauses]


def score_by_heuristic(clauses: Sequence[dict[str, Any]]) -> list[float]:
    """Score clauses by frequency of high-risk / oppressive legal keywords."""
    scores: list[float] = []
    for c in clauses:
        text = c["text"]
        matches = sum(len(p.findall(text)) for p in HEURISTIC_PATTERNS)
        # Bonus for explicit monetary penalties (e.g. $500, $250)
        has_money_penalty = bool(re.search(r"\$\d+(?:\.\d+)?\s*(?:per|penalty|fine)", text, re.I))
        score = float(matches) + (2.0 if has_money_penalty else 0.0)
        scores.append(score)
    return scores


class TFIDFBaselineRanker:
    """Ranks clauses by TF-IDF distance to the nearest clause in the baseline pack."""

    def __init__(self, baseline_texts: Sequence[str] | None = None) -> None:
        if baseline_texts is None:
            pack = get_baseline_pack(mock=False)
            baseline_texts = [bc.text for bc in pack.clauses]

        self.baseline_texts = list(baseline_texts)
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        self.baseline_vectors = self.vectorizer.fit_transform(self.baseline_texts)

    def score_document(self, clauses: Sequence[dict[str, Any]]) -> list[float]:
        """Compute 1.0 - max(cosine_similarity) to any standard baseline clause."""
        doc_texts = [c["text"] for c in clauses]
        doc_vectors = self.vectorizer.transform(doc_texts)
        sim_matrix = cosine_similarity(doc_vectors, self.baseline_vectors)
        # Max similarity to nearest baseline clause
        max_sims = sim_matrix.max(axis=1)
        # Distance = 1.0 - max_similarity (higher distance = more anomalous)
        distances = [float(1.0 - sim) for sim in max_sims]
        return distances


def get_clause_ranks_from_scores(scores: Sequence[float]) -> list[int]:
    """Convert scores (higher is more anomalous) into 1-based ranks (1 is top anomalous)."""
    # Order indices descending by score
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)
    ranks = [0] * len(scores)
    for rank, (orig_idx, _) in enumerate(indexed, start=1):
        ranks[orig_idx] = rank
    return ranks
