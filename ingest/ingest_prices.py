"""
Pull 2 years of daily OHLCV for all 20 NSE stocks via yfinance
and write to the price_data SQLite table.

Usage: python ingest/ingest_prices.py
Done condition: SELECT COUNT(DISTINCT ticker) FROM price_data = 20;
               no ticker under ~450 trading days
"""

import sqlite3
import yfinance as yf
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/retail_behavior.db")
PERIOD = "2y"

TICKERS_NS = [
    "HDFCBANK.NS",   "ICICIBANK.NS",  "KOTAKBANK.NS",  "BAJFINANCE.NS",
    "BAJAJFINSV.NS", "PNB.NS",        "BANKBARODA.NS", "IDFCFIRSTB.NS",
    "YESBANK.NS",    "IIFL.NS",
    "LT.NS",         "MARUTI.NS",     "BAJAJ-AUTO.NS", "TMPV.NS",
    "HEROMOTOCO.NS", "ASHOKLEY.NS",   "SUZLON.NS",     "RVNL.NS",
    "BHEL.NS",       "IDEA.NS",
]
def ingest(conn: sqlite3.Connection, tickers: list[str] = TICKERS_NS) -> None:
    for ticker_ns in tickers:
        ticker = ticker_ns.replace(".NS", "")
        print(f"Fetching {ticker_ns}...")
        raw = yf.download(ticker_ns, period=PERIOD, auto_adjust=True, progress=False)
        if raw.empty:
            print(f"  WARNING: no data returned for {ticker_ns}")
            continue

        df = raw.reset_index()[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df.columns = ["trade_date", "open", "high", "low", "close", "volume"]
        df["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")
        df["ticker"] = ticker

        df.to_sql("price_data", conn, if_exists="append", index=False)
        print(f"  {len(df)} rows loaded")

    conn.commit()


def main() -> None:
    import sys
    conn = sqlite3.connect(DB_PATH)

    if len(sys.argv) > 1:
        # single-ticker mode: python ingest/ingest_prices.py TMPV.NS
        ingest(conn, tickers=[sys.argv[1]])
    else:
        ingest(conn, tickers=TICKERS_NS)

    stats = pd.read_sql(
        "SELECT ticker, COUNT(*) AS days FROM price_data GROUP BY ticker ORDER BY days",
        conn,
    )
    print(stats.to_string(index=False))
    conn.close()
    
def check_data() -> None:
    import sys
    conn = sqlite3.connect(DB_PATH)

    stats = pd.read_sql(
        "DELETE FROM price_data WHERE ticker = 'TMPV';",
        conn,
    )
    print(stats)
    conn.close()
    
if __name__ == "__main__":
    main()
    #check_data()
