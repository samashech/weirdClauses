"""Pytest configuration and shared test fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

# Ensure offline mock mode for tests by default
os.environ["WC_MOCK"] = "1"
os.environ["WC_CACHE_DIR"] = "/tmp/weirdclauses_test_cache"


@pytest.fixture
def cli_runner() -> CliRunner:
    """Fixture providing Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def samples_dir() -> Path:
    """Fixture returning path to samples directory."""
    return Path(__file__).resolve().parent.parent / "samples"
