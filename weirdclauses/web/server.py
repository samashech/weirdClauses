"""Local offline HTTP server for WeirdClauses interactive web interface."""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from weirdclauses import LEGAL_DISCLAIMER, __version__
from weirdclauses.baseline import get_baseline_pack
from weirdclauses.config import settings
from weirdclauses.facts import attach_facts_to_clauses
from weirdclauses.lm import get_surprisal_engine
from weirdclauses.report import build_report, export_html, export_json, export_markdown
from weirdclauses.scoring import score_clauses
from weirdclauses.segment import segment_clauses
from weirdclauses.web.ui import get_web_ui_html

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


class WeirdClausesHandler(BaseHTTPRequestHandler):
    """HTTP request handler serving the single-page app and REST analysis endpoints."""

    server_version = f"WeirdClauses/{__version__}"

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stdout request logging."""
        pass

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, text: str, content_type: str, status: int = 200) -> None:
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("", "/"):
            self._send_text(get_web_ui_html(), "text/html")
        elif path in ("/health", "/api/health"):
            self._send_json(
                {"status": "ok", "version": __version__, "disclaimer": LEGAL_DISCLAIMER}
            )
        elif path == "/api/samples":
            samples: list[dict[str, str]] = []
            if SAMPLES_DIR.exists():
                for p in sorted(SAMPLES_DIR.glob("*.txt")):
                    samples.append({"name": p.name, "path": str(p)})
            self._send_json(samples)
        elif path.startswith("/api/samples/"):
            filename = urllib.parse.unquote(path.removeprefix("/api/samples/"))
            target = SAMPLES_DIR / filename
            if target.exists() and target.is_file() and target.suffix in (".txt", ".md"):
                self._send_json({"name": filename, "text": target.read_text(encoding="utf-8")})
            else:
                self._send_json({"error": f"Sample '{filename}' not found"}, status=404)
        else:
            self._send_json({"error": "Not Found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else ""

        if path == "/api/analyze":
            try:
                req = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_json({"error": "Invalid JSON body"}, status=400)
                return

            text = req.get("text", "")
            if not text:
                self._send_json({"error": "No text provided for analysis"}, status=400)
                return

            # Public demo restriction if enabled
            if settings.public_demo and len(text) > 50_000:
                self._send_json(
                    {"error": "Text exceeds public demo character limit (50,000 chars)"},
                    status=400,
                )
                return

            mode = req.get("mode", "conditional")
            aggregator = req.get("aggregator", "topq")
            mock = bool(req.get("mock", settings.mock))

            clauses = segment_clauses(text)
            facts_by_clause = attach_facts_to_clauses(clauses)
            baseline_pack = get_baseline_pack(mock=mock)
            engine = get_surprisal_engine(mock=mock)
            surprisals = engine.token_surprisals(text)

            scored = score_clauses(
                clauses,
                surprisals,
                aggregator=aggregator,
                mode=mode,
                baseline_pack=baseline_pack,
                engine=engine,
            )

            report = build_report(
                raw_text=text,
                clauses=clauses,
                scored_clauses=scored,
                facts_by_clause=facts_by_clause,
                lm_model="mock-lm" if mock else settings.lm_model,
                embed_model="mock-embed" if mock else settings.embed_model,
                device=settings.device,
                mode=mode,
                aggregator=aggregator,
            )
            self._send_json(report)

        elif path == "/api/export":
            query = urllib.parse.parse_qs(parsed.query)
            fmt = query.get("format", ["html"])[0].lower()
            try:
                rep = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "Invalid JSON body"}, status=400)
                return

            if fmt == "json":
                self._send_text(export_json(rep), "application/json")
            elif fmt in ("md", "markdown"):
                self._send_text(export_markdown(rep), "text/markdown")
            else:
                self._send_text(export_html(rep), "text/html")
        else:
            self._send_json({"error": "Not Found"}, status=404)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Instantiate the threading HTTP server."""
    return ThreadingHTTPServer((host, port), WeirdClausesHandler)


def start_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = False,
) -> None:
    """Start local web server and block until interrupted."""
    server = create_server(host, port)
    url = f"http://{host}:{port}"
    print(f"\n{LEGAL_DISCLAIMER}\n")
    print(f"WeirdClauses web explorer running at: {url}")
    print("Press Ctrl+C to stop.\n")

    if open_browser:
        import webbrowser

        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
    finally:
        server.server_close()
