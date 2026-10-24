"""Baseline standard clause pack comparison and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StandardClause:
    category: str
    text: str


class BaselinePack:
    """Manages baseline corpus of standard clauses."""

    def __init__(self, pack_dir: Path) -> None:
        self.pack_dir = pack_dir
        self.clauses: list[StandardClause] = []

    def load(self) -> None:
        """Load baseline clauses from pack_dir (stub for Phase 3)."""
        pass

    def retrieve_nearest(self, query_text: str, k: int = 3) -> list[StandardClause]:
        """Retrieve k nearest baseline standard clauses (stub for Phase 3)."""
        return self.clauses[:k]
