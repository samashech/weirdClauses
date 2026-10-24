"""Self-contained HTML report generator with character-accurate heat maps and no external assets."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from weirdclauses import LEGAL_DISCLAIMER


def _render_tokens_heat_map(clause: dict[str, Any]) -> str:
    """Render clause text with character-accurate token surprisal highlights."""
    text, tokens = clause.get("text", ""), clause.get("tokens", [])
    facts, c_start = clause.get("facts", []), clause.get("start", 0)
    if not tokens:
        return html.escape(text)

    parts: list[str] = []
    curr = c_start

    for tok in sorted(tokens, key=lambda t: t["start"]):
        s, e, bits = tok["start"], tok["end"], tok["bits"]
        if s > curr and curr >= c_start:
            parts.append(html.escape(text[curr - c_start : s - c_start]))
        alpha = min(0.85, max(0.08, (bits - 2.5) / 12.0))
        inside = next((f for f in facts if max(s, f["start"]) < min(e, f["end"])), None)
        f_style = "border-bottom: 2px solid var(--accent);" if inside else ""
        title = f"{bits:.2f} bits" + (f" | [rule-based: {inside['kind']}]" if inside else "")
        tok_txt = html.escape(text[s - c_start : e - c_start])
        style = f"background-color: rgba(239, 68, 68, {alpha:.2f}); {f_style}"
        parts.append(f'<span class="tok" style="{style}" title="{title}">{tok_txt}</span>')
        curr = max(curr, e)

    c_end = clause.get("end", c_start + len(text))
    if curr < c_end:
        parts.append(html.escape(text[curr - c_start :]))
    return "".join(parts)


def _css_styles() -> str:
    return """
:root {
  --bg: #f8fafc; --surface: #fff; --surface-alt: #f1f5f9; --text: #0f172a;
  --text-muted: #64748b; --border: #e2e8f0; --accent: #2563eb;
  --warn-bg: #fffbeb; --warn-border: #fcd34d; --warn-text: #92400e;
}
[data-theme='dark'] {
  --bg: #0f172a; --surface: #1e293b; --surface-alt: #334155; --text: #f8fafc;
  --text-muted: #94a3b8; --border: #334155; --accent: #38bdf8;
  --warn-bg: #451a03; --warn-border: #78350f; --warn-text: #fde68a;
}
body {
  margin: 0; padding: 0; background: var(--bg); color: var(--text);
  font-family: system-ui, -apple-system, sans-serif; line-height: 1.6;
}
.container { max-width: 1040px; margin: 0 auto; padding: 24px; }
header { display: flex; justify-content: space-between; margin-bottom: 20px; }
.btn-theme {
  background: var(--surface-alt); color: var(--text); border: 1px solid var(--border);
  padding: 6px 12px; border-radius: 6px; cursor: pointer;
}
.disclaimer-banner {
  background: var(--warn-bg); border: 1px solid var(--warn-border); color: var(--warn-text);
  padding: 12px 16px; border-radius: 8px; margin-bottom: 20px;
}
.meta-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;
  margin-bottom: 24px; background: var(--surface); padding: 14px;
  border: 1px solid var(--border); border-radius: 8px;
}
.meta-box span { display: block; font-size: 0.75rem; color: var(--text-muted); }
.meta-box strong { font-size: 0.9rem; }
h2 { border-bottom: 2px solid var(--border); padding-bottom: 6px; margin-top: 32px; }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px; margin-bottom: 12px;
}
.card-header { display: flex; justify-content: space-between; gap: 8px; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; }
.badge-rank { background: #fee2e2; color: #991b1b; } .badge-rule { background: #e0f2fe; }
.badge-fact { background: var(--surface-alt); } .badge-money { background: #dcfce7; }
.badge-percentage { background: #f3e8ff; } .badge-notice_period { background: #fef3c7; }
.badge-auto_renewal { background: #ffe4e6; color: #9f1239; }
.clause-quote { font-family: Georgia, serif; font-size: 1rem; margin: 10px 0 6px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { padding: 8px 12px; border: 1px solid var(--border); text-align: left; }
th { background: var(--surface-alt); }
.clause-box {
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  padding: 14px; margin-bottom: 12px;
}
.clause-box-header {
  display: flex; justify-content: space-between; border-bottom: 1px solid var(--border);
  padding-bottom: 6px; margin-bottom: 8px; font-size: 0.85rem;
}
.clause-content { font-family: monospace; font-size: 0.9rem; line-height: 1.7; }
.tok { border-radius: 2px; padding: 2px 0; }
.doc-heading { color: var(--accent); margin-top: 20px; }
.doc-frame { font-style: italic; color: var(--text-muted); margin: 10px 0; }
footer {
  text-align: center; margin-top: 40px; padding-top: 20px;
  border-top: 1px solid var(--border); font-size: 0.85rem; color: var(--text-muted);
}
"""


def render_html_report(report: dict[str, Any]) -> str:
    """Generate self-contained HTML report with light/dark mode and zero external assets."""
    doc, models = report["document"], report["models"]
    clauses, key_facts = report["clauses"], report.get("key_facts", [])

    scored = sorted(
        [c for c in clauses if c.get("score") is not None], key=lambda c: c["score"], reverse=True
    )
    top_clauses = scored[: max(1, round(len(scored) * 0.25))]

    top_cards: list[str] = []
    for sc in top_clauses:
        nearest = sc.get("nearest_matches", [])
        m_title, m_sim = (
            (nearest[0]["title"], f"{nearest[0]['similarity']:.2f}") if nearest else ("None", "-")
        )
        gain_str = f"{sc.get('gain', 0.0):+.2f} bits" if sc.get("gain") is not None else "-"
        heading_text = html.escape(sc.get("parent_heading") or f"Clause {sc['id']}")
        score_info = (
            f"Score: <strong>{sc['score']:.2f} bits</strong> (Z: {sc['z_score']:+.2f}) "
            f"| Gain: {gain_str}"
        )
        top_cards.append(f"""
        <div class="card">
          <div class="card-header">
            <div><span class="badge badge-rank">Rank #{sc.get("rank", "-")}</span>
            <strong>{heading_text}</strong></div>
            <div>{score_info}</div>
          </div>
          <p class="clause-quote">{html.escape(sc.get("content") or sc.get("text") or "")}</p>
          <div style="font-size:0.82rem; color:var(--text-muted);">
            Nearest standard: {html.escape(m_title)} (sim: {m_sim})
          </div>
        </div>""")

    facts_rows: list[str] = [
        f'<tr><td><span class="badge badge-fact badge-{html.escape(f["kind"])}">'
        f"{html.escape(f['kind'])}</span></td><td>{html.escape(f['value'])}</td>"
        f"<td>Clause #{f.get('clause_id', '-')}</td>"
        '<td><span class="badge badge-rule">rule-based</span></td></tr>'
        for f in key_facts
    ]

    clause_blocks: list[str] = []
    for c in clauses:
        c_id, c_kind = c["id"], c.get("kind", "clause")
        heat_text = _render_tokens_heat_map(c)
        if c_kind == "heading":
            clause_blocks.append(f'<h3 class="doc-heading" id="c-{c_id}">{heat_text}</h3>')
        elif c_kind == "frame":
            clause_blocks.append(f'<div class="doc-frame" id="c-{c_id}">{heat_text}</div>')
        else:
            r_badge = (
                f'<span class="badge badge-rank">Rank #{c["rank"]}</span> ' if c.get("rank") else ""
            )
            s_meta = (
                f"Score: <strong>{c['score']:.2f} bits</strong>"
                if c.get("score") is not None
                else ""
            )
            clause_blocks.append(f"""
            <div class="clause-box" id="c-{c_id}">
              <div class="clause-box-header">
                <div>{r_badge}<span>{html.escape(c.get("parent_heading") or "")}</span></div>
                <div>{s_meta}</div>
              </div>
              <div class="clause-content">{heat_text}</div>
            </div>""")

    facts_body = (
        "".join(facts_rows) if facts_rows else '<tr><td colspan="4">No facts extracted</td></tr>'
    )
    doc_blocks_count = f"{doc['char_count']} chars ({doc['clause_count']} blocks)"
    doc_name = html.escape(doc["file_name"])
    lm_model_name = html.escape(models["lm_model"])
    mode_summary = f"{models['mode']} ({models['aggregator']})"
    ver = report.get("version", "0.1.0")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WeirdClauses Report - {doc_name}</title>
<style>{_css_styles()}</style>
</head>
<body>
<div class="container">
  <header>
    <div><h1 style="margin:0; font-size:1.6rem;">WeirdClauses</h1>
    <span style="font-size:0.82rem; color:var(--text-muted);">v{ver}</span></div>
    <button class="btn-theme" onclick="toggleTheme()">🌓 Theme</button>
  </header>
  <div class="disclaimer-banner">{LEGAL_DISCLAIMER}</div>
  <div class="meta-grid">
    <div class="meta-box"><span>Document</span><strong>{doc_name}</strong></div>
    <div class="meta-box"><span>Length</span><strong>{doc_blocks_count}</strong></div>
    <div class="meta-box"><span>Model</span><strong>{lm_model_name}</strong></div>
    <div class="meta-box"><span>Mode</span><strong>{mode_summary}</strong></div>
  </div>
  <h2>Read These First (Most Unusual Clauses)</h2>
  {"".join(top_cards)}
  <h2>Key Facts Table (Rule-Based Extraction)</h2>
  <p style="font-size:0.85rem; color:var(--text-muted);">
    Extracted using deterministic pattern matching (regex), NOT by the language model.
  </p>
  <table>
    <thead>
      <tr>
        <th>Category</th><th>Extracted Value</th><th>Clause Reference</th><th>Source Layer</th>
      </tr>
    </thead>
    <tbody>{facts_body}</tbody>
  </table>
  <h2>Full Document & Heat-Mapped Surprisal</h2>
  <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:12px;">
    Token background intensity = surprisal (-log2 p). Underlined = rule-based facts.
  </div>
  {"".join(clause_blocks)}
  <footer>
    <div class="disclaimer-banner">{LEGAL_DISCLAIMER}</div>
    WeirdClauses - Privacy-first, local contract surprisal analysis. Zero text leaves the machine.
  </footer>
</div>
<script>
function toggleTheme() {{
  const cur = document.documentElement.getAttribute('data-theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
}}
</script>
</body>
</html>"""


def export_html(report: dict[str, Any], path: Path | str | None = None) -> str:
    """Render and optionally save the self-contained HTML report."""
    content = render_html_report(report)
    if path is not None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
    return content
