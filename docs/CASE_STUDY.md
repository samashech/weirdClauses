# WeirdClauses Real-Contract Case Study Protocol

> **DISCLAIMER: WeirdClauses is NOT legal advice.** It is a research and text-analysis tool for identifying unusual phrasing. Always consult a qualified attorney for legal guidance.

This protocol enables you to evaluate WeirdClauses on 2–3 real-world agreements that you are legally authorized to review (e.g., your current or previous residential lease, a university housing agreement, or a commercial office license).

---

## Evaluation Objectives

1. **Attentional Efficiency**: Measure reading time required for a full unassisted read vs. reading only the top 10% flagged clauses and key facts table.
2. **Qualitative Utility**: Measure agreement between the model's highest-surprisal clauses and clauses you independently judge to be commercially or personally significant.
3. **Failure Analysis**: Identify false positives (benign clauses flagged as weird) and false negatives (onerous clauses that slipped past unflagged).

---

## Step-by-Step Execution Protocol

### Step 1: Baseline Reading (Full Unassisted Review)
1. Pick a contract you have permission to analyze.
2. Start a timer ($T_{\text{full}}$).
3. Read the contract from start to finish as you normally would before signing.
4. Mark every clause you consider non-standard, surprising, or concerning.
5. Stop the timer and log $T_{\text{full}}$ in minutes.

### Step 2: WeirdClauses Analysis
Run WeirdClauses on the agreement in conditional mode:
```bash
weirdclauses review path/to/real_lease.pdf --out case_study_report.html --top 10%
```
Open `case_study_report.html` in your browser.

### Step 3: Triaged Review (Assisted Review)
1. Start a timer ($T_{\text{triage}}$).
2. Review **only**:
   - The **Read These First** cards (top 10% unusual clauses).
   - The **Key Facts** rule-based extraction table (money, notice periods, dates, renewals).
   - Any high-surprisal red spans highlighted in the heat map.
3. Stop the timer and log $T_{\text{triage}}$ in minutes.

---

## Case Study Data Collection Template

Copy the template below for each agreement evaluated:

```markdown
### Agreement #1: [Brief Descriptive Title, e.g., 2024 Metro Residential Lease]
- **Jurisdiction**: [e.g., Seattle, WA]
- **File Format**: [.pdf / .docx / .txt]
- **Total Word Count**: [e.g., 4,200 words]
- **Total Clauses Identified**: [e.g., 28 clauses]

#### Timing Comparison
- **Full Unassisted Read Time ($T_{full}$)**: _____ minutes
- **Triaged Read Time ($T_{triage}$)**: _____ minutes
- **Time Reduction**: `(T_full - T_triage) / T_full * 100%` = _____ %

#### Qualitative Analysis (Top 10% Flagged Clauses)
| Rank | Section / Clause Snippet | Model Score (bits / Z) | Human Judgment (True Positive / Benign False Positive) | Notes |
| :---: | :--- | :---: | :---: | :--- |
| #1 | [e.g., Clause 14: Tenant pays landlord legal fees win or lose] | 13.4 b (+2.1 Z) | True Positive | Highly one-sided fee clause |
| #2 | [e.g., Clause 8: 90 days notice for renewal] | 11.8 b (+1.4 Z) | True Positive | Longer than typical 30-day notice |
| #3 | [e.g., Clause 22: Victorian description of garden upkeep] | 11.2 b (+1.1 Z) | False Positive | Archaic language but benign term |

#### Missed Clauses (False Negatives)
*List any clauses that were commercially important or risky, but were NOT in the top 10%:*
1. [Clause description and why it mattered]
2. [Clause description and why it mattered]

#### Key Facts Audit
- **Extracted Rent / Deposit**: [Accurate / Missed / Incomplete]
- **Notice Periods Extracted**: [Accurate / Missed / Incomplete]
- **Auto-Renewal Detected**: [Yes / No / N/A]
```

---

## Guidelines for Real Document Privacy

- **Offline Guarantee**: WeirdClauses runs 100% locally on your CPU/GPU. No document text, token logprobs, or metadata ever leave your machine.
- **Redaction**: If you intend to publish case study excerpts or reports online, manually redact names, addresses, phone numbers, and identifying landlord entities.
