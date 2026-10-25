"""System environment and model cache diagnostics for WeirdClauses."""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from weirdclauses import LEGAL_DISCLAIMER
from weirdclauses.config import settings


def check_model_cached(model_name: str) -> tuple[bool, str]:
    """Check if model weights and config are already in local Hugging Face cache."""
    try:
        from transformers import AutoConfig

        AutoConfig.from_pretrained(model_name, local_files_only=True)
        return True, "cached locally"
    except (OSError, ValueError, Exception) as exc:
        return False, f"not downloaded yet ({type(exc).__name__})"


def check_cache_dir(cache_path: Path) -> tuple[bool, str]:
    """Verify that the cache directory is writable."""
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        test_file = cache_path / ".doctor_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return True, f"writable ({cache_path})"
    except Exception as exc:
        return False, f"not writable: {exc}"


def run_doctor(console: Console | None = None, mock: bool = False) -> bool:
    """Execute all diagnostic checks and print Rich report."""
    con = console or Console()
    con.print(
        Panel.fit(
            f"[bold yellow]{LEGAL_DISCLAIMER}[/bold yellow]",
            title="[bold red]Legal Disclaimer[/bold red]",
            border_style="yellow",
        )
    )

    table = Table(title="WeirdClauses System Diagnostics", show_lines=True)
    table.add_column("Component", style="bold cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    all_ok = True
    is_mock = mock or bool(settings.mock)
    if is_mock:
        table.add_row(
            "Mock Mode",
            "[bold green]ENABLED[/bold green]",
            "Deterministic offline testing; no model downloads required",
        )
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python Version", "[green]PASS[/green]", f"{py_ver} (>= 3.11)")

    try:
        import torch

        cuda = torch.cuda.is_available()
        table.add_row(
            "PyTorch",
            "[green]PASS[/green]",
            f"v{torch.__version__} (CUDA: {cuda}, {settings.device})",
        )
    except ImportError as e:
        table.add_row("PyTorch", "[red]FAIL[/red]", str(e))
        all_ok = False

    try:
        import transformers

        table.add_row("Transformers", "[green]PASS[/green]", f"v{transformers.__version__}")
    except ImportError as e:
        table.add_row("Transformers", "[red]FAIL[/red]", str(e))
        all_ok = False

    c_ok, c_msg = check_cache_dir(settings.cache_dir)
    table.add_row("Cache Directory", "[green]PASS[/green]" if c_ok else "[red]FAIL[/red]", c_msg)
    all_ok = all_ok and c_ok

    lm_ok, lm_msg = check_model_cached(settings.lm_model)
    table.add_row(
        f"LM ({settings.lm_model})",
        "[green]CACHED[/green]" if lm_ok else "[yellow]NOT DOWNLOADED[/yellow]",
        lm_msg,
    )

    em_ok, em_msg = check_model_cached(settings.embed_model)
    table.add_row(
        f"Embed ({settings.embed_model})",
        "[green]CACHED[/green]" if em_ok else "[yellow]NOT DOWNLOADED[/yellow]",
        em_msg,
    )

    b_ok = settings.baseline_dir.exists()
    table.add_row(
        "Baseline Dir",
        "[green]FOUND[/green]" if b_ok else "[yellow]MISSING[/yellow]",
        str(settings.baseline_dir),
    )

    con.print(table)
    if not all_ok:
        con.print("[bold red]Critical environment checks failed.[/bold red]")
        return False
    con.print("[bold green]System is ready.[/bold green]")
    return True
