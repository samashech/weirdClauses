"""Web UI template loader for WeirdClauses."""

from __future__ import annotations

from pathlib import Path

from weirdclauses import LEGAL_DISCLAIMER, __version__

INDEX_HTML_PATH = Path(__file__).resolve().parent / "index.html"


def get_web_ui_html() -> str:
    """Return self-contained HTML/CSS/JS for local offline web interface."""
    template = INDEX_HTML_PATH.read_text(encoding="utf-8")
    return template.replace("{{LEGAL_DISCLAIMER}}", LEGAL_DISCLAIMER).replace(
        "{{VERSION}}", __version__
    )
