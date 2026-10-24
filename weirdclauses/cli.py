"""CLI interface for WeirdClauses."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from weirdclauses import LEGAL_DISCLAIMER, __version__
from weirdclauses.config import settings

app = typer.Typer(
    name="weirdclauses",
    help="WeirdClauses: Local, offline contract clause surprisal and anomaly ranking tool.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(
            f"[bold cyan]WeirdClauses[/bold cyan] version [bold green]{__version__}[/bold green]"
        )
        console.print(f"[dim]{LEGAL_DISCLAIMER}[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """WeirdClauses root command."""
    pass


def _check_model_cached(model_name: str) -> tuple[bool, str]:
    """Check if model is present in local cache without attempting network download."""
    try:
        from transformers import AutoConfig

        AutoConfig.from_pretrained(model_name, local_files_only=True)
        return True, "cached locally"
    except (OSError, ValueError, Exception) as exc:
        return False, f"not downloaded yet ({type(exc).__name__})"


def _check_cache_dir(cache_path: Path) -> tuple[bool, str]:
    """Verify that the cache directory exists or can be created and is writable."""
    try:
        cache_path.mkdir(parents=True, exist_ok=True)
        test_file = cache_path / ".doctor_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return True, f"writable ({cache_path})"
    except Exception as exc:
        return False, f"not writable: {exc}"


@app.command()
def doctor() -> None:
    """Diagnose local environment, dependencies, and model cache status."""
    console.print(
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

    all_critical_ok = True

    # 1. Python version check
    py_ver = sys.version_info
    py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver >= (3, 11):
        table.add_row("Python Version", "[green]PASS[/green]", f"{py_ver_str} (>= 3.11 required)")
    else:
        table.add_row("Python Version", "[red]FAIL[/red]", f"{py_ver_str} (requires >= 3.11)")
        all_critical_ok = False

    # 2. PyTorch import check
    try:
        import torch

        torch_ver = torch.__version__
        cuda_avail = torch.cuda.is_available()
        table.add_row(
            "PyTorch",
            "[green]PASS[/green]",
            f"v{torch_ver} (CUDA available: {cuda_avail}, configured device: {settings.device})",
        )
    except ImportError as exc:
        table.add_row("PyTorch", "[red]FAIL[/red]", f"Cannot import torch: {exc}")
        all_critical_ok = False

    # 3. Transformers import check
    try:
        import transformers

        table.add_row("Transformers", "[green]PASS[/green]", f"v{transformers.__version__}")
    except ImportError as exc:
        table.add_row("Transformers", "[red]FAIL[/red]", f"Cannot import transformers: {exc}")
        all_critical_ok = False

    # 4. Cache directory check
    cache_ok, cache_msg = _check_cache_dir(settings.cache_dir)
    if cache_ok:
        table.add_row("Cache Directory", "[green]PASS[/green]", cache_msg)
    else:
        table.add_row("Cache Directory", "[red]FAIL[/red]", cache_msg)
        all_critical_ok = False

    # 5. Configured LM Model check (local cache check)
    lm_cached, lm_msg = _check_model_cached(settings.lm_model)
    lm_status = "[green]CACHED[/green]" if lm_cached else "[yellow]NOT DOWNLOADED[/yellow]"
    table.add_row(f"LM Model ({settings.lm_model})", lm_status, lm_msg)

    # 6. Configured Embedding Model check (local cache check)
    embed_cached, embed_msg = _check_model_cached(settings.embed_model)
    embed_status = "[green]CACHED[/green]" if embed_cached else "[yellow]NOT DOWNLOADED[/yellow]"
    table.add_row(f"Embed Model ({settings.embed_model})", embed_status, embed_msg)

    # 7. Baseline Directory check
    baseline_exists = settings.baseline_dir.exists()
    baseline_status = "[green]FOUND[/green]" if baseline_exists else "[yellow]MISSING[/yellow]"
    table.add_row(
        "Baseline Pack Dir",
        baseline_status,
        str(settings.baseline_dir),
    )

    console.print(table)

    if not all_critical_ok:
        console.print("[bold red]Critical environment checks failed. Please see above.[/bold red]")
        raise typer.Exit(code=1)

    console.print(
        "[bold green]System is ready.[/bold green] "
        "Models not cached yet will be fetched on first run, "
        "or run with [bold cyan]--mock[/bold cyan] for instant offline execution."
    )


if __name__ == "__main__":
    app()
