"""
Compute Metric A (volume spike ratio, price range %) and Metric B (realized vol)
for each stock-quarter at ±3d and ±5d event windows.
Results written to metrics_results table.

Usage: python src/metrics.py
Done condition: SELECT COUNT(*) FROM metrics_results = 160 (20 stocks x 8 quarters x 2 windows...
                actually 20 x 8 x 2 = 320 rows, one per ticker-quarter-window combination)
"""

import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path

from metrics.assign_buckets import assign_buckets

DB_PATH = Path("data/retail_behavior.db")
WINDOWS = [3, 5]
BASELINE_DAYS = 30


def get_trading_dates(prices: pd.DataFrame, anchor_date: str, n: int) -> pd.DataFrame:
    """Return n trading days before or after anchor_date (exclusive of anchor)."""
    dates = prices["trade_date"].sort_values().values
    idx = np.searchsorted(dates, anchor_date)
    return idx


def compute_metrics_for_row(
    ticker: str,
    results_date: str,
    quarter_end_date: str,
    prices: pd.DataFrame,
    window: int,
) -> dict | None:
    dates = np.array(sorted(prices["trade_date"].unique()))
    idx = int(np.searchsorted(dates, results_date))

    event_dates = dates[max(0, idx - window): idx + window + 1]
    baseline_end = max(0, idx - window)
    baseline_start = max(0, baseline_end - BASELINE_DAYS)
    baseline_dates = dates[baseline_start:baseline_end]

    if len(event_dates) == 0 or len(baseline_dates) == 0:
        return None

    ev = prices[prices["trade_date"].isin(event_dates)].copy()
    bl = prices[prices["trade_date"].isin(baseline_dates)].copy()

    if ev.empty or bl.empty:
        return None

    ev_vol_avg = ev["volume"].mean()
    bl_vol_avg = bl["volume"].mean()
    volume_spike_ratio = ev_vol_avg / bl_vol_avg if bl_vol_avg > 0 else None

    ev["range_pct"] = (ev["high"] - ev["low"]) / ev["close"]
    bl["range_pct"] = (bl["high"] - bl["low"]) / bl["close"]
    ev_range_avg = ev["range_pct"].mean()
    bl_range_avg = bl["range_pct"].mean()
    price_range_pct = ev_range_avg / bl_range_avg if bl_range_avg > 0 else None

    ev["log_ret"] = np.log(ev["close"] / ev["close"].shift(1))
    realized_vol = ev["log_ret"].std() if len(ev) > 1 else None

    return {
        "ticker": ticker,
        "quarter_end_date": quarter_end_date,
        "results_date": results_date,
        "window_days": window,
        "volume_spike_ratio": volume_spike_ratio,
        "price_range_pct": price_range_pct,
        "realized_vol": realized_vol,
        "bucket": None,  # filled by assign_buckets() in main()
    }


def main() -> None:
    conn = sqlite3.connect(DB_PATH)

    results_df = pd.read_sql(
        "SELECT ticker, quarter_end_date, results_date FROM shareholding WHERE results_date IS NOT NULL",
        conn,
    )

    all_rows = []
    for _, row in results_df.iterrows():
        prices = pd.read_sql(
            "SELECT trade_date, open, high, low, close, volume FROM price_data WHERE ticker = ?",
            conn,
            params=(row["ticker"],),
        )
        for w in WINDOWS:
            metrics = compute_metrics_for_row(
                row["ticker"], row["results_date"], row["quarter_end_date"], prices, w
            )
            if metrics:
                all_rows.append(metrics)

    if all_rows:
        df_out = pd.DataFrame(all_rows)
        df_out.to_sql("metrics_results", conn, if_exists="replace", index=False)
        print(f"metrics_results rows written: {len(df_out)}")
        assign_buckets(conn)  # within-sector median split on public_retail_pct
        print("bucket column populated (within-sector median split)")
    else:
        print("No rows computed — check that shareholding and price_data are populated.")

    conn.close()


if __name__ == "__main__":
    main()
