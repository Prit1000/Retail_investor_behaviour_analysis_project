# Root Cause Analysis — Retail Ownership vs. Results-Day Erraticness

**Project:** Retail Investor Behavior Analysis
**Scope:** Why the core hypothesis test (Mann-Whitney U) found *no significant difference between High-retail and Low-retail stocks*, and why the direction leaned opposite to H1.


## 1. Background

**Original hypothesis (H1):** Stocks with higher public retail ownership show greater erraticness (volume spikes, wider price ranges, higher volatility) around quarterly results than stocks with lower retail ownership.

**Result (Mann-Whitney U):** No metric reached significance at either window width (all p ≥ 0.058). Where a trend existed, the Low-retail bucket showed directionally *higher* medians than High -> the opposite of what H1 predicted.

This document explains why, using confirmed results.

## 2. 5 Whys

**Why #1: Why did High and Low show no significant difference?**
Because the median gap between buckets was small relative to within-bucket spread on every Mann-Whitney U test (Step 5: all p ≥ 0.058).

**Why #2: Why was the gap small instead of large, if retail ownership should drive reactive trading?**
The OLS regression of realized_vol on all four ownership types found `public_retail_pct` non-significant (p=0.841 at ±3d, p=0.476 at ±5d) even after controlling for `promoter_pct`, `fii_pct`, and `dii_pct` , while `dii_pct` was significant at both windows (p=0.022, p<0.001). Retail% was likely the wrong variable to isolate in the first place: *DII ownership is what actually carries a measurable relationship with volatility.*

**Why #3: Why does Low-retail stocks consistently had slightly higher median values than  High-retail stocks, not just "no different"?**
Two confirmed sources of noise in the comparison:
- The Kruskal-Wallis test on calendar year found `price_range_pct` significantly different across years (p=0.023 at ±3d, p=0.013 at ±5d), with 2025 running higher than 2024 and 2026, independent of bucket — an external timing effect sitting inside the same comparison.
- The Wilcoxon signed-rank test confirmed ±3d values are significantly higher than ±5d for the same stock-quarter (p≤0.002) , meaning any real signal, if present, is concentrated narrowly around results and easily swamped by small-sample noise in the wider window, consistent with the ±5d results drifting further from significance than ±3d in Step 5.

Both are confirmed contributors to variance in the comparison; neither alone fully explains the direction being reversed, which remains the one open question in this chain.

**Why #4: Why would the median split do that??**
Closing it requires one direct check not yet run: listing which tickers sit in the High bucket and checking whether the bucket is capturing retail *trading intensity* or just retail *ownership level*. The Chi-square test of independence and the 4-group Kruskal-Wallis both ruled out sector as the explanation (p=0.45–0.66 across all 6 sector×bucket comparisons) , so the reversal isn't a sector artifact, but what it is remains unconfirmed.

**Why #5: Why does this matter beyond "no effect found"?**
The project's defensible finding isn't "nothing happened" — the OLS regression identified DII ownership, not retail ownership, as the variable with a real, significant relationship to realized_vol. That's a stronger, data-backed conclusion than the original hypothesis, and it leads the Discussion section below.


## 3. Fishbone (Ishikawa) Diagram

**Effect: No significant High/Low retail difference found (Mann-Whitney U); direction mildly reversed**

### Structural / Ownership
*(OLS regression)*
- `dii_pct` has a significant negative relationship with realized_vol (p=0.022 at ±3d, p<0.001 at ±5d).
- `public_retail_pct` does not (p=0.841, p=0.476), even controlling for promoter/FII/DII.
- Strongest, most direct branch: ownership composition matters, but not the component the original hypothesis targeted.

### Measurement Design
- Static bucket-assignment bug in the original `assign_buckets()` diluted signal — confirmed by the shift in realized_vol's p-value at ±3d from 0.871 (pre-fix) to 0.058 (post-fix).
- Wilcoxon signed-rank test confirms ±3d and ±5d are statistically distinct (p≤0.002 on all 3 metrics), validating that reaction concentrates in the tight window — exactly where Mann-Whitney p-values sat closest to significant.
- 6 bad zero-volume dates from the original EDA were never dropped in `metrics.py` — confirmed unresolved.
- Baseline window in `metrics.py` (30 days immediately adjacent to the event window) deviates from the original spec's gapped −40/−20 window — confirmed deviation.

### Macro / Regime Timing
*(Kruskal-Wallis by year)*
- `price_range_pct` differs significantly by calendar year (p=0.023 at ±3d, p=0.013 at ±5d), with 2025 elevated relative to 2024 and 2026, independent of bucket.
- Weakened by 2024's small subsample (n=20 vs 80/60 for 2025/2026). **So highly biased**

### Company-Specific Supply Shocks
*(OLS trend regression)*
- **IDEA:** confirmed genuine linear decline in retail% (slope = −1.773 pts/quarter, p=0.005, R²=0.758).
- **ICICIBANK:** statistically significant slope (p=0.035) but driven by a step-change after 6 flat quarters, not gradual drift — R²=0.553 carried mostly by the last 2 data points.
- **IDFCFIRSTB:** no significant linear trend (p=0.315); the pattern is a peak in Dec-2024 followed by decline, not the drift originally assumed in the EDA.


## 4. Conclusion

No significant difference was found between High- and Low-retail stocks on any erraticness metric (Mann-Whitney U, all p ≥ 0.058). This null result is not attributable to sector composition. It is partly explained by targeting the wrong ownership variable — DII ownership, not retail ownership, shows a significant relationship with volatility — and partly by confirmed sources of noise in the comparison: a year-level timing effect and the narrow concentration of any real signal around the ±3d window. The mild reversal of direction (Low trending above High) remains only partially explained; the ticker-level check above is the next step to close that gap.
