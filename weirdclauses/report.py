"""Report generation and export module (JSON schema, Markdown, HTML)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from weirdclauses import LEGAL_DISCLAIMER, __version__
from weirdclauses.facts import ExtractedFact
from weirdclauses.report_html import export_html, render_html_report
from weirdclauses.scoring import ScoredClause
from weirdclauses.segment import Clause

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "docs" / "report.schema.json"


def build_report(
    raw_text: str,
    clauses: Sequence[Clause],
    scored_clauses: Sequence[ScoredClause],
    facts_by_clause: dict[int, list[ExtractedFact]],
    file_path: Path | str | None = None,
    lm_model: str = "mock-model",
    embed_model: str = "mock-embed",
    device: str | None = "cpu",
    mode: str = "conditional",
    aggregator: str = "topq",
) -> dict[str, Any]:
    """Construct full report dictionary conforming to the WeirdClauses JSON schema."""
    scored_map: dict[int, tuple[int, ScoredClause]] = {
        sc.clause.id: (rank, sc) for rank, sc in enumerate(scored_clauses, start=1)
    }

    clause_dicts: list[dict[str, Any]] = []
    for c in clauses:
        facts = [f.to_dict() for f in facts_by_clause.get(c.id, [])]
        rank, sc = scored_map.get(c.id, (None, None))

        tokens: list[dict[str, Any]] = []
        nearest_matches: list[dict[str, Any]] = []

        if sc is not None:
            tokens = [{"start": s, "end": e, "bits": round(b, 4)} for s, e, b in sc.tokens]
            nearest_matches = [
                {
                    "id": m.clause.file_name,
                    "title": m.clause.title,
                    "topic": m.clause.topic,
                    "similarity": round(m.similarity, 4),
                    "summary": m.clause.title,
                }
                for m in sc.nearest_matches
            ]

        clause_dicts.append(
            {
                "id": c.id,
                "text": c.text,
                "content": c.content,
                "start": c.start,
                "end": c.end,
                "kind": c.kind,
                "parent_heading": c.parent_heading,
                "rank": rank,
                "score": sc.score if sc else None,
                "z_score": sc.z_score if sc else None,
                "raw_surprisal": sc.raw_surprisal if sc else None,
                "conditional_surprisal": sc.conditional_surprisal if sc else None,
                "nearest_similarity": sc.nearest_similarity if sc else None,
                "gain": sc.gain if sc else None,
                "nearest_matches": nearest_matches,
                "tokens": tokens,
                "facts": facts,
            }
        )

    all_facts: list[dict[str, Any]] = []
    for c in clauses:
        for f in facts_by_clause.get(c.id, []):
            d = f.to_dict()
            d["clause_id"] = c.id
            all_facts.append(d)

    scores = [sc.score for sc in scored_clauses]
    sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    path_obj = Path(file_path) if file_path else None

    return {
        "version": __version__,
        "disclaimer": LEGAL_DISCLAIMER,
        "document": {
            "file_path": str(path_obj) if path_obj else None,
            "file_name": path_obj.name if path_obj else "unnamed_document",
            "char_count": len(raw_text),
            "clause_count": len(clauses),
            "sha256": sha256,
        },
        "models": {
            "lm_model": lm_model,
            "embed_model": embed_model,
            "device": device or "cpu",
            "mode": mode,
            "aggregator": aggregator,
        },
        "summary": {
            "total_clauses": len(clauses),
            "scored_clauses": len(scored_clauses),
            "key_facts_count": len(all_facts),
            "mean_score": round(sum(scores) / len(scores), 4) if scores else None,
            "max_score": round(max(scores), 4) if scores else None,
        },
        "clauses": clause_dicts,
        "key_facts": all_facts,
    }


def validate_report(report: dict[str, Any], schema_path: Path | None = None) -> None:
    """Validate report dict against the JSON schema."""
    import jsonschema

    target_schema = schema_path or SCHEMA_PATH
    schema_data = json.loads(target_schema.read_text(encoding="utf-8"))
    jsonschema.validate(instance=report, schema=schema_data)


def export_json(report: dict[str, Any], path: Path | str | None = None) -> str:
    """Serialize report dictionary to formatted JSON string, optionally writing to path."""
    content = json.dumps(report, indent=2, ensure_ascii=False)
    if path is not None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return content


def export_markdown(report: dict[str, Any], path: Path | str | None = None) -> str:
    """Format an analysis report as clean Markdown, optionally writing to path."""
    doc = report["document"]
    models = report["models"]
    clauses = report["clauses"]
    key_facts = report.get("key_facts", [])

    lines: list[str] = [
        f"# WeirdClauses Analysis Report: {doc['file_name']}",
        "",
        f"> **LEGAL DISCLAIMER**: {LEGAL_DISCLAIMER}",
        "",
        "## Document & Model Metadata",
        f"- **File**: `{doc['file_name']}` ({doc['char_count']} chars, "
        f"{doc['clause_count']} blocks)",
        f"- **SHA-256**: `{doc['sha256']}`",
        f"- **Models**: `{models['lm_model']}` / `{models['embed_model']}` "
        f"({models['mode']} mode, {models['aggregator']})",
        "",
        "## Key Facts (Rule-Based Extraction)",
        "> **Notice**: The facts below were extracted using "
        "deterministic pattern matching (regex), NOT by the language model.",
        "",
    ]

    if not key_facts:
        lines.append("*(No key facts detected)*")
    else:
        lines.extend(
            [
                "| Category | Extracted Value | Clause Reference | Source |",
                "| :--- | :--- | :--- | :--- |",
            ]
        )
        for f in key_facts:
            src = f.get("source_label", "rule-based")
            c_ref = f"Clause #{f.get('clause_id', '-')}"
            lines.append(f"| `{f['kind']}` | **{f['value']}** | {c_ref} | `{src}` |")

    scored = [c for c in clauses if c.get("score") is not None]
    scored.sort(key=lambda c: c["score"], reverse=True)
    top_n = max(1, round(len(scored) * 0.25))

    lines.extend(["", "## Read These First (Most Unusual Clauses)", ""])
    for sc in scored[:top_n]:
        nearest = sc.get("nearest_matches", [])
        m_title = nearest[0]["title"] if nearest else "-"
        m_sim = f"{nearest[0]['similarity']:.2f}" if nearest else "-"
        heading = sc.get("parent_heading") or f"Clause #{sc['id']}"
        gain_str = f"{sc.get('gain', 0.0):+.2f}" if sc.get("gain") is not None else "-"
        lines.append(f"### Rank #{sc.get('rank', '-')} — {heading}")
        score_line = (
            f"- **Surprisal Score**: `{sc['score']:.2f} bits` | "
            f"**Z-Score**: `{sc['z_score']:+.2f}` | **Gain**: `{gain_str}`"
        )
        lines.append(score_line)
        lines.append(f"- **Nearest Standard Clause**: *{m_title}* (similarity: {m_sim})")
        lines.append("")
        snippet = sc.get("content") or sc.get("text") or ""
        lines.append(f"> {snippet}")
        lines.append("")

    lines.extend(["---", f"> **LEGAL DISCLAIMER**: {LEGAL_DISCLAIMER}"])
    content = "\n".join(lines)
    if path is not None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return content


def format_text_report(ranked_clauses: list[dict[str, Any]], facts: list[dict[str, Any]]) -> str:
    """Format an analysis report with mandatory legal disclaimer."""
    lines: list[str] = [
        "=" * 80,
        "WEIRDCLAUSES ANALYSIS REPORT",
        f"{LEGAL_DISCLAIMER}",
        "=" * 80,
        "",
        "## Key Facts (Rule-Based Extraction)",
    ]
    if not facts:
        lines.append("  (None detected)")
    else:
        for f in facts:
            lines.append(f"  - [{f.get('fact_type', f.get('kind', 'fact'))}] {f.get('value')}")

    lines.extend(["", "## Ranked Clauses (Most Unusual First)"])
    if not ranked_clauses:
        lines.append("  (No clauses analyzed)")
    else:
        for rank, c in enumerate(ranked_clauses, start=1):
            score = c.get("score", 0.0)
            z_score = c.get("z_score", 0.0)
            text = c.get("text", "")
            lines.append(f"{rank}. [Score: {score:.2f} | Z: {z_score:+.2f}] {text}")

    lines.extend(["", "=" * 80, LEGAL_DISCLAIMER, "=" * 80])
    return "\n".join(lines)


__all__ = [
    "SCHEMA_PATH",
    "build_report",
    "export_html",
    "export_json",
    "export_markdown",
    "format_text_report",
    "render_html_report",
    "validate_report",
]
