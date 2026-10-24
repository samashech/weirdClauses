"""Causal language model teacher-forced surprisal scorer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TokenSurprisal:
    token: str
    token_id: int
    surprisal: float  # -log2(p)
    start_char: int
    end_char: int


class LMProtocol(Protocol):
    def score_text(self, text: str) -> list[TokenSurprisal]:
        """Compute per-token surprisal values for the input text."""
        ...


class FakeLMScorer:
    """Deterministic fake LM scorer for offline tests and mocking."""

    def __init__(self, default_surprisal: float = 2.5) -> None:
        self.default_surprisal = default_surprisal

    def score_text(self, text: str) -> list[TokenSurprisal]:
        words = text.split()
        tokens: list[TokenSurprisal] = []
        pos = 0
        for idx, word in enumerate(words):
            start = text.find(word, pos)
            end = start + len(word)
            pos = end
            # Produce deterministic surprisal based on word length
            surprisal = self.default_surprisal + (len(word) % 5) * 0.5
            tokens.append(
                TokenSurprisal(
                    token=word,
                    token_id=idx + 100,
                    surprisal=surprisal,
                    start_char=start,
                    end_char=end,
                )
            )
        return tokens
