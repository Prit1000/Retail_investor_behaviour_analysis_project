# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Retail-Heavy Stocks vs. Results-Season Volatility

## Project Summary
BA/DA case study testing whether high-retail-ownership stocks show more erratic
price/volume behavior around quarterly results than low-retail-ownership stocks,
using Indian equities (10 Finance + 10 Manufacturing sector stocks, 8 quarters
from 2024-09-30 to 2026-06-30). `INSTRUCTIONS.md` holds the *why* behind each
locked decision; this file is the *what* for day-to-day execution.

## Stack
- **Data collection**: yfinance (OHLCV, scripted), screener.in (shareholding %, manual CSV)
- **Storage**: SQLite (`data/retail_behavior.db`, committed to git)
- **Analysis**: Python (pandas, scipy.stats, matplotlib/seaborn)
- **Stats test**: Mann-Whitney U (scipy.stats.mannwhitneyu) — non-parametric, n=10/bucket
- **Dashboard**: Tableau (deliberate skill-building choice, not Power BI)
- **Case study**: PowerPoint
- **Env**: venv + requirements.txt (Docker explicitly out of scope for now)

## Run Commands
All scripts use relative paths (`data/...`) — **run from the repo root**.
```bash
python -m venv venv
venv\Scripts\activate             # Windows (source venv/bin/activate elsewhere)
pip install -r requirements.txt

# One-time DB init — no script applies the schema
sqlite3 data/retail_behavior.db < sql/schema.sql

python src/load_shareholding.py   # seeds `stocks`, loads data/raw/*.csv into `shareholding`
python src/ingest_prices.py       # pulls yfinance OHLCV (period=2y) into `price_data`
python src/ingest_prices.py TMPV.NS   # single-ticker mode
python src/metrics.py             # computes Metric A + B, ±3d and ±5d → `metrics_results`
python src/stats_test.py          # assigns buckets, runs Mann-Whitney U, prints verdict

jupyter notebook notebooks/01_pre_metric_eda.ipynb
jupyter notebook notebooks/02_post_metric_eda.ipynb

pytest                                       # all tests
pytest tests/test_<feature>.py::test_<name>  # single test
```

**Rerun behavior** (matters when re-executing a stage):
- `load_shareholding.py` and `ingest_prices.py` use `to_sql(if_exists="append")`
  against tables with composite primary keys — rerunning without first deleting
  the affected rows raises `IntegrityError`. `stocks` uses `INSERT OR IGNORE`.
- `metrics.py` uses `if_exists="replace"`, which drops and recreates
  `metrics_results` from the DataFrame — the PK/FK from `schema.sql` are lost.
- `stats_test.py` mutates `metrics_results.bucket` in place via `UPDATE`.

## Pipeline / Data Flow
```
data/raw/shareholding.csv ─┐
data/raw/results_dates.csv ┴→ load_shareholding.py → stocks, shareholding (results_date merged in)
yfinance ───────────────────→ ingest_prices.py     → price_data
shareholding + price_data ──→ metrics.py           → metrics_results (bucket = NULL)
stocks + shareholding ──────→ stats_test.py        → metrics_results.bucket, console verdict
```
- The ticker list is duplicated as a hard-coded constant in `load_shareholding.py`
  (`STOCKS`, with sector + expected tilt), `ingest_prices.py` (`TICKERS_NS`) and
  the scraper scripts — change all of them together.
- `metrics.py` locates the event window by `np.searchsorted` on the stock's
  trading dates (a non-trading results date snaps to the next trading day); the
  event window is `[idx-w, idx+w]` and the baseline is the 30 trading days before it.
  Quarters with NULL `results_date` are skipped.
- Buckets are per ticker (not per quarter), from `AVG(public_retail_pct)` across
  all quarters, then written onto every `metrics_results` row for that ticker.
- `tableau/*.csv` are export targets (header-only so far); no export script exists yet.

## Feature Workflow (project slash commands in `.claude/`)
Each roadmap step is built as a spec-driven feature branch:
1. `/create-spec <step> <name>` — requires a clean tree; creates
   `feature/<slug>` off `main` and writes `specs/<NN>-<slug>.md`
2. Implement against the spec
3. `/test-feature <NN>-<slug>` — test-writer subagent writes
   `tests/test_<NN>-<slug>.py` from the spec (in-memory SQLite fixture built from
   `sql/schema.sql`), test-runner executes it
4. `/code-review-feature <NN>-<slug>` — security + quality reviewers run in
   parallel on `git diff`; no edits until the user approves the action plan

## Stock Universe (locked, verify against screener.in before data collection)
**Finance (10)**: HDFC Bank, ICICI Bank, Kotak Mahindra Bank, Bajaj Finance,
Bajaj Finserv, Punjab National Bank, Bank of Baroda, IDFC First Bank, Yes Bank,
IIFL Finance (verify retail tilt before locking)

**Manufacturing (10)**: Larsen & Toubro, Maruti Suzuki, Bajaj Auto, Tata Motors,
Hero MotoCorp, Ashok Leyland, Suzlon Energy, RVNL, BHEL, Vodafone Idea (`IDEA` —
10th slot, sector fit still flagged "verify" in code)

Tickers use `.NS` suffix for yfinance (e.g. `HDFCBANK.NS`); DB stores them without
it. Tata Motors is `TMPV` (post-demerger passenger-vehicles listing), not `TATAMOTORS`.

## Conventions
- All SQL tables keyed by `ticker` (string, NSE symbol without `.NS`) and
  `quarter_end_date` / `trade_date` (ISO date strings)
- Event window: **±3 trading days primary**, **±5 trading days robustness check**,
  around each quarter's results date
- Baseline window: 30 trading days immediately preceding the event window
- Bucketing: **within-sector median split** on `public_retail_pct` — never a
  global rank split across both sectors (confounds sector with retail level)
- Bucket comparison uses **median**, not mean (robust to outlier quarters)
- Metrics computed: volume spike ratio, price range %, realized volatility —
  each at both ±3d and ±5d
- `auto_adjust=True` required on every yfinance pull (handles splits/dividends)

## Roadmap (numbered steps — specs live in `specs/`)
1. Project scaffold (schema, folders, requirements.txt)
2. Manual data collection (screener.in → raw CSVs)
3. Load shareholding data into SQLite
4. Ingest price data via yfinance into SQLite
5. Pre-metric EDA + hypothesis formulation (H0/H1 written in notebook)
6. Python metrics calculation (Metric A + B, ±3d and ±5d)
7. Bucketing logic (within-sector median split)
8. Statistical test (Mann-Whitney U, 4 metric/window combinations)
9. Post-metric EDA (bucket comparison, interpretation)
10. Root cause reasoning (RCA + PESTEL, manual, tied to confirmed result)
11. Tableau workbook (bucket comparison + forward-looking KPI flag table)
12. Case study PPT (Question → Finding → Root Cause → Pain Point → Recommendation)
13. README

## Hard Rules
- **No scraping of screener.in** — manual CSV entry only (ToS + effort tradeoff).
  `src/scrape_shareholding.py` and `src/scrape_results_dates.py` (NSE API) exist
  in the repo but are outside the plan: don't run or extend them, and their
  deps (`requests`, `bs4`) are deliberately not in requirements.txt
- **No live/real-time data feed** — this is a static, quarterly-lagging analysis;
  the Tableau KPI flag table is a manual-rerun snapshot, not a continuous system
- **No Docker** for this project's initial scope — venv + requirements.txt only
- **No global (cross-sector) bucket ranking** — within-sector median split only
- **No t-test** — sample size (n=10/bucket) requires Mann-Whitney U
- **No expanding the stock universe or quarter count mid-project** to chase
  significance — a null/weak finding is a valid, reportable outcome
- **No predictive modeling** — descriptive/diagnostic only
- **RCA/PESTEL reasoning happens only after Stage 8's stats verdict is known**,
  and must tie back to the actual confirmed result — not generic speculation
  written before the data is seen (`deliverables/root_cause_analysis.md` is
  the template the user fills manually)
- Every raw-query touchpoint (if any ad-hoc SQL is written) must be parameterized,
  never string-concatenated — standard safety habit regardless of project size
