# WeirdClauses Benchmark Evaluation Results

> **DISCLAIMER: WeirdClauses is NOT legal advice.** It is a research and text-analysis tool for identifying unusual phrasing. Always consult an attorney.

Evaluated on 100 synthetic residential leases with 292 planted unusual clauses. Confidence intervals (95%) computed via 1,000 bootstrap resamples.

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
| **Conditional Surprisal (topq, k=1)** | 0.517 [0.469, 0.563] | 0.820 [0.799, 0.842] | 0.916 [0.871, 0.958] |
| **Conditional Surprisal (max, k=1)** | 0.338 [0.289, 0.390] | 0.760 [0.737, 0.782] | 0.695 [0.635, 0.750] |
| **Conditional Surprisal (mean, k=3)** | 0.388 [0.341, 0.438] | 0.775 [0.753, 0.795] | 0.737 [0.677, 0.793] |
| **Conditional Surprisal (topq, k=3)** | 0.482 [0.434, 0.530] | 0.793 [0.770, 0.815] | 0.893 [0.843, 0.942] |
| **Conditional Surprisal (max, k=3)** | 0.322 [0.272, 0.373] | 0.712 [0.685, 0.739] | 0.684 [0.623, 0.744] |
| **Conditional Surprisal (mean, k=5)** | 0.373 [0.326, 0.423] | 0.768 [0.746, 0.789] | 0.718 [0.657, 0.775] |
| **Conditional Surprisal (topq, k=5)** | 0.458 [0.404, 0.510] | 0.789 [0.767, 0.812] | 0.877 [0.826, 0.930] |
| **Conditional Surprisal (max, k=5)** | 0.305 [0.255, 0.357] | 0.712 [0.686, 0.739] | 0.670 [0.602, 0.733] |

## Empirical Choice of Default Aggregator and Parameters

- **Selected Default Configuration**: `Conditional Surprisal (topq, k=1)`
- **Recall@10%**: 0.517 [0.469, 0.563]
- **Mean Percentile Rank**: 0.820 [0.799, 0.842]
- **MRR**: 0.916 [0.871, 0.958]

### Why this configuration was selected:
1. **Signal vs. Length**: `topq` captures the most anomalous phrasing without diluting signal across standard boilerplate.
2. **Context Conditioning**: Priming with standard neighbors ($k=1, 3$) provides comparison context without saturating attention.
