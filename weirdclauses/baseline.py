"""Baseline standard clause pack loading, embedding, and semantic retrieval."""

from __future__ import annotations

import contextlib
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from weirdclauses.config import settings


@dataclass(frozen=True)
class BaselineClause:
    topic: str
    title: str
    text: str
    file_name: str
    jurisdiction: str = "generic-synthetic"
    synthetic: bool = True


@dataclass(frozen=True)
class BaselineMatch:
    clause: BaselineClause
    similarity: float


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Extract YAML-style frontmatter and body from markdown text."""
    meta: dict[str, str] = {}
    body = content
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    if match:
        raw_meta, body = match.group(1), match.group(2)
        for line in raw_meta.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip().strip("'\"")
    return meta, body.strip()


class BaselinePack:
    """Manages baseline standard clause corpus and sentence embeddings."""

    def __init__(
        self,
        pack_dir: Path | None = None,
        embed_model: str | None = None,
    ) -> None:
        self.pack_dir = pack_dir or settings.baseline_dir
        self.embed_model = embed_model or settings.embed_model
        self.clauses: list[BaselineClause] = []
        self._embeddings: np.ndarray | None = None
        self._model: Any = None

    def load(self) -> None:
        """Load all markdown standard clauses from pack_dir."""
        if not self.pack_dir.exists():
            return
        self.clauses.clear()
        for md_file in sorted(self.pack_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(content)
            if body:
                self.clauses.append(
                    BaselineClause(
                        topic=meta.get("topic", "general"),
                        title=meta.get("title", md_file.stem),
                        text=body,
                        file_name=md_file.name,
                        jurisdiction=meta.get("jurisdiction", "generic-synthetic"),
                        synthetic=meta.get("synthetic", "true").lower() == "true",
                    )
                )

    def _get_cache_path(self) -> Path:
        """Return cache path for current pack clauses and embed model."""
        combined_text = "".join(c.text for c in self.clauses)
        pack_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()[:16]
        safe_model = re.sub(r"[^\w\-.]", "--", self.embed_model)
        cache_dir = settings.cache_dir / "embeddings"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{safe_model}_{pack_hash}.npy"

    def _ensure_embeddings(self) -> np.ndarray:
        """Ensure embeddings are computed and normalized, using disk cache if available."""
        if self._embeddings is not None:
            return self._embeddings

        if not self.clauses:
            self.load()
        if not self.clauses:
            return np.empty((0, 384), dtype=np.float32)

        cache_path = self._get_cache_path()
        if cache_path.is_file():
            with contextlib.suppress(Exception):
                self._embeddings = np.load(cache_path)
                return self._embeddings

        from sentence_transformers import SentenceTransformer

        if self._model is None:
            self._model = SentenceTransformer(self.embed_model)

        texts = [c.text for c in self.clauses]
        embs = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        self._embeddings = np.asarray(embs, dtype=np.float32)

        with contextlib.suppress(OSError):
            np.save(cache_path, self._embeddings)

        return self._embeddings

    def retrieve_nearest(self, query_text: str, k: int = 3) -> list[BaselineMatch]:
        """Retrieve k nearest standard baseline clauses with cosine similarity."""
        if not self.clauses:
            self.load()
        if not self.clauses:
            return []

        embeddings = self._ensure_embeddings()
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.embed_model)

        q_emb = self._model.encode([query_text], normalize_embeddings=True, show_progress_bar=False)
        q_vec = np.asarray(q_emb[0], dtype=np.float32)

        sims = np.dot(embeddings, q_vec)
        top_k_indices = np.argsort(sims)[::-1][:k]

        return [
            BaselineMatch(clause=self.clauses[idx], similarity=round(float(sims[idx]), 4))
            for idx in top_k_indices
        ]


class FakeBaselinePack:
    """Mock baseline retriever using word-overlap similarity for fast offline tests."""

    def __init__(self, pack_dir: Path | None = None) -> None:
        self.pack_dir = pack_dir or settings.baseline_dir
        self.clauses: list[BaselineClause] = []

    def load(self) -> None:
        if not self.pack_dir.exists():
            return
        self.clauses.clear()
        for md_file in sorted(self.pack_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(content)
            if body:
                self.clauses.append(
                    BaselineClause(
                        topic=meta.get("topic", "general"),
                        title=meta.get("title", md_file.stem),
                        text=body,
                        file_name=md_file.name,
                    )
                )

    def retrieve_nearest(self, query_text: str, k: int = 3) -> list[BaselineMatch]:
        if not self.clauses:
            self.load()
        if not self.clauses:
            return []

        query_words = set(re.findall(r"\b\w+\b", query_text.lower()))
        scores: list[tuple[float, BaselineClause]] = []

        for c in self.clauses:
            clause_words = set(re.findall(r"\b\w+\b", c.text.lower()))
            overlap = len(query_words & clause_words)
            sim = overlap / max(1, len(query_words | clause_words))
            scores.append((sim, c))

        scores.sort(key=lambda item: item[0], reverse=True)
        return [BaselineMatch(clause=c, similarity=round(sim + 0.1, 4)) for sim, c in scores[:k]]


def get_baseline_pack(
    pack_dir: Path | None = None,
    embed_model: str | None = None,
    mock: bool = False,
) -> BaselinePack | FakeBaselinePack:
    """Factory returning BaselinePack or FakeBaselinePack."""
    if mock or settings.mock:
        pack = FakeBaselinePack(pack_dir=pack_dir)
        pack.load()
        return pack
    real_pack = BaselinePack(pack_dir=pack_dir, embed_model=embed_model)
    real_pack.load()
    return real_pack
