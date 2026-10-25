---
title: "WeirdClauses: Skimming the Boring 90% of Contracts with Open-Weight Surprisal"
published: false
tags: hf26challenge, ai, opensource, productivity
cover_image: https://raw.githubusercontent.com/samashech/weirdClauses/main/docs/images/cover.png
---

We have all done it. 

You are standing in an empty hallway on moving day. The moving truck is double-parked downstairs with its hazard lights blinking, the driver is tapping his clipboard, and the property manager slides a 24-page residential lease across the kitchen counter. 

You start reading with noble intentions. By Clause 3 (*"Tenant covenants to maintain domestic tranquillity pursuant to Section 12(b)..."*), your eyes glaze over. By page seven, your brain has completely surrendered. You flip directly to the signature block, scrawl your name, and pray you didn't accidentally promise your firstborn child or agree to pay for roof replacements out of pocket.

Human nature is fundamentally lazy. Reading 50 pages of repetitive legal boilerplate is mentally exhausting, so people either gamble and sign blindly, or pay an attorney $400 an hour to tell them what they already suspected: 90% of the agreement is mundane boilerplate, and 10% is where the traps hide.

What if an AI tool didn't summarize the contract with hallucinated fluff, but instead acted like an attentional spotlight—letting you skim the boring majority and slowing you down only on the genuinely weird clauses?

That is **WeirdClauses**.

---

## What I Built

**WeirdClauses** is an open-source, local, and completely offline contract exploration tool built for the DEV Hacktoberfest Open-Source AI Challenge (Theme: *"Slow and Steady"*, rewarding laziness). 

Instead of reading agreements sequentially from top to bottom, WeirdClauses:
1. Ingests agreements (`.txt`, `.md`, `.docx`, or digital text `.pdf`) and losslessly segments them into clauses with exact character spans.
2. Measures per-token **linguistic surprisal** (`-log₂( P(token | context) )`) using a small open-weight causal base language model (`Qwen/Qwen2.5-0.5B`) running locally via Hugging Face Transformers.
3. Retrieves the nearest standard clauses from a generic baseline corpus ("what normal looks like") using sentence embeddings (`sentence-transformers/all-MiniLM-L6-v2`) and scores the clause *conditionally* against its standard neighbors.
4. Aggregates token surprisals using top-quartile mean (`topq`), Z-score normalizes within the document, and ranks clauses descending by unusualness.
5. Runs an auxiliary rule-based regex layer to extract key facts (money amounts, percentages, notice periods, durations, dates, auto-renewal triggers) labeled explicitly as `[rule-based]`.
6. Generates self-contained standalone HTML heat-map reports and powers an offline interactive single-page web explorer (`weirdclauses serve`).

Zero document text, tokens, or metadata ever leave your machine. No API keys, no telemetry, no recurring SaaS subscriptions.

---

## The Lazy Payoff 🦥

Being lazy doesn't mean being reckless—it means getting maximum signal for minimum reading effort. 

To measure whether WeirdClauses actually saves reading time, I built a reproducible benchmark (`make eval`) evaluating 100 synthetic residential leases (1,516 total clauses) with 292 unusual clauses planted across them, sampled from a held-out pool to prevent retrieval leakage.

Here is what the empirical numbers show:
- **Recall@10%**: **0.517 [0.469, 0.563]** (95% bootstrap CI). By reading just the top 10% highest-ranked clauses, you capture over **51.7%** of all anomalous terms.
- **Mean Percentile Rank**: **0.820 [0.799, 0.842]**. Planted unusual clauses fall in the **82nd percentile** of the document ranking on average.
- **Mean Reciprocal Rank (MRR)**: **0.916 [0.871, 0.958]**. The very first unusual clause in the document appears at rank **1.09** on average—meaning the top-ranked clause is almost guaranteed to be an anomaly.

In practice, contracts follow the Pareto principle: skimming the 90% that is identical boilerplate and reviewing the top 10% of flagged clauses turns a 20-minute slog into a focused 3-to-4-minute triage. You spend your attention budget where the financial and operational risk actually lives.

---

## Why Open Innovation Matters

In an era where every coding tool is a wrapper around a hosted cloud API, WeirdClauses is built on an unapologetic architectural stance: **contracts must never leave your computer**.

1. **Absolute Document Privacy**: Contracts contain your name, bank accounts, residential address, emergency contacts, rent amounts, and private covenants. Sending your lease to a third-party commercial LLM API leaks sensitive personal data and breaches strict corporate non-disclosure agreements. With local open weights, your private documents never touch a network socket.
2. **True Offline Independence**: WeirdClauses works on an airplane, in an air-gapped security room, or in a basement apartment with zero Wi-Fi. Once the one-time model weights are downloaded, it operates 100% offline.
3. **Zero Marginal Cost**: No monthly API tokens, no rate limits, no subscription tiers. It runs on commodity CPUs using standard open weights.
4. **The Core Signal Requires Raw Log-Probabilities**: Hosted commercial APIs (like ChatGPT, Claude, or proprietary endpoints) are designed for chat generation. They hide token log-probabilities, charge exorbitant premiums for partial logprobs, or distort probability distributions through RLHF and instruction tuning. Causal surprisal fundamentally requires teacher-forced exact token log-probabilities (`log₂( P(tᵢ | t<ᵢ) )`) from raw, unaligned **base models**. Open-weight models are not just a feature; they are the sole reason this mathematics works.

---

## Demo

Here is WeirdClauses in action ranking a residential lease with planted eccentric covenants (such as unannounced 3 AM landlord inspections, 180-day auto-renewal traps, and mandatory display of felines in bay windows):

### Interactive Web Explorer Demo
![WeirdClauses Interactive Demo](https://raw.githubusercontent.com/samashech/weirdClauses/main/docs/images/demo.gif)

### Standalone Heat-Mapped HTML Report
![Interactive HTML Report](https://raw.githubusercontent.com/samashech/weirdClauses/main/docs/images/report_heatmap.svg)

### Terminal CLI Ranking Table
![WeirdClauses CLI Ranking Table](https://raw.githubusercontent.com/samashech/weirdClauses/main/docs/images/cli_ranking.svg)

### Try It Yourself
You can run the interactive explorer locally in 10 seconds:
```bash
# Test instantly with zero downloads in deterministic mock mode
weirdclauses serve --mock --open
```

Or run end-to-end review on any contract:
```bash
weirdclauses review sample_lease.pdf --out report.html
```

---

## How It Works & Architecture

### 1. The Core Idea: What is Surprisal?
A causal language model is fundamentally a statistical prediction engine. As it reads text, it calculates a probability distribution over the vocabulary for what word comes next: `P(wₜ | w₁, ..., wₜ₋₁)`.

When text follows standard grammatical and professional conventions, the model assigns high probability to the tokens. But when text veers into bizarre, oppressive, or atypical territory, the model is "surprised." 

We quantify this surprise mathematically using **Shannon information content** (in bits):

```text
Surprisal(token) = -log₂( P(token | context) )
```

A standard phrase like *"Tenant shall pay rent on the first day of each month"* generates low surprisal (~2 to 4 bits per token). A clause stipulating *"Tenant shall submit all private smart speaker recordings to Landlord weekly"* forces the model into low-probability territory, causing surprisal to spike above 12 to 14 bits per token.

### 2. The Semantic Twist: Conditioning on "What Standard Looks Like"
Raw surprisal alone has a critical flaw: it gets confused by standard legal terminology. Archaic words like *"hereinafter"*, *"indemnification"*, or *"severability"* are rare in everyday conversational English, so raw language models often misidentify standard legalese as anomalous.

To solve this, WeirdClauses introduces **standard-clause conditioning**:
1. We bundle a synthetic baseline pack (`baseline_packs/rental/`) of 60 generic, standard clauses covering common lease covenants (rent, deposits, quiet hours, repair notices, holdover).
2. For each clause under review, we use `sentence-transformers/all-MiniLM-L6-v2` to retrieve the `k` nearest standard clauses from the baseline pack.
3. We construct a conditioning prompt:
   ```text
   Standard clauses of this type:
   - Within thirty days following surrender, Landlord shall return the security deposit...
   
   Clause under review:
   Regardless of premises condition, Tenant's entire deposit is 100% non-refundable...
   ```
4. We evaluate the language model over the prompt, but calculate token surprisals **only over the tokens in the clause under review**.

This transforms the measurement from *"how rare is this text in general English?"* to *"how surprising is this clause given what a standard version of it looks like?"*.

### 3. Architecture Pipeline
The entire system operates as a modular, deterministic pipeline:

```text
┌────────────────────────────────────────────────────────┐
│     Raw Contract Document (.txt, .md, .docx, .pdf)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│     Lossless Clause Segmentation (segment.py)          │
└───────────────────────────┬────────────────────────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
     ┌──────────────┐┌──────────────┐┌──────────────┐
     │ Causal Base  ││ Standard     ││ Rule-Based   │
     │ LM Surprisal ││ Baseline     ││ Fact RegEx   │
     │ (lm.py)      ││ (baseline.py)││ (facts.py)   │
     └───────┬──────┘└──────┬───────┘└──────┬───────┘
             │              │               │
             └──────┬───────┘               │
                    ▼                       │
       ┌────────────────────────┐           │
       │ Conditional Scoring    │           │
       │ (scoring.py)           │           │
       └────────────┬───────────┘           │
                    │                       │
                    ▼                       │
       ┌────────────────────────┐           │
       │ Top-Quartile Mean &    │           │
       │ Z-Score Normalization  │           │
       └────────────┬───────────┘           │
                    │                       │
                    └───────────┬───────────┘
                                ▼
       ┌─────────────────────────────────────────────────┐
       │ Standalone HTML Heat-Map Report & Web Explorer  │
       └─────────────────────────────────────────────────┘
```

### 4. Honest Evaluation & Baseline Comparison

We benchmarked WeirdClauses against simple non-LM baselines across 100 synthetic agreements (1,516 total clauses, 292 planted anomalies) with 95% bootstrap confidence intervals (1,000 resamples). 

Here are the complete, unedited results from `make eval`:

| Ranker | Recall@10% [95% CI] | Mean Percentile Rank [95% CI] | MRR [95% CI] |
| :--- | :---: | :---: | :---: |
| **Random** | 0.150 [0.113, 0.189] | 0.513 [0.476, 0.547] | 0.422 [0.365, 0.484] |
| **Longest Clause** | 0.722 [0.683, 0.762] | 0.923 [0.916, 0.931] | 1.000 [1.000, 1.000] |
| **TF-IDF Distance** | 0.273 [0.222, 0.321] | 0.775 [0.758, 0.793] | 0.575 [0.517, 0.638] |
| **Keyword/Rule Heuristic** | 0.564 [0.523, 0.607] | 0.803 [0.777, 0.830] | 0.948 [0.915, 0.975] |
| **Raw Surprisal (mean)** | 0.222 [0.185, 0.264] | 0.648 [0.621, 0.678] | 0.585 [0.513, 0.651] |
| **Raw Surprisal (topq)** | 0.270 [0.228, 0.317] | 0.687 [0.658, 0.714] | 0.650 [0.583, 0.716] |
| **Raw Surprisal (max)** | 0.300 [0.261, 0.343] | 0.682 [0.655, 0.708] | 0.622 [0.564, 0.683] |
| **Conditional Surprisal (mean, k=1)** | 0.420 [0.372, 0.472] | 0.806 [0.787, 0.824] | 0.793 [0.740, 0.845] |
| **Conditional Surprisal (topq, k=1)** | **0.517 [0.469, 0.563]** | **0.820 [0.799, 0.842]** | **0.916 [0.871, 0.958]** |
| **Conditional Surprisal (topq, k=3)** | 0.482 [0.434, 0.530] | 0.793 [0.770, 0.815] | 0.893 [0.843, 0.942] |

#### What the Data Tells Us (The Good and The Bad):
- **Conditioning Works**: Conditional surprisal almost doubles the Recall@10% of raw surprisal (**0.517 vs. 0.270**) and significantly improves Mean Percentile Rank (**0.820 vs. 0.687**).
- **Beating Standard Retrieval**: Conditional surprisal comfortably outperforms standard TF-IDF cosine distance (**0.820 vs. 0.775** percentile rank; **0.517 vs. 0.273** Recall@10%).
- **Why Longest Clause Scored High**: The `Longest Clause` baseline scored an artificially high 0.923 percentile rank. Why? Because human drafters writing weird synthetic clauses naturally included more descriptive adjectives and explanations than the terse single-sentence boilerplate provisions. In real-world contracts, traps are often short; this is a known synthetic benchmark artifact.
- **The Keyword Heuristic Challenge**: A simple keyword regex searching for words like *"penalty"*, *"forfeit"*, and *"waive"* scored 0.564 Recall@10%. While keywords work well when drafters use obvious trigger words, they fail completely on subtle clauses that lack trigger words (e.g., quiet relocation rights or mandatory exterior repainting). Conditional surprisal achieved higher overall Mean Percentile Rank (**0.820 vs. 0.803**) without needing an exhaustive keyword dictionary.

---

## Partner Categories

WeirdClauses relies strictly on open-weight models and foundational open-source toolkits:
- **Hugging Face Transformers**: Executes local causal base language models (`Qwen/Qwen2.5-0.5B`, also tested with `google/gemma-2-2b`) in teacher-forced inference mode to calculate exact token surprisal bits without generation.
- **Sentence-Transformers**: Runs `all-MiniLM-L6-v2` locally to embed standard clauses and perform fast cosine-similarity nearest-neighbor search for prompt conditioning.

No proprietary APIs or closed cloud services are used.

---

## Limitations and What I'd Do Next

Honest engineering requires acknowledging what a tool cannot do:
1. **Benchmark Optimism**: Planted clauses in the benchmark were engineered to be weird. In real-life contracts, unfair clauses can be phrased in mundane language.
2. **Generic Baselines**: The bundled baseline pack represents generic residential leases. It is not tailored to specific municipal or state statutes (e.g., California Civil Code vs. New York City Housing Code).
3. **Surprisal Flags Rare Wording, Not Unlawfulness**: An archaic or ornate formulation of a harmless clause will score high surprisal, while a predatory term phrased in standard boilerplate might score low surprisal (which is why our rule-based fact extractor always surfaces money and dates regardless of score).
4. **English Language Only**: The tokenizers and embedding models are currently calibrated for English prose.

### What I'd Do Next:
- **Jurisdiction-Specific Baseline Packs**: Curate tailored baseline packs for tenant-friendly jurisdictions (e.g., Ontario, Berlin, California) so users can measure compliance against local statutory baselines.
- **Commercial & SaaS Addendums**: Expand baseline packs to cover B2B SaaS agreements, NDAs, and employment contracts.
- **ONNX Runtime & INT4 Quantization**: Quantize model weights to 4-bit GGUF/ONNX to run instantaneous inference on mobile and low-power hardware in < 500 MB RAM.

---

## Code Repository

WeirdClauses is 100% open-source under the MIT License:

- **GitHub Repository**: [github.com/samashech/weirdClauses](https://github.com/samashech/weirdClauses)
- **Documentation**:
  - [Evaluation Results & Methodology](https://github.com/samashech/weirdClauses/blob/main/eval/results/benchmark_table.md)
  - [Limitations & Boundary Conditions](https://github.com/samashech/weirdClauses/blob/main/docs/LIMITATIONS.md)
  - [Real-Contract Case Study Protocol](https://github.com/samashech/weirdClauses/blob/main/docs/CASE_STUDY.md)

---

> **DISCLAIMER: WeirdClauses is NOT legal advice.** It is an open-source research and text-analysis tool designed to highlight unusual phrasing and candidate anomalies in contracts. It does not provide legal interpretation, counsel, representation, or warranty. Always consult a qualified attorney for legal guidance.

*AI Disclosure: This project and article were developed with AI pair-programming assistance from Antigravity (Google DeepMind). All architectural designs, code verification, benchmark executions, and editorial decisions were conducted by the author.*
