"""Report generator formatting ranked weird clauses and key facts with legal disclaimer."""

from __future__ import annotations

from typing import Any

from weirdclauses import LEGAL_DISCLAIMER


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
            lines.append(f"  - [{f.get('fact_type', 'fact')}] {f.get('value')}")

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
