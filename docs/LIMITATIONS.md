# WeirdClauses Limitations & Boundaries

> **DISCLAIMER: WeirdClauses is NOT legal advice.** It is a research and text-analysis tool for identifying unusual phrasing. Always consult a qualified attorney for legal guidance.

This document describes known limitations, methodological boundaries, and assumptions of WeirdClauses.

---

## 1. Benchmark Optimism: Planted Clauses are Weird by Construction

In the Phase 6 benchmark evaluation (`eval/run_eval.py`), the test dataset consists of synthetic lease agreements where 2–4 unusual clauses were deliberately drafted and planted alongside standard provisions. 

Because these planted clauses were explicitly engineered to represent extreme, one-sided, or eccentric covenants (e.g., *24/7 unannounced inspections*, *mandatory external facade repainting*, *unrestricted unilateral rent increases*, or *wildlife authorization*), the benchmark evaluation metrics (Recall@10%, Percentile Rank, and MRR) reflect an **optimistic ceiling**.

In real-world commercial and residential contracts:
- Oppressive terms are often veiled in subdued, highly standardized legalese rather than overtly bizarre phrasing.
- The boundary between "standard protection" and "unfair burden" is context-dependent and frequently subtle.

---

## 2. Generic, Non-Jurisdiction-Specific Baseline Corpus

The default standard clause packs bundled with WeirdClauses (e.g., `baseline_packs/rental/`) are **generic synthetic baselines**:
- They are not tailored to any specific municipal, state, provincial, or national legal code (such as California Civil Code, New York City Housing Maintenance Code, or UK Housing Act).
- Statutory tenant protections vary widely across jurisdictions. A clause deemed "standard" in one jurisdiction may be void or illegal as a matter of law in another.
- Users evaluating contracts in specific regions should curate custom baseline packs representing standard practices for their local jurisdiction (`WC_BASELINE_DIR`).

---

## 3. Linguistic Surprisal vs. Substantive Unfairness

WeirdClauses measures **linguistic surprisal** ($\Delta = -\log_2 P(\text{token} \mid \text{context})$) from an open-weight causal language model, augmented by semantic baseline retrieval:
- **Surprisal flags rare phrasing, not substantive illegality**: An archaic, ornate, or highly idiosyncratic formulation of an entirely benign clause (e.g., a formal, Victorian-era description of mowing the lawn) will produce high surprisal and receive a high ranking.
- **Normal phrasing can be predatory**: Conversely, an exploitative term phrased using completely standard, boilerplate terminology (e.g., a standard-looking clause specifying an unusually steep late fee percentage) may have moderate or low surprisal unless captured by rule-based fact extraction.

---

## 4. Unusual Is Not Necessarily Unfavourable

A high weirdness score indicates that a clause deviates from standard baseline language. It does **not** indicate that the clause is harmful to the reader:
- An unusually generous landlord concession (e.g., *"Landlord provides complimentary monthly deep cleaning and free gigabit fiber optic internet"*) is linguistically anomalous and will score high surprisal.
- Always read the flagged clause in context. The ranking acts as an **attentional spotlight** ("slow down and read this carefully"), not a moral or legal judgment.

---

## 5. English Language Only

- The default causal language model (`Qwen2.5-0.5B`) and sentence embedder (`all-MiniLM-L6-v2`) are optimized and evaluated exclusively on English contract prose.
- Non-English contracts, bilingual agreements, or jurisdiction-specific Latin maxims are not currently supported and may yield erratic token surprisal estimates.

---

## 6. Document Layout and OCR

- Ingestion supports clean digital `.txt`, `.md`, `.docx`, and text-extractable `.pdf` files.
- Scanned, flattened image PDFs are detected and intentionally rejected. Optical Character Recognition (OCR) is strictly out of scope for WeirdClauses.
