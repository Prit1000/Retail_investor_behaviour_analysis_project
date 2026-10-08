"""
Load manual screener.in CSVs (shareholding_manual.csv, results_dates.csv)
into SQLite tables: stocks, shareholding.

Usage: python src/load_shareholding.py
Done condition: SELECT COUNT(*) FROM shareholding = 160 (20 stocks x 8 quarters)
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/retail_behavior.db")
SHAREHOLDING_CSV = Path("data/raw/shareholding.csv")
RESULTS_CSV = Path("data/raw/results_dates.csv")

STOCKS = [
    # (ticker, company_name, sector, expected_retail_tilt)
    ("HDFCBANK",   "HDFC Bank",                "Finance",       "Low"),
    ("ICICIBANK",  "ICICI Bank",               "Finance",       "Low"),
    ("KOTAKBANK",  "Kotak Mahindra Bank",       "Finance",       "Low"),
    ("BAJFINANCE", "Bajaj Finance",             "Finance",       "Low"),
    ("BAJAJFINSV", "Bajaj Finserv",             "Finance",       "Low-Medium"),
    ("PNB",        "Punjab National Bank",      "Finance",       "Medium-High"),
    ("BANKBARODA", "Bank of Baroda",            "Finance",       "Medium-High"),
    ("IDFCFIRSTB", "IDFC First Bank",           "Finance",       "Medium"),
    ("YESBANK",    "Yes Bank",                  "Finance",       "High"),
    ("IIFL",       "IIFL Finance",              "Finance",       "High"),
    ("LT",         "Larsen & Toubro",           "Manufacturing", "Low"),
    ("MARUTI",     "Maruti Suzuki",             "Manufacturing", "Low"),
    ("BAJAJ-AUTO", "Bajaj Auto",               "Manufacturing", "Low"),
    ("TMPV",       "Tata Motors",               "Manufacturing", "Low-Medium"),
    ("HEROMOTOCO", "Hero MotoCorp",             "Manufacturing", "Medium"),
    ("ASHOKLEY",   "Ashok Leyland",             "Manufacturing", "Medium"),
    ("SUZLON",     "Suzlon Energy",             "Manufacturing", "High"),
    ("RVNL",       "RVNL",                      "Manufacturing", "High"),
    ("BHEL",       "BHEL",                      "Manufacturing", "High"),
    ("IDEA",       "Vodafone Idea",             "Manufacturing", "High"),  # verify sector fit
]


def seed_stocks(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO stocks VALUES (?, ?, ?, ?)",
        STOCKS,
    )
    conn.commit()


def load_shareholding(conn: sqlite3.Connection) -> None:
    df = pd.read_csv(SHAREHOLDING_CSV)
    results = pd.read_csv(RESULTS_CSV)
    # left join: quarters without a results date keep results_date = NULL
    df = df.merge(results, on=["ticker", "quarter_end_date"], how="left")
    df.to_sql("shareholding", conn, if_exists="append", index=False)
    conn.commit()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    seed_stocks(conn)
    load_shareholding(conn)

    count = conn.execute("SELECT COUNT(*) FROM shareholding").fetchone()[0]
    print(f"shareholding rows loaded: {count}")
    conn.close()


if __name__ == "__main__":
    main()
