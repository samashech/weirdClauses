"""Core analysis pipeline coordinating ingestion, segmentation, facts, and surprisal."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rich.table import Table

from weirdclauses.baseline import get_baseline_pack
from weirdclauses.facts import ExtractedFact, attach_facts_to_clauses
from weirdclauses.ingest import load_text
from weirdclauses.lm import get_surprisal_engine
from weirdclauses.scoring import ScoredClause, score_clauses
from weirdclauses.segment import Clause, segment_clauses


@dataclass
class PipelineResult:
    text: str
    clauses: list[Clause]
    scored_clauses: list[ScoredClause]
    facts_by_clause: dict[int, list[ExtractedFact]]
    mode: str
    aggregator: str


def run_pipeline(
    file: Path | str,
    mode: str = "conditional",
    aggregator: str = "topq",
    mock: bool = False,
    device: str | None = None,
    on_step: Callable[[str], None] | None = None,
) -> PipelineResult:
    """Run full analysis pipeline from document file to scored clauses and facts."""
    scoring_mode = "conditional" if mode.lower() in ("conditional", "cond") else "raw"

    if on_step:
        on_step("Ingesting and segmenting document...")
    text = load_text(file)
    clauses = segment_clauses(text)

    if on_step:
        on_step("Extracting rule-based key facts...")
    facts_by_clause = attach_facts_to_clauses(clauses)

    if on_step:
        on_step("Loading baseline standard corpus...")
    baseline_pack = get_baseline_pack(mock=mock)

    if on_step:
        on_step(f"Scoring clauses ({scoring_mode} mode, slow & steady)...")
    engine = get_surprisal_engine(mock=mock, device=device)
    surprisals = engine.token_surprisals(text)
    scored = score_clauses(
        clauses,
        surprisals,
        aggregator=aggregator,
        mode=scoring_mode,
        baseline_pack=baseline_pack,
        engine=engine,
    )

    return PipelineResult(
        text=text,
        clauses=clauses,
        scored_clauses=scored,
        facts_by_clause=facts_by_clause,
        mode=scoring_mode,
        aggregator=aggregator,
    )


def create_ranking_table(res: PipelineResult, top: int) -> tuple[Table, int]:
    """Create Rich table displaying full clause ranking."""
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
        m_title = sc.nearest_matches[0].clause.title if sc.nearest_matches else "-"
        sim_str = f"{sc.nearest_similarity:.2f}" if sc.nearest_similarity is not None else "-"
        snippet = (
            sc.clause.content[:117] + "..." if len(sc.clause.content) > 120 else sc.clause.content
        )
        row = [str(rank), f"{sc.score:.2f}", f"{sc.z_score:+.2f}"]
        if res.mode == "conditional":
            row.append(f"{sc.gain:+.2f}" if sc.gain is not None else "-")
        row.extend([sim_str, m_title, heading, snippet])
        table.add_row(*row)

    return table, display_count


def create_top_anomalies_table(res: PipelineResult, top_limit: int) -> Table:
    """Create Rich table displaying top anomaly summary cards."""
    num_scored = len(res.scored_clauses)
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

    return top_table
