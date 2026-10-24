"""Causal language model teacher-forced token surprisal engine."""

from __future__ import annotations

import math
from typing import Any, Protocol

from weirdclauses.cache import get_cached_surprisals, save_cached_surprisals
from weirdclauses.config import settings
from weirdclauses.fake_lm import FakeLM


class SurprisalEngine(Protocol):
    """Protocol for token surprisal scorers."""

    def token_surprisals(self, text: str) -> list[tuple[int, int, float]]:
        """Compute token surprisals: list of (char_start, char_end, bits)."""
        ...


class CausalLMScorer:
    """Computes teacher-forced token surprisals using a local open-weight base causal LM."""

    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        self.model_name = model_name or settings.lm_model
        self.device_name = device or settings.device
        self._tokenizer: Any = None
        self._model: Any = None
        self._device: Any = None

    def _ensure_loaded(self) -> None:
        """Lazily load torch, transformers, tokenizer, and model weights."""
        if self._model is not None:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self._device = torch.device(self.device_name)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            dtype=torch.float32,
        ).to(self._device)
        self._model.eval()

    def token_surprisals(self, text: str, window_size: int = 512) -> list[tuple[int, int, float]]:
        """Compute per-token surprisals (-log2 p) using teacher-forced sliding windows.

        Excludes the first token of each window from scored targets.
        Uses fast tokenizer offset_mapping to map tokens directly to character spans.
        Results are cached to disk keyed by (model_id, text_hash).
        """
        if not text:
            return []

        # Check disk cache first (bypasses model loading if cached)
        cached = get_cached_surprisals(self.model_name, text)
        if cached is not None:
            return cached

        self._ensure_loaded()
        import torch

        encoding = self._tokenizer(
            text,
            return_offsets_mapping=True,
            add_special_tokens=True,
        )
        input_ids: list[int] = encoding["input_ids"]
        offset_mapping: list[tuple[int, int]] = encoding["offset_mapping"]

        # Handle BOS: prepend if model expects BOS and it was not added
        bos_id = self._tokenizer.bos_token_id
        if bos_id is not None and (not input_ids or input_ids[0] != bos_id):
            input_ids = [bos_id] + input_ids
            offset_mapping = [(0, 0)] + offset_mapping

        total_tokens = len(input_ids)
        if total_tokens <= 1:
            return []

        max_pos = getattr(self._model.config, "max_position_embeddings", window_size)
        win_size = max(64, min(window_size, max_pos))
        stride = win_size // 2
        overlap = win_size - stride

        surprisals_by_pos: dict[int, float] = {}
        t_start = 1

        while t_start < total_tokens:
            t_end = min(t_start + stride, total_tokens)
            ctx_start = max(0, t_start - overlap)
            ctx_end = min(total_tokens, ctx_start + win_size)

            window_tokens = input_ids[ctx_start:ctx_end]
            if len(window_tokens) < 2:
                break

            with torch.inference_mode():
                in_tensor = torch.tensor([window_tokens], device=self._device)
                logits = self._model(in_tensor).logits
                log_probs = torch.log_softmax(logits[0, :-1, :], dim=-1)

            # Target tokens for this window are in global indices [t_start, t_end)
            for g_idx in range(t_start, t_end):
                w_pos = g_idx - ctx_start
                target_token = input_ids[g_idx]
                log_p = log_probs[w_pos - 1, target_token].item()
                bits = -log_p / math.log(2.0)
                surprisals_by_pos[g_idx] = bits

            t_start = t_end

        results: list[tuple[int, int, float]] = []
        for g_idx in sorted(surprisals_by_pos.keys()):
            c_start, c_end = offset_mapping[g_idx]
            if c_start < c_end:
                results.append((c_start, c_end, round(surprisals_by_pos[g_idx], 4)))

        save_cached_surprisals(self.model_name, text, results)
        return results


def get_surprisal_engine(
    mock: bool = False,
    model_name: str | None = None,
    device: str | None = None,
) -> SurprisalEngine:
    """Return a surprisal engine: FakeLM if mock is True, else CausalLMScorer."""
    if mock or settings.mock:
        return FakeLM(model_id=model_name or "fake-lm-v1")
    return CausalLMScorer(model_name=model_name, device=device)
