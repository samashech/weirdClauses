"""Core analysis pipeline coordinating ingestion, segmentation, facts, and surprisal."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

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
