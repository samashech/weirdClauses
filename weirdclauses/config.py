"""Configuration settings loaded from environment variables and .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    lm_model: str = os.getenv("WC_LM_MODEL", "Qwen/Qwen2.5-0.5B")
    embed_model: str = os.getenv("WC_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    cache_dir: Path = Path(os.path.expanduser(os.getenv("WC_CACHE_DIR", "~/.cache/weirdclauses")))
    device: str = os.getenv("WC_DEVICE", "cpu")
    baseline_dir: Path = Path(
        os.path.expanduser(os.getenv("WC_BASELINE_DIR", "./baseline_packs/rental"))
    )
    mock: bool = os.getenv("WC_MOCK", "0").lower() in ("1", "true", "yes")
    public_demo: bool = os.getenv("WC_PUBLIC_DEMO", "0").lower() in ("1", "true", "yes")


settings = Settings()
