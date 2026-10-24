"""CLI interface for WeirdClauses."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from weirdclauses import LEGAL_DISCLAIMER, __version__
from weirdclauses.config import settings
from weirdclauses.ingest import load_text
from weirdclauses.lm import get_surprisal_engine
from weirdclauses.scoring import score_clauses
from weirdclauses.segment import segment_clauses

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
    try:
        from transformers import AutoConfig

        AutoConfig.from_pretrained(model_name, local_files_only=True)
        return True, "cached locally"
    except (OSError, ValueError, Exception) as exc:
        return False, f"not downloaded yet ({type(exc).__name__})"


def _check_cache_dir(cache_path: Path) -> tuple[bool, str]:
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

    py_ver = sys.version_info
    py_ver_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
    if py_ver >= (3, 11):
        table.add_row("Python Version", "[green]PASS[/green]", f"{py_ver_str} (>= 3.11 required)")
    else:
        table.add_row("Python Version", "[red]FAIL[/red]", f"{py_ver_str} (requires >= 3.11)")
        all_critical_ok = False

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

    try:
        import transformers

        table.add_row("Transformers", "[green]PASS[/green]", f"v{transformers.__version__}")
    except ImportError as exc:
        table.add_row("Transformers", "[red]FAIL[/red]", f"Cannot import transformers: {exc}")
        all_critical_ok = False

    cache_ok, cache_msg = _check_cache_dir(settings.cache_dir)
    table.add_row(
        "Cache Directory",
        "[green]PASS[/green]" if cache_ok else "[red]FAIL[/red]",
        cache_msg,
    )
    if not cache_ok:
        all_critical_ok = False

    lm_cached, lm_msg = _check_model_cached(settings.lm_model)
    lm_status = "[green]CACHED[/green]" if lm_cached else "[yellow]NOT DOWNLOADED[/yellow]"
    table.add_row(f"LM Model ({settings.lm_model})", lm_status, lm_msg)

    embed_cached, embed_msg = _check_model_cached(settings.embed_model)
    embed_status = "[green]CACHED[/green]" if embed_cached else "[yellow]NOT DOWNLOADED[/yellow]"
    table.add_row(f"Embed Model ({settings.embed_model})", embed_status, embed_msg)

    baseline_status = (
        "[green]FOUND[/green]" if settings.baseline_dir.exists() else "[yellow]MISSING[/yellow]"
    )
    table.add_row("Baseline Pack Dir", baseline_status, str(settings.baseline_dir))

    console.print(table)
    if not all_critical_ok:
        console.print("[bold red]Critical environment checks failed. Please see above.[/bold red]")
        raise typer.Exit(code=1)

    console.print(
        "[bold green]System is ready.[/bold green] "
        "Models not cached yet will be fetched on first run, "
        "or run with [bold cyan]--mock[/bold cyan] for instant offline execution."
    )


@app.command()
def score(
    file: Annotated[Path, typer.Argument(help="Path to agreement file (.txt, .md, .docx, .pdf)")],
    aggregator: Annotated[
        str, typer.Option("--aggregator", "-a", help="Aggregator: mean, topq, max")
    ] = "topq",
    top: Annotated[int, typer.Option("--top", "-n", help="Top clauses to show")] = 10,
    mock: Annotated[bool, typer.Option("--mock", help="Use deterministic FakeLM")] = False,
    device: Annotated[str | None, typer.Option("--device", "-d", help="Device (cpu, cuda)")] = None,
) -> None:
    """Score and rank agreement clauses by language model surprisal."""
    console.print(
        Panel.fit(
            f"[bold yellow]{LEGAL_DISCLAIMER}[/bold yellow]",
            title="[bold red]Legal Disclaimer[/bold red]",
            border_style="yellow",
        )
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Ingesting document...", total=3)
        text = load_text(file)
        progress.advance(task)

        progress.update(task, description="[cyan]Segmenting clauses...")
        clauses = segment_clauses(text)
        progress.advance(task)

        progress.update(task, description="[cyan]Computing token surprisal (slow & steady)...")
        engine = get_surprisal_engine(mock=mock, device=device)
        surprisals = engine.token_surprisals(text)
        progress.advance(task)

    scored = score_clauses(clauses, surprisals, aggregator=aggregator)
    total_clauses = len([c for c in clauses if c.kind == "clause"])

    table = Table(
        title=f"WeirdClauses Ranking ({total_clauses} clauses | Aggregator: {aggregator})",
        show_lines=True,
    )
    table.add_column("Rank", style="bold cyan", justify="right", width=5)
    table.add_column("Score (bits)", justify="right", style="bold green", width=12)
    table.add_column("Z-Score", justify="right", style="bold yellow", width=8)
    table.add_column("Tokens", justify="right", width=6)
    table.add_column("Section / Heading", style="bold magenta", width=22)
    table.add_column("Clause Snippet", ratio=1)

    display_count = min(top, len(scored))
    for rank, sc in enumerate(scored[:display_count], start=1):
        heading = sc.clause.parent_heading or "(No heading)"
        snippet = sc.clause.content
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        table.add_row(
            str(rank),
            f"{sc.score:.2f}",
            f"{sc.z_score:+.2f}",
            str(sc.token_count),
            heading,
            snippet,
        )

    console.print(table)
    console.print(
        f"[dim]Showing top {display_count} of {len(scored)} clauses. {LEGAL_DISCLAIMER}[/dim]"
    )


if __name__ == "__main__":
    app()
