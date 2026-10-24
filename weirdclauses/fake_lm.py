"""Deterministic FakeLM scorer based on a word-frequency table for fast offline tests."""

from __future__ import annotations

import re

# Surprisal values in bits (-log2 p) for frequent vs unusual terms
_BASE_SURPRISALS: dict[str, float] = {
    # Very frequent function words
    "the": 1.2,
    "of": 1.5,
    "and": 1.6,
    "a": 1.8,
    "to": 1.7,
    "in": 1.9,
    "is": 2.1,
    "for": 2.2,
    "on": 2.3,
    "by": 2.4,
    "with": 2.5,
    "at": 2.6,
    "this": 2.4,
    "that": 2.7,
    "or": 2.5,
    "as": 2.3,
    "be": 2.2,
    # Standard residential agreement terms (expected in context)
    "tenant": 2.8,
    "landlord": 2.9,
    "lease": 3.0,
    "rent": 3.1,
    "agreement": 3.0,
    "premises": 3.2,
    "shall": 2.9,
    "month": 3.3,
    "notice": 3.4,
    "deposit": 3.5,
    "written": 3.6,
    "days": 3.2,
    "repairs": 3.8,
    "utilities": 3.7,
    "maintenance": 3.9,
    "clean": 4.0,
    "condition": 3.8,
    "payment": 3.5,
    "term": 3.6,
    "calendar": 3.9,
    "occupancy": 4.1,
    # Bizarre or unexpected terms (planted clauses have high surprisal)
    "accordion": 12.5,
    "polka": 13.0,
    "nocturnal": 11.8,
    "psychic": 12.2,
    "cleansing": 11.5,
    "thermometer": 10.8,
    "sofa": 9.5,
    "feline": 11.2,
    "audits": 10.4,
    "ledger": 10.2,
    "disharmony": 12.8,
    "easement": 8.7,
    "privilege": 8.5,
    "glances": 11.4,
    "hourly": 8.9,
}


class FakeLM:
    """Mock language model providing deterministic surprisal scores."""

    def __init__(self, model_id: str = "fake-lm-v1") -> None:
        self.model_id = model_id

    def token_surprisals(self, text: str) -> list[tuple[int, int, float]]:
        """Return deterministic token surprisals (char_start, char_end, bits)."""
        if not text:
            return []

        tokens: list[tuple[int, int, float]] = []
        pattern = re.compile(r"\w+|[^\w\s]")

        for m in pattern.finditer(text):
            word = m.group(0)
            clean = word.lower()
            start, end = m.start(), m.end()

            if clean in _BASE_SURPRISALS:
                bits = _BASE_SURPRISALS[clean]
            elif word.isdigit():
                bits = 4.5
            elif not word.isalnum():
                bits = 2.0  # Punctuation
            else:
                # Deterministic fallback based on word length and char sum
                char_sum = sum(ord(c) for c in clean)
                bits = 5.0 + (char_sum % 30) / 10.0 + min(len(clean) * 0.15, 2.5)

            tokens.append((start, end, round(bits, 4)))

        return tokens
