# Instruction File — Retail-Heavy Stocks vs. Results-Season Volatility

This is the Build-Planner-generated summary of this specific project's locked
plan. Read alongside the repo's own `CLAUDE.md` (which Claude Code reads every
session) — this file is the "why" behind the decisions; `CLAUDE.md` is the
"what" for day-to-day execution.

## Problem
Do retail-heavy stocks show more erratic price/volume behavior around results
season than institution-heavy stocks? Framed as a BA case study
(Question → Finding → Root Cause → Pain Point → Recommendation), backed by a
formal hypothesis test — not a narrative-only argument.

## Locked Decisions (do not re-litigate without going back to discussion)

| Decision | Choice | Why |
|---|---|---|
| Universe | 20 stocks: 10 Finance + 10 Manufacturing | Deliberate spread of expected retail ownership per sector |
| History | 8 quarters (2 years) | Balances statistical usefulness against manual data-entry cost |
| Bucketing | Binned, within-sector median split | n=20 too thin for correlation; within-sector avoids sector confound |
| Metrics | Both A (volume spike ratio + price range %) and B (realized volatility) | A is intuitive for BA narrative, B is the quant-standard measure — together give robustness |
| Window | ±3 trading days primary, ±5 robustness check | Retail reaction may lag — ±3-only risks biasing against the hypothesis being tested |
| Stats test | Mann-Whitney U | n=10/bucket too small to assume normality (t-test's core assumption) |
| DB | SQLite | Single-user, read-mostly, no deployment target — Postgres/Docker is over-engineering here |
| Dashboard | Tableau | Deliberate skill-building choice, not the user's default (Power BI) |
| Env | venv + requirements.txt | Static analysis, no running service — Docker is a legitimate *later* add-on, not day-1 |
| Repo | Standalone, not inside `da-finance-course-repo` | This is original analysis, not course-curriculum work — deserves its own portfolio link |

## Pipeline (do not reorder)
```
Data Collection → SQL → Pre-Metric EDA + Hypothesis → Python Metrics →
Post-Metric EDA + Stats Test → Root Cause (RCA + PESTEL, manual) → Tableau + PPT
```

The Root Cause stage (RCA/PESTEL) is explicitly sequenced **after** the stats
verdict is known — it explains a confirmed result, it does not precede or
replace the hypothesis test. This is a BA reasoning layer, done manually by
the user, feeding directly into the PPT's "Root Cause" section.

## Risks Already Identified (see CLAUDE.md "Hard Rules" for the mitigations)
- Manual data entry errors (160 cells)
- Small sample size (n=10/bucket) — mitigated by running 4 metric/window
  combinations and checking for a *consistent* direction, not one p-value
- Results date may not match true market reaction date (Indian market lag) —
  mitigated by the ±5d robustness window
- Sector confound — mitigated by within-sector bucketing
- Data availability gaps for less-liquid names (Yes Bank, Suzlon, and the two
  explicitly flagged "verify" placeholder stocks)
- Corporate action noise (splits/bonus/mergers) — mitigated by `auto_adjust=True`

## Explicitly Out of Scope
No live data feed, no Docker (yet), no screener.in scraping, no correlation-based
stats, no mid-project universe expansion, no predictive modeling, no sector
expansion beyond Finance + Manufacturing, no external data sources (news
sentiment, social media) beyond what's already in scope for RCA/PESTEL
reasoning (which is qualitative, not a new data pipeline).

## If the Idea Itself Needs to Change
If execution reveals the core question can't be answered with this data (e.g.
screener.in data for the "verify" placeholder stocks turns out unusable), flag
it and consider whether this needs to go back to Idea Lab — don't silently
redefine the question inside execution.
