"""Disk caching for token surprisal scores keyed by (model_id, text_hash)."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Sequence
from pathlib import Path

from weirdclauses.config import settings


def _compute_text_hash(text: str) -> str:
    """Compute deterministic SHA-256 hash for text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sanitize_model_id(model_id: str) -> str:
    """Sanitize model ID for use in filesystem directory names."""
    return re.sub(r"[^\w\-.]", "--", model_id)


def get_cache_dir(cache_root: Path | None = None) -> Path:
    """Return the base directory for cached surprisals."""
    root = cache_root or settings.cache_dir
    cache_path = root / "surprisals"
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def get_cache_path(model_id: str, text: str, cache_root: Path | None = None) -> Path:
    """Return file path for a cached (model_id, text) pair."""
    safe_model = _sanitize_model_id(model_id)
    text_hash = _compute_text_hash(text)
    model_dir = get_cache_dir(cache_root) / safe_model
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir / f"{text_hash}.json"


def get_cached_surprisals(
    model_id: str, text: str, cache_root: Path | None = None
) -> list[tuple[int, int, float]] | None:
    """Retrieve cached token surprisals if present, else return None."""
    path = get_cache_path(model_id, text, cache_root)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [(int(item[0]), int(item[1]), float(item[2])) for item in data]
    except (json.JSONDecodeError, KeyError, IndexError, ValueError, OSError):
        return None


def save_cached_surprisals(
    model_id: str,
    text: str,
    surprisals: Sequence[tuple[int, int, float]],
    cache_root: Path | None = None,
) -> None:
    """Atomically write token surprisals to disk cache."""
    path = get_cache_path(model_id, text, cache_root)
    temp_path = path.with_suffix(f".tmp.{os.getpid()}")
    try:
        data = [[s, e, round(b, 5)] for s, e, b in surprisals]
        temp_path.write_text(json.dumps(data), encoding="utf-8")
        temp_path.replace(path)
    except OSError:
        if temp_path.exists():
            temp_path.unlink()
