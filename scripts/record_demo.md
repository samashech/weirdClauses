# WeirdClauses Demo Recording Script (60–90 Seconds)

This guide provides a reproducible walkthrough for recording a 60–90 second demo GIF showing WeirdClauses running locally and offline using only the bundled synthetic samples.

> **DISCLAIMER: WeirdClauses is NOT legal advice.** It is a research and text-analysis tool for identifying unusual phrasing. Always consult a qualified attorney for legal guidance.

---

## Recommended Tools

You can record the demo using either:
1. **[VHS by Charm](https://github.com/charmbracelet/vhs)** (*Automated & Recommended*): Generates pixel-perfect terminal GIFs from an automated `.tape` script.
2. **[Asciinema](https://asciinema.org) + [Agg](https://github.com/asciinema/agg)**: Records terminal session and compiles to GIF.
3. **[Peek](https://github.com/phw/peek)** or **[Kooha](https://github.com/SeaDve/Kooha)**: GUI screen recorders for Linux.

---

## 1. Automated VHS Script (`demo.tape`)

If you have `vhs` installed (`brew install vhs` or `go install github.com/charmbracelet/vhs@latest`), save the following block as `scripts/demo.tape` and run:

```bash
vhs scripts/demo.tape
```

### `scripts/demo.tape`
```vhs
# Output configuration
Output docs/images/demo.gif
Set FontSize 14
Set Width 1000
Set Height 650
Set Padding 20
Set Theme "Catppuccin Macchiato"

# Setup terminal
Hide
Type "source .venv/bin/activate && clear"
Enter
Show

# Scene 1: System Readiness & Privacy Check (0:00 - 0:15)
Type "# 1. Verify offline models and environment readiness"
Enter
Sleep 500ms
Type "weirdclauses doctor"
Enter
Sleep 3s

# Scene 2: Score Agreement & Rank Anomalies (0:15 - 0:45)
Type "clear"
Enter
Sleep 500ms
Type "# 2. Analyze rental agreement for unusual clauses"
Enter
Sleep 500ms
Type "weirdclauses score samples/unusual_rental.txt --mode conditional --top 5"
Enter
Sleep 5s

# Scene 3: Generate Interactive Standalone Report (0:45 - 1:10)
Type "# 3. Export self-contained offline HTML report"
Enter
Sleep 500ms
Type "weirdclauses review samples/unusual_rental.txt --out report.html --top 10%"
Enter
Sleep 4s

# Scene 4: Start Zero-Telemetry Web Explorer (1:10 - 1:25)
Type "# 4. Launch local interactive web interface"
Enter
Sleep 500ms
Type "weirdclauses serve --port 8000"
Enter
Sleep 4s
Ctrl+C
Sleep 1s
```

---

## 2. Manual Recording Walkthrough

If recording manually with OBS, Peek, or Kooha, follow these four chronological scenes:

### Scene 1: Diagnostics & Offline Verification (0:00 – 0:15)
1. Clear the terminal: `clear`.
2. Type:
   ```bash
   weirdclauses doctor
   ```
3. **What to highlight**:
   - Prominent **NOT legal advice** disclaimer panel.
   - Offline readiness checks (Python 3.11+, PyTorch, local model weights in `~/.cache/`).
   - Confirmation: `"System is ready. All models and caches available offline."`

### Scene 2: Surprisal Ranking of Anomalous Lease (0:15 – 0:45)
1. Clear the terminal: `clear`.
2. Run:
   ```bash
   weirdclauses score samples/unusual_rental.txt --mode conditional --top 5
   ```
3. **What to highlight**:
   - The progress indicator (`Scoring clauses (conditional mode, slow & steady)...`).
   - The ranking table showing planted anomalies at the top:
     - Rank #1: **Feline Visual Observation Covenant** (Score: 12.80 bits, +1.13 Z)
     - Rank #2: **Thermodynamic Beverage Logs** (Score: 12.24 bits, +0.81 Z)
     - Rank #3: **Sofa Sleeping Sovereignty** (Score: 11.19 bits, +0.19 Z)
   - The semantic similarity to standard clauses (e.g., Pet Deposit, Temperature Maintenance).

### Scene 3: Standalone Heat-Mapped Report Export (0:45 – 1:10)
1. Run:
   ```bash
   weirdclauses review samples/unusual_rental.txt --out report.html --top 10%
   ```
2. **What to highlight**:
   - "Top Unusual Clauses (Read These First)" summary table.
   - Successful generation of `report.html`.
   - Open `report.html` in browser for 5 seconds to showcase dark/light mode toggle and character-accurate red token surprisal highlights.

### Scene 4: Local Single-Page Web Explorer (1:10 – 1:30)
1. Run:
   ```bash
   weirdclauses serve --port 8000 --open
   ```
2. **What to highlight**:
   - Instant browser startup at `http://127.0.0.1:8000`.
   - Selecting a bundled sample from the dropdown.
   - Clicking **Analyze Agreement**.
   - Displaying the metric summary cards and rule-based key facts table.
