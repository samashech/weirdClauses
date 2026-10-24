# WeirdClauses

> **DISCLAIMER: WeirdClauses is NOT legal advice.** It is an open-source research and text-analysis tool designed to highlight unusual phrasing and candidate anomalies in contracts. It does not provide legal interpretation, counsel, representation, or warranty. Always consult a qualified attorney for legal guidance.

---

**WeirdClauses** is a local, privacy-first contract exploration tool built for the DEV Hacktoberfest Open-Source AI Challenge (Theme: *"Slow and Steady"*, rewarding laziness). 

Instead of reading repetitive 25-page residential leases line by line, WeirdClauses segments agreements into clauses, scores them by **linguistic surprisal** ($-\log_2 P(\text{token} \mid \text{context})$) using an open-weight base language model, contrasts them against a corpus of standard baseline terms, and ranks them by unusualness. The reader can skim the boring majority and slow down only on the weird clauses.

Zero document text, tokens, or metadata ever leave your machine. No API keys, no telemetry, no cloud dependencies.

---

## Key Features

- **Local Open-Weight LM Surprisal Engine**: Teacher-forced token log-probability calculation using base causal language models (defaults to `Qwen/Qwen2.5-0.5B`, also tested with Gemma-family base models) via Hugging Face Transformers.
- **Context-Conditioned Scoring**: Semantic baseline retrieval (via `sentence-transformers/all-MiniLM-L6-v2`) compares each clause against standard practices to compute contextual surprisal gain.
- **Lossless Character-Accurate Segmentation**: Maps tokens and extracted spans to the exact original characters with zero gaps or overlaps.
- **Rule-Based Fact Extraction**: Regex-based extraction of money amounts, percentages, notice periods, dates, durations, and auto-renewal triggers, explicitly labeled `[rule-based]` so users never mistake heuristic extraction for model inferences.
- **Zero-Network Interactive Web UI & HTML Reports**: Self-contained single-page web explorer (`weirdclauses serve`) and stand-alone HTML report generator (`weirdclauses review`) featuring interactive token heat-maps, dark/light modes, and zero external CDNs.
- **Reproducible Evaluation Benchmark**: 100-document synthetic lease benchmark with 95% bootstrap confidence intervals (`make eval`).
- **Instant `--mock` Mode**: Fully deterministic test mode using synthetic precomputed tables for fast offline testing and zero-download reviewer demonstrations.

---

## Architecture

```
Agreement (.txt, .md, .docx, .pdf)
               │
               ▼
   [ Lossless Segmentation ] ──► Exact Character Spans
               │
      ┌────────┴────────────────────────┬────────────────────────┐
      ▼                                 ▼                        ▼
[ Token Surprisal ]           [ Standard Baseline ]      [ Rule-Based Facts ]
Teacher-Forced Forward Pass   Sentence Embeddings        Regex Pattern Matcher
(Causal LM: Qwen2.5-0.5B)     (all-MiniLM-L6-v2)         (Money, Dates, Periods)
      │                                 │                        │
      └────────┬────────────────────────┘                        │
               ▼                                                 │
     [ Clause Aggregator ]                                       │
     Top-Quartile Mean (topq)                                    │
     Z-Score Normalization                                       │
               │                                                 │
               └────────────────────────┬────────────────────────┘
                                        ▼
                             [ Interactive Reports ]
                       CLI Table / Offline HTML / Web UI
```

---

## Installation

### Prerequisites
- Python 3.11+
- PyTorch 2.0+

```bash
git clone https://github.com/your-username/weirdclauses.git
cd weirdclauses

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package with developer dependencies
pip install -e ".[dev]"
```

---

## Configuration

WeirdClauses is configured entirely via environment variables (or `.env` file):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `WC_LM_MODEL` | `Qwen/Qwen2.5-0.5B` | Open-weight causal LM checkpoint on Hugging Face |
| `WC_EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Sentence transformer embedding model |
| `WC_CACHE_DIR` | `~/.cache/weirdclauses` | Local disk cache for surprisals and embeddings |
| `WC_DEVICE` | `cpu` | Execution device (`cpu`, `cuda`, `mps`) |
| `WC_BASELINE_DIR`| `baseline_packs/rental` | Directory of markdown baseline clauses |
| `WC_MOCK` | `0` | Enable fast deterministic mock mode without downloading models |
| `WC_PUBLIC_DEMO` | `0` | Limit analysis payload length to 50,000 characters for hosted demos |

---

## CLI Usage

### System Diagnostics
Verify dependencies, model cache, and environment readiness:
```bash
weirdclauses doctor
```

### Rank Agreement Clauses
Print a ranked terminal table of the most unusual clauses in an agreement:
```bash
weirdclauses score samples/unusual_rental.txt --mode conditional --aggregator topq --top 10
```

### Generate Standalone Reports
Export a self-contained offline HTML or Markdown report:
```bash
weirdclauses review samples/unusual_rental.txt --out report.html --top 10%
```

### Interactive Local Web Explorer
Start the zero-telemetry local single-page web application:
```bash
weirdclauses serve --port 8000 --open
```

---

## Evaluation Benchmark

WeirdClauses includes a rigorous benchmark evaluating rankers across 100 synthetic agreements (1,516 total clauses, 292 planted unusual clauses) using Recall@10%, Mean Percentile Rank, and Mean Reciprocal Rank (MRR) with 1,000 bootstrap resamples:

```bash
make eval
```

Evaluation outputs are persisted to:
- `eval/results/benchmark_table.md`
- `eval/results/benchmark_summary.json`
- `eval/results/benchmark_chart.svg`

For detailed discussions of evaluation boundaries and real-world testing, see:
- [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md)
- [`docs/CASE_STUDY.md`](docs/CASE_STUDY.md)

---

## License

This project is licensed under the [MIT License](LICENSE).
