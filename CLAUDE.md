# CLAUDE.md — Retail-Heavy Stocks vs. Results-Season Volatility

## Project Summary
BA/DA case study testing whether high-retail-ownership stocks show more erratic
price/volume behavior around quarterly results than low-retail-ownership stocks,
using Indian equities (10 Finance + 10 Manufacturing sector stocks, 8 quarters).

## Stack
- **Data collection**: yfinance (OHLCV, scripted), screener.in (shareholding %, manual CSV)
- **Storage**: SQLite (`data/retail_behavior.db`)
- **Analysis**: Python (pandas, scipy.stats, matplotlib/seaborn)
- **Stats test**: Mann-Whitney U (scipy.stats.mannwhitneyu) — non-parametric, n=10/bucket
- **Dashboard**: Tableau (deliberate skill-building choice, not Power BI)
- **Case study**: PowerPoint
- **Env**: venv + requirements.txt (Docker explicitly out of scope for now)

## Run Commands
```bash
python -m venv venv
source venv/bin/activate          # or venv\Scripts\activate on Windows
pip install -r requirements.txt

python src/load_shareholding.py   # loads manual CSVs into SQLite
python src/ingest_prices.py       # pulls yfinance OHLCV into SQLite
python src/metrics.py             # computes Metric A + B, ±3d and ±5d, writes metrics_results
python src/stats_test.py          # buckets + runs Mann-Whitney U, prints verdict

jupyter notebook notebooks/01_pre_metric_eda.ipynb
jupyter notebook notebooks/02_post_metric_eda.ipynb
```

## Folder Map
```
retail-behavior-ba/
├── data/raw/              # manual screener.in CSVs (shareholding, results dates)
├── data/retail_behavior.db
├── sql/schema.sql         # 4 tables: stocks, shareholding, price_data, metrics_results
├── src/                   # ingest_prices.py, load_shareholding.py, metrics.py, stats_test.py
├── notebooks/             # 01_pre_metric_eda.ipynb, 02_post_metric_eda.ipynb
├── tableau/                # CSV exports + .twbx workbook
└── deliverables/           # case_study.pptx, root_cause_analysis.md
```

## Stock Universe (locked, verify against screener.in before data collection)
**Finance (10)**: HDFC Bank, ICICI Bank, Kotak Mahindra Bank, Bajaj Finance,
Bajaj Finserv, Punjab National Bank, Bank of Baroda, IDFC First Bank, Yes Bank,
IIFL Finance (verify retail tilt before locking)

**Manufacturing (10)**: Larsen & Toubro, Maruti Suzuki, Bajaj Auto, Tata Motors,
Hero MotoCorp, Ashok Leyland, Suzlon Energy, RVNL, BHEL, [10th slot — verify
sector fit before locking, candidate flagged as uncertain in planning]

Tickers use `.NS` suffix for yfinance (e.g. `HDFCBANK.NS`).

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

## Roadmap (numbered steps — see TASKS.md for full detail)
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
- **No scraping of screener.in** — manual CSV entry only (ToS + effort tradeoff)
- **No live/real-time data feed** — this is a static, quarterly-lagging analysis;
  the Tableau KPI flag table is a manual-rerun snapshot, not a continuous system
- **No Docker** for this project's initial scope — venv + requirements.txt only
- **No global (cross-sector) bucket ranking** — within-sector median split only
- **No t-test** — sample size (n=10/bucket) requires Mann-Whitney U
- **No expanding the stock universe or quarter count mid-project** to chase
  significance — a null/weak finding is a valid, reportable outcome
- **No predictive modeling** — descriptive/diagnostic only
- **RCA/PESTEL reasoning happens only after Stage 5's stats verdict is known**,
  and must tie back to the actual confirmed result — not generic speculation
  written before the data is seen
- Every raw-query touchpoint (if any ad-hoc SQL is written) must be parameterized,
  never string-concatenated — standard safety habit regardless of project size
