"""
Bucket stocks by within-sector median split on public_retail_pct,
then run Mann-Whitney U test for each metric x window combination.

Outputs p-value + verdict for all 4 combinations:
  - Metric A (volume_spike_ratio)  x ±3d
  - Metric A (volume_spike_ratio)  x ±5d
  - Metric B (realized_vol)        x ±3d
  - Metric B (realized_vol)        x ±5d

Usage: python src/stats_test.py
"""

import sqlite3
import pandas as pd
from scipy.stats import mannwhitneyu
from pathlib import Path

DB_PATH = Path("data/retail_behavior.db")
ALPHA = 0.05


def assign_buckets(conn: sqlite3.Connection) -> pd.DataFrame:
    sh = pd.read_sql("""
        SELECT s.ticker, s.sector, sh.quarter_end_date, sh.public_retail_pct
        FROM stocks s
        JOIN shareholding sh ON s.ticker = sh.ticker
    """, conn)

    # within-sector median split, computed PER QUARTER (not collapsed to an all-quarter average)
    sector_quarter_median = sh.groupby(["sector", "quarter_end_date"])["public_retail_pct"].transform("median")
    sh["bucket"] = (sh["public_retail_pct"] > sector_quarter_median).map({True: "High", False: "Low"})

    # write bucket back to metrics_results — row-level match, not ticker-level
    for _, row in sh.iterrows():
        conn.execute(
            "UPDATE metrics_results SET bucket = ? WHERE ticker = ? AND quarter_end_date = ?",
            (str(row["bucket"]), row["ticker"], str(row["quarter_end_date"])),
        )
    conn.commit()
    return sh


def run_tests(conn: sqlite3.Connection) -> None:
    df = pd.read_sql("SELECT * FROM metrics_results", conn)

    metrics = {
        "Metric A – volume_spike_ratio": "volume_spike_ratio",
        "Metric B – realized_vol":       "realized_vol",
    }

    print(f"\n{'='*60}")
    print("Mann-Whitney U Test Results (within-sector buckets)")
    print(f"{'='*60}")

    for label, col in metrics.items():
        for w in [3, 5]:
            sub = df[df["window_days"] == w][["bucket", col]].dropna()
            high = sub[sub["bucket"] == "High"][col].values
            low  = sub[sub["bucket"] == "Low"][col].values

            if len(high) < 2 or len(low) < 2:
                print(f"\n{label} | ±{w}d: insufficient data (High n={len(high)}, Low n={len(low)})")
                continue

            stat, p = mannwhitneyu(high, low, alternative="two-sided")
            verdict = "REJECT H0" if p < ALPHA else "FAIL TO REJECT H0"

            print(f"\n{label} | ±{w}d window")
            print(f"  High-retail n={len(high)}, median={pd.Series(high).median():.4f}")
            print(f"  Low-retail  n={len(low)},  median={pd.Series(low).median():.4f}")
            print(f"  U={stat:.1f}, p={p:.4f}  →  {verdict} (α={ALPHA})")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    buckets = assign_buckets(conn)
    print("Bucket assignment (per ticker-quarter):")
    print(buckets[["ticker", "sector", "quarter_end_date", "public_retail_pct", "bucket"]].to_string(index=False))
    run_tests(conn)
    conn.close()


if __name__ == "__main__":
    main()
