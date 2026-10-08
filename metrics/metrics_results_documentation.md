# `metrics_results` - Metric Documentation (as implemented in `metrics.py`)

---

## 1. Identity columns

| Column | Source | Role |
|---|---|---|
| `ticker` | copied from `shareholding` table | which stock is which |
| `quarter_end_date` | copied from `shareholding` table| which quarter |
| `results_date` | copied from `shareholding` table | anchor date for the event window |

---

## 2. `window_days` — methodology parameter

how many trading days before/after results_date count as the **event window.** Common choices in event-study literature: ±1 (tight, catches immediate reaction only), ±3 (your primary), ±5 (wider, robustness check).

- Values: `3` (primary), `5` (robustness)
- Not a measurement — a design choice fixing how many trading days before/after `results_date` define the event window.
- Stored as **two rows per stock-quarter** so robustness can be checked later (does the finding hold at both widths).

---

## 3. `volume_spike_ratio` — Metric A, trading activity surge

**Formula (as coded):**
```
volume_spike_ratio = mean(volume during event window) / mean(volume during baseline window)
```

**Event window:** `dates[idx - window : idx + window + 1]` → **2 × window + 1 trading days, results_date included.**

**Baseline window (as coded):**
```
baseline_end   = idx - window           # starts right where event window begins
baseline_start = baseline_end - 30      # 30 trading days before that
```
So baseline is the 30 trading days **immediately preceding** the event window, with **no gap** between them.

**Why used:** Raw volume isn't comparable across stocks of different sizes - the ratio normalizes to "how many times more than this stock's own normal activity." >1.0 = more activity than usual; proxy for retail herding (institutions pre-position, retail reacts at/after news).

---

## 4. `price_range_pct` — Metric A (2nd half), intraday chaos

**Formula:**
```
daily_range_pct = (high - low) / close                     # per day
price_range_pct = mean(daily_range_pct during event window) / mean(daily_range_pct during baseline window)
```

**Why used:** Close-to-close change can hide a stock that whipsaws intraday but closes flat. This catches that. Normalizing by `close` makes the range comparable across stocks trading at very different price levels (₹200 vs ₹2,000).

**Same event/baseline windows as `volume_spike_ratio`** (defined once per row, reused for both metrics).

---

## 5. `realized_vol` — Metric B, volatility

**Formula:**
```
log_ret      = ln(close_t / close_t-1)        # within event window only
realized_vol = std(log_ret)
```

**Why used:** Standard deviation of log returns is the textbook/industry-standard risk measure. Log returns used (not simple % returns) because they're additive across days - finance convention.

**Important , this is event-window-only, NOT a ratio or delta against baseline.** No `baseline_realized_vol` or `vol_delta` is computed anywhere in `metrics.py`. 

**Known limitation:** ±3d window → at most 7 price rows → 6 log returns. Std dev from 6 observations is a noisy, low-power estimate.

---

## 6. `bucket` — High/Low retail label

**Formula:**
```	
bucket = 'High' if public_retail_pct > median(public_retail_pct within that sector)
 else 'Low'
```

**Columns involved:** `shareholding.public_retail_pct`, `shareholding.quarter_end_date`, `stocks.sector` → written to `metrics_results.bucket`.

**Why used:** Within-sector, within-quarter median split is deliberate on two axes:
- **Within-sector** (not a global median across Finance + Manufacturing) — avoids sector-level ownership norms contaminating the split. A sector that's naturally more retail-heavy shouldn't push its stocks disproportionately into "High" just because of sector composition.
- **Per-quarter** (not collapsed to each stock's all-period average) — retail ownership % drifts over time (mergers, government stake dilution, etc.), so a stock's bucket membership should be allowed to change quarter to quarter, not be frozen to a single label for its entire history.

**Not computed from price data at all** — it's the grouping variable, not a measurement. Every other column in `metrics_results` (volume spike, price range, realized vol) gets compared across this label; this is where ownership data and trading-behavior data converge.

**Known limitation:** a median split guarantees a roughly balanced High/Low count per sector-quarter by construction, but says nothing about whether the split is behaviorally meaningful — a stock sitting just above vs. just below the median is nearly identical in practice, yet gets opposite labels. This is a standard median-split caveat, not specific to this dataset.

---

