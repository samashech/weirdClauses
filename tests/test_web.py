"""Unit and integration tests for local offline web interface and REST API."""

from __future__ import annotations

import json
import re
import threading
import urllib.error
import urllib.request
from collections.abc import Generator
from typing import Any

import pytest
from typer.testing import CliRunner

from weirdclauses import LEGAL_DISCLAIMER, __version__
from weirdclauses.cli import app
from weirdclauses.report import validate_report
from weirdclauses.web.server import create_server
from weirdclauses.web.ui import get_web_ui_html


@pytest.fixture(scope="module")
def web_server_url() -> Generator[str, None, None]:
    """Start local test server on an ephemeral port in a daemon thread."""
    server = create_server(host="127.0.0.1", port=0)
    assigned_port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{assigned_port}"
    try:
        yield base_url
    finally:
        server.shutdown()
        server.server_close()


def _http_get(url: str) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, headers, resp.read()
    except urllib.error.HTTPError as err:
        headers = {k.lower(): v for k, v in err.headers.items()}
        return err.code, headers, err.read()


def _http_post(url: str, payload: Any) -> tuple[int, dict[str, str], bytes]:
    body = json.dumps(payload).encode("utf-8") if isinstance(payload, (dict, list)) else payload
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, headers, resp.read()
    except urllib.error.HTTPError as err:
        headers = {k.lower(): v for k, v in err.headers.items()}
        return err.code, headers, err.read()


def test_web_ui_template() -> None:
    """Template rendering injects disclaimer and package version."""
    html = get_web_ui_html()
    assert "{{LEGAL_DISCLAIMER}}" not in html
    assert "{{VERSION}}" not in html
    assert LEGAL_DISCLAIMER in html
    assert f"v{__version__}" in html
    assert "WeirdClauses Explorer" in html


def test_get_root_and_health(web_server_url: str) -> None:
    """Root serves HTML and health endpoint returns system status."""
    status, headers, body = _http_get(f"{web_server_url}/")
    assert status == 200
    assert "text/html" in headers.get("content-type", "")
    assert LEGAL_DISCLAIMER in body.decode("utf-8")

    status, headers, body = _http_get(f"{web_server_url}/health")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["status"] == "ok"
    assert data["version"] == __version__
    assert data["disclaimer"] == LEGAL_DISCLAIMER


def test_get_samples_endpoints(web_server_url: str) -> None:
    """Sample discovery and retrieval endpoints return existing samples."""
    status, _, body = _http_get(f"{web_server_url}/api/samples")
    assert status == 200
    samples = json.loads(body.decode("utf-8"))
    sample_names = [s["name"] for s in samples]
    assert "normal_rental.txt" in sample_names
    assert "unusual_rental.txt" in sample_names

    # Valid sample retrieval
    status, _, body = _http_get(f"{web_server_url}/api/samples/normal_rental.txt")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["name"] == "normal_rental.txt"
    assert "RESIDENTIAL LEASE AGREEMENT" in data["text"]

    # Missing sample retrieval
    status, _, body = _http_get(f"{web_server_url}/api/samples/nonexistent_lease.txt")
    assert status == 404


def test_analyze_endpoint_mock_mode(web_server_url: str) -> None:
    """POST /api/analyze runs end-to-end pipeline and yields valid report."""
    sample_text = (
        "1. Rent and Term\n"
        "Tenant shall pay monthly rent of $1,800 on the first day of each month.\n"
        "2. Surrender of Personal Freedom\n"
        "Tenant agrees that Landlord may inspect premises without notice at 3:00 AM.\n"
    )
    payload = {
        "text": sample_text,
        "mode": "conditional",
        "aggregator": "topq",
        "mock": True,
    }
    status, headers, body = _http_post(f"{web_server_url}/api/analyze", payload)
    assert status == 200
    assert "application/json" in headers.get("content-type", "")
    report = json.loads(body.decode("utf-8"))

    # Must validate against JSON schema
    validate_report(report)
    assert report["version"] == __version__
    assert report["disclaimer"] == LEGAL_DISCLAIMER
    assert len(report["clauses"]) >= 2
    assert len(report["key_facts"]) >= 1


def test_analyze_endpoint_validation_errors(web_server_url: str) -> None:
    """POST /api/analyze rejects empty text or malformed JSON payloads."""
    # Empty text
    status, _, body = _http_post(f"{web_server_url}/api/analyze", {"text": ""})
    assert status == 400
    assert "No text provided" in json.loads(body.decode("utf-8"))["error"]

    # Malformed JSON
    status, _, _ = _http_post(f"{web_server_url}/api/analyze", b"not-a-valid-json{")
    assert status == 400


def test_export_endpoint(web_server_url: str) -> None:
    """POST /api/export renders HTML, Markdown, and JSON report downloads."""
    sample_text = "1. Rent is $1,200 due monthly. Deposit is $1,200."
    _, _, body = _http_post(
        f"{web_server_url}/api/analyze",
        {"text": sample_text, "mock": True, "mode": "raw"},
    )
    report_dict = json.loads(body.decode("utf-8"))

    # Test HTML export
    status, headers, html_bytes = _http_post(
        f"{web_server_url}/api/export?format=html", report_dict
    )
    assert status == 200
    assert "text/html" in headers.get("content-type", "")
    assert LEGAL_DISCLAIMER in html_bytes.decode("utf-8")

    # Test Markdown export
    status, headers, md_bytes = _http_post(f"{web_server_url}/api/export?format=md", report_dict)
    assert status == 200
    assert "text/markdown" in headers.get("content-type", "")
    assert LEGAL_DISCLAIMER in md_bytes.decode("utf-8")

    # Test JSON export
    status, headers, json_bytes = _http_post(
        f"{web_server_url}/api/export?format=json", report_dict
    )
    assert status == 200
    assert "application/json" in headers.get("content-type", "")
    assert json.loads(json_bytes.decode("utf-8"))["version"] == __version__

    # Test bad json
    status, _, _ = _http_post(f"{web_server_url}/api/export", b"{bad-json")
    assert status == 400


def test_cli_serve_help() -> None:
    """weirdclauses serve --help displays arguments and options."""
    runner = CliRunner()
    result = runner.invoke(app, ["serve", "--help"], env={"NO_COLOR": "1"})
    assert result.exit_code == 0
    clean_out = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.stdout)
    assert "--host" in clean_out
    assert "--port" in clean_out
    assert "--mock" in clean_out
    assert "--open" in clean_out


def test_upload_disabled_in_demo(web_server_url: str) -> None:
    """POST and GET /api/upload return 403 Forbidden explaining demo upload restrictions."""
    status, _, body = _http_post(f"{web_server_url}/api/upload", {"sample": "data"})
    assert status == 403
    assert "disabled" in json.loads(body.decode("utf-8"))["error"].lower()

    status, _, body = _http_get(f"{web_server_url}/api/upload")
    assert status == 403
    assert "disabled" in json.loads(body.decode("utf-8"))["error"].lower()


def test_public_demo_template_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """When WC_PUBLIC_DEMO is active, the template injects public demo flag."""
    from weirdclauses.config import Settings

    monkeypatch.setattr("weirdclauses.web.ui.settings", Settings(public_demo=True))
    html = get_web_ui_html()
    assert "const isPublicDemo = true;" in html
    assert "{{PUBLIC_DEMO}}" not in html
