"""CLI interface for WeirdClauses."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from weirdclauses import LEGAL_DISCLAIMER, __version__
from weirdclauses.config import settings
from weirdclauses.doctor import run_doctor
from weirdclauses.pipeline import run_pipeline
from weirdclauses.report import build_report, export_html, export_json, export_markdown

app = typer.Typer(
    name="weirdclauses",
    help="WeirdClauses: Local, offline contract clause surprisal and anomaly ranking tool.",
    add_completion=False,
)
console = Console()


def _parse_top_count(top_spec: str, total_count: int) -> int:
    """Parse top specifier like '10%' or '5' into an integer count."""
    clean = top_spec.strip()
    if clean.endswith("%"):
        pct = float(clean[:-1].strip())
        return max(1, math.ceil(total_count * (pct / 100.0)))
    return max(1, int(clean))


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


@app.command()
def doctor() -> None:
    """Diagnose local environment, dependencies, and model cache status."""
    if not run_doctor(console):
        raise typer.Exit(code=1)


@app.command()
def score(
    file: Annotated[Path, typer.Argument(help="Path to agreement file (.txt, .md, .docx, .pdf)")],
    aggregator: Annotated[
        str, typer.Option("--aggregator", "-a", help="Aggregator: mean, topq, max")
    ] = "topq",
    mode: Annotated[
        str, typer.Option("--mode", "-m", help="Mode: 'raw' or 'conditional'")
    ] = "conditional",
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
        task = progress.add_task("[cyan]Starting analysis...", total=4)

        def step_cb(msg: str) -> None:
            progress.update(task, description=f"[cyan]{msg}")
            progress.advance(task)

        res = run_pipeline(
            file, mode=mode, aggregator=aggregator, mock=mock, device=device, on_step=step_cb
        )

    title = (
        f"WeirdClauses Ranking ({len(res.scored_clauses)} clauses "
        f"| Mode: {res.mode} | Agg: {res.aggregator})"
    )
    table = Table(title=title, show_lines=True)
    table.add_column("Rank", style="bold cyan", justify="right", width=5)
    table.add_column("Score (bits)", justify="right", style="bold green", width=12)
    table.add_column("Z-Score", justify="right", style="bold yellow", width=8)
    if res.mode == "conditional":
        table.add_column("Gain", justify="right", style="bold magenta", width=7)
    table.add_column("Sim", justify="right", width=6)
    table.add_column("Nearest Match", style="cyan", width=20)
    table.add_column("Section / Heading", style="bold magenta", width=22)
    table.add_column("Clause Snippet", ratio=1)

    display_count = min(top, len(res.scored_clauses))
    for rank, sc in enumerate(res.scored_clauses[:display_count], start=1):
        heading = sc.clause.parent_heading or "(No heading)"
        match_title = sc.nearest_matches[0].clause.title if sc.nearest_matches else "-"
        sim_str = f"{sc.nearest_similarity:.2f}" if sc.nearest_similarity is not None else "-"
        snippet = (
            sc.clause.content[:117] + "..." if len(sc.clause.content) > 120 else sc.clause.content
        )
        row = [str(rank), f"{sc.score:.2f}", f"{sc.z_score:+.2f}"]
        if res.mode == "conditional":
            row.append(f"{sc.gain:+.2f}" if sc.gain is not None else "-")
        row.extend([sim_str, match_title, heading, snippet])
        table.add_row(*row)

    console.print(table)
    console.print(f"[dim]Showing top {display_count} clauses. {LEGAL_DISCLAIMER}[/dim]")


@app.command()
def review(
    file: Annotated[Path, typer.Argument(help="Path to agreement file (.txt, .md, .docx, .pdf)")],
    out: Annotated[
        Path, typer.Option("--out", "-o", help="Output report path (.html, .md, .json)")
    ] = Path("report.html"),
    top: Annotated[
        str, typer.Option("--top", "-n", help="Top clauses (e.g. '10%' or '5')")
    ] = "10%",
    aggregator: Annotated[
        str, typer.Option("--aggregator", "-a", help="Aggregator: mean, topq, max")
    ] = "topq",
    mode: Annotated[
        str, typer.Option("--mode", "-m", help="Mode: 'raw' or 'conditional'")
    ] = "conditional",
    mock: Annotated[bool, typer.Option("--mock", help="Use deterministic FakeLM")] = False,
    device: Annotated[str | None, typer.Option("--device", "-d", help="Device (cpu, cuda)")] = None,
) -> None:
    """Analyze contract, extract rule-based facts, rank anomalies, and export interactive report."""
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
        task = progress.add_task("[cyan]Starting analysis...", total=5)

        def step_cb(msg: str) -> None:
            progress.update(task, description=f"[cyan]{msg}")
            progress.advance(task)

        res = run_pipeline(
            file, mode=mode, aggregator=aggregator, mock=mock, device=device, on_step=step_cb
        )

        progress.update(task, description="[cyan]Building and validating export report...")
        report_data = build_report(
            raw_text=res.text,
            clauses=res.clauses,
            scored_clauses=res.scored_clauses,
            facts_by_clause=res.facts_by_clause,
            file_path=file,
            lm_model="mock-lm" if mock else settings.lm_model,
            embed_model="mock-embed" if mock else settings.embed_model,
            device=device or settings.device,
            mode=res.mode,
            aggregator=res.aggregator,
        )

        out_suffix = out.suffix.lower()
        if out_suffix == ".md":
            export_markdown(report_data, path=out)
        elif out_suffix == ".json":
            export_json(report_data, path=out)
        else:
            export_html(report_data, path=out)
        progress.advance(task)

    num_scored = len(res.scored_clauses)
    num_facts = sum(len(f) for f in res.facts_by_clause.values())
    top_limit = _parse_top_count(top, num_scored)

    console.print(
        f"\n[bold green]✓[/bold green] Analysis complete: "
        f"[bold]{num_scored}[/bold] clauses evaluated, "
        f"[bold cyan]{num_facts}[/bold cyan] rule-based facts extracted."
    )
    console.print(
        f"[bold green]✓[/bold green] Report saved to [bold underline]{out}[/bold underline]\n"
    )

    top_table = Table(
        title=f"Top Unusual Clauses (Read These First — Top {top_limit} of {num_scored})",
        show_lines=True,
    )
    top_table.add_column("Rank", justify="right", style="bold cyan", width=5)
    top_table.add_column("Score", justify="right", style="bold green", width=10)
    top_table.add_column("Z-Score", justify="right", style="bold yellow", width=8)
    top_table.add_column("Nearest Standard", style="cyan", width=24)
    top_table.add_column("Clause Snippet", ratio=1)

    for rank, sc in enumerate(res.scored_clauses[:top_limit], start=1):
        m_title = sc.nearest_matches[0].clause.title if sc.nearest_matches else "-"
        snippet = (
            sc.clause.content[:100] + "..." if len(sc.clause.content) > 100 else sc.clause.content
        )
        top_table.add_row(str(rank), f"{sc.score:.2f} b", f"{sc.z_score:+.2f}", m_title, snippet)

    console.print(top_table)
    console.print(f"[dim]{LEGAL_DISCLAIMER}[/dim]\n")


if __name__ == "__main__":
    app()
