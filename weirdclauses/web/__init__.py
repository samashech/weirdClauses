"""Web interface package for WeirdClauses."""

from __future__ import annotations

from weirdclauses.web.server import create_server, start_server
from weirdclauses.web.ui import get_web_ui_html

__all__ = ["create_server", "get_web_ui_html", "start_server"]
