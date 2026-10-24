"""Generate clean SVG comparison charts for benchmark evaluation results."""

from __future__ import annotations

from pathlib import Path

from eval.metrics import EvaluationReport


def generate_benchmark_svg(
    reports: list[EvaluationReport],
    output_path: Path,
    title: str = "WeirdClauses Benchmark: Ranker Comparison",
) -> None:
    """Generate a clean SVG bar chart comparing rankers across benchmark metrics."""
    # Dimensions
    n_rankers = len(reports)
    bar_height = 18
    group_gap = 14
    group_height = 3 * bar_height + group_gap
    margin_top = 70
    margin_left = 220
    margin_right = 160
    chart_width = 460
    total_width = margin_left + chart_width + margin_right
    total_height = margin_top + n_rankers * group_height + 80

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} {total_height}" '
        f'width="{total_width}" height="{total_height}" style="background:#ffffff; '
        f'font-family:system-ui,-apple-system,sans-serif;">',
        f'  <text x="{margin_left}" y="32" font-size="18" font-weight="700" '
        f'fill="#0f172a">{title}</text>',
        f'  <text x="{margin_left}" y="52" font-size="12" fill="#64748b">'
        f"Evaluated on 100 synthetic leases (292 planted unusual clauses) with 95% bootstrap CIs"
        f"</text>",
    ]

    # Legend
    legend_y = margin_top - 12
    legend_items = [
        (0, "#2563eb", "Recall@10%"),
        (120, "#10b981", "Percentile Rank"),
        (260, "#f59e0b", "MRR"),
    ]
    for offset, color, label in legend_items:
        lx = margin_left + offset
        svg_lines.append(
            f'  <rect x="{lx}" y="{legend_y}" width="12" height="12" fill="{color}" rx="2" />'
        )
        svg_lines.append(
            f'  <text x="{lx + 18}" y="{legend_y + 10}" font-size="11" '
            f'fill="#334155">{label}</text>'
        )

    # Grid lines and X-axis ticks (0.0 to 1.0)
    for tick in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        x = margin_left + int(tick * chart_width)
        svg_lines.append(
            f'  <line x1="{x}" y1="{margin_top + 10}" x2="{x}" '
            f'y2="{margin_top + n_rankers * group_height}" stroke="#e2e8f0" stroke-width="1" />'
        )
        svg_lines.append(
            f'  <text x="{x}" y="{margin_top + n_rankers * group_height + 20}" font-size="11" '
            f'fill="#64748b" text-anchor="middle">{tick:.1f}</text>'
        )

    # Render groups for each ranker
    colors = ["#2563eb", "#10b981", "#f59e0b"]
    for i, rep in enumerate(reports):
        gy = margin_top + 15 + i * group_height

        # Ranker label
        display_name = rep.ranker_name
        svg_lines.append(
            f'  <text x="{margin_left - 12}" y="{gy + 28}" font-size="12" font-weight="600" '
            f'fill="#0f172a" text-anchor="end">{display_name}</text>'
        )

        metrics = [rep.recall_at_10, rep.mean_percentile_rank, rep.mrr]
        for m_idx, met in enumerate(metrics):
            by = gy + m_idx * bar_height
            bw = max(2, int(met.mean * chart_width))
            color = colors[m_idx]

            # Bar
            svg_lines.append(
                f'  <rect x="{margin_left}" y="{by}" width="{bw}" height="{bar_height - 3}" '
                f'fill="{color}" rx="2" opacity="0.9" />'
            )

            # Error bar line (CI lower to upper)
            ci_x1 = margin_left + int(met.ci_lower * chart_width)
            ci_x2 = margin_left + int(met.ci_upper * chart_width)
            mid_y = by + (bar_height - 3) / 2
            svg_lines.append(
                f'  <line x1="{ci_x1}" y1="{mid_y}" x2="{ci_x2}" y2="{mid_y}" '
                f'stroke="#0f172a" stroke-width="1.5" />'
            )
            svg_lines.append(
                f'  <line x1="{ci_x1}" y1="{mid_y - 3}" x2="{ci_x1}" y2="{mid_y + 3}" '
                f'stroke="#0f172a" stroke-width="1.5" />'
            )
            svg_lines.append(
                f'  <line x1="{ci_x2}" y1="{mid_y - 3}" x2="{ci_x2}" y2="{mid_y + 3}" '
                f'stroke="#0f172a" stroke-width="1.5" />'
            )

            # Value text
            val_x = margin_left + bw + 6
            svg_lines.append(
                f'  <text x="{val_x}" y="{mid_y + 4}" font-size="10" fill="#334155">'
                f"{met.mean:.3f}</text>"
            )

    svg_lines.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg_lines), encoding="utf-8")
