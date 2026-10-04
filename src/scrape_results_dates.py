"""
Scrape quarterly Financial Results announcement dates from NSE's public
corporate-announcements API, for each ticker, matched to the target
quarter-end dates.

NOTE: NSE's ToS also restricts automated scraping. Use low volume,
rate-limited, personal use only (same caveat as the shareholding scraper).

Usage: python scrape_results_dates.py
Output: results_dates.csv with columns: ticker, quarter_end_date, results_date
"""

import time
import csv
import re
import requests
from datetime import datetime, timedelta

TICKERS_NS = [
    "HDFCBANK.NS",   "ICICIBANK.NS",  "KOTAKBANK.NS",  "BAJFINANCE.NS",
    "BAJAJFINSV.NS", "PNB.NS",        "BANKBARODA.NS", "IDFCFIRSTB.NS",
    "YESBANK.NS",    "IIFL.NS",
    "LT.NS",         "MARUTI.NS",     "BAJAJ-AUTO.NS", "TMPV.NS",
    "HEROMOTOCO.NS", "ASHOKLEY.NS",   "SUZLON.NS",     "RVNL.NS",
    "BHEL.NS",       "IDEA.NS",
]

TARGET_QUARTERS = [
    "2024-09-30", "2024-12-31", "2025-03-31", "2025-06-30",
    "2025-09-30", "2025-12-31", "2026-03-31", "2026-06-30",
]

# Fetch a wide enough window to cover all 8 quarters' results
# (results usually land 3-7 weeks after quarter-end)
FROM_DATE = "01-07-2024"
TO_DATE = "31-10-2026"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json",
}


def get_session() -> requests.Session:
    """NSE blocks requests without a valid session/cookies from visiting the site first."""
    s = requests.Session()
    s.headers.update(HEADERS)
    s.get("https://www.nseindia.com", timeout=10)  # sets cookies
    time.sleep(1)
    return s


def fetch_announcements(session: requests.Session, symbol: str) -> list[dict]:
    url = "https://www.nseindia.com/api/corporate-announcements"
    params = {
        "index": "equities",
        "symbol": symbol,
        "from_date": FROM_DATE,
        "to_date": TO_DATE,
    }
    resp = session.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        print(f"  WARNING: {symbol} -> HTTP {resp.status_code}")
        return []
    try:
        return resp.json()
    except ValueError:
        print(f"  WARNING: {symbol} -> could not parse JSON (likely blocked)")
        return []


def is_results_announcement(item: dict) -> bool:
    desc = (item.get("desc") or "").lower()
    subject = (item.get("subject") or item.get("attchmntText") or "").lower()
    return "financial result" in desc or "financial result" in subject \
        or "board meeting" in desc and "result" in subject


def nearest_quarter_end(ann_date: datetime) -> str | None:
    """Match an announcement date to the quarter it most likely reports on
    (results land 3-7 weeks after quarter-end, so look backward)."""
    best, best_gap = None, timedelta(days=9999)
    for q in TARGET_QUARTERS:
        q_date = datetime.strptime(q, "%Y-%m-%d")
        gap = ann_date - q_date
        if timedelta(days=0) <= gap <= timedelta(days=60) and gap < best_gap:
            best, best_gap = q, gap
    return best


def scrape_ticker(session: requests.Session, ticker_ns: str) -> list[dict]:
    symbol = ticker_ns.replace(".NS", "")
    print(f"Fetching {symbol}...")
    items = fetch_announcements(session, symbol)

    found = {}
    for item in items:
        if not is_results_announcement(item):
            continue
        raw_date = item.get("an_dt") or item.get("sort_date") or item.get("attchmntDate")
        if not raw_date:
            continue
        try:
            ann_date = datetime.strptime(raw_date.split()[0], "%d-%b-%Y")
        except ValueError:
            try:
                ann_date = datetime.strptime(raw_date.split()[0], "%Y-%m-%d")
            except ValueError:
                continue

        q = nearest_quarter_end(ann_date)
        if q and q not in found:  # keep earliest/first match per quarter
            found[q] = ann_date.strftime("%Y-%m-%d")

    rows = [
        {"ticker": symbol, "quarter_end_date": q, "results_date": found.get(q)}
        for q in TARGET_QUARTERS
    ]
    missing = [q for q in TARGET_QUARTERS if q not in found]
    if missing:
        print(f"  WARNING: {symbol} -> missing results_date for quarters: {missing}")
    else:
        print(f"  all 8 quarters matched")
    return rows


def main():
    session = get_session()
    all_rows = []
    for ticker_ns in TICKERS_NS:
        rows = scrape_ticker(session, ticker_ns)
        all_rows.extend(rows)
        time.sleep(3)  # polite delay

    with open("results_dates.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ticker", "quarter_end_date", "results_date"])
        writer.writeheader()
        writer.writerows(all_rows)

    filled = sum(1 for r in all_rows if r["results_date"])
    print(f"\nDone. {filled}/{len(all_rows)} rows have a results_date. Written to results_dates.csv")


if __name__ == "__main__":
    main()
