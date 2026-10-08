"""
Scrape quarterly shareholding % (FII/DII/Govt/Public/Promoter) from screener.in.

NOTE: screener.in ToS disallows automated scraping. Use only for personal,
low-volume, rate-limited pulls. For 20 stocks this is marginal — manual
CSV entry (as originally planned) stays compliant. Use at your own risk.

Usage: python ingest/scrape_shareholding.py
Output: shareholding.csv with columns:
    ticker, quarter_end_date, promoter_pct, fii_pct, dii_pct, public_retail_pct
"""

import time
import csv
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

TICKERS = [
    "HDFCBANK", "ICICIBANK", "KOTAKBANK", "BAJFINANCE",
    "BAJAJFINSV", "PNB", "BANKBARODA", "IDFCFIRSTB",
    "YESBANK", "IIFL",
    "LT", "MARUTI", "BAJAJ-AUTO", "TMPV",  
    "HEROMOTOCO", "ASHOKLEY", "SUZLON", "RVNL",
    "BHEL", "IDEA",
]

MONTH_MAP = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}


def quarter_to_date(label: str) -> str:
    """'Jun 2025' -> '2025-06-30' (approx quarter-end; adjust per month if needed)."""
    mon, year = label.strip().split()
    last_day = {"03": "31", "06": "30", "09": "30", "12": "31"}[MONTH_MAP[mon]]
    return f"{year}-{MONTH_MAP[mon]}-{last_day}"


def scrape_ticker(ticker: str) -> list[dict]:
    url = f"https://www.screener.in/company/{ticker}/consolidated/"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        print(f"  WARNING: {ticker} -> HTTP {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Shareholding table sits inside a section with id="shareholding"
    section = soup.find("section", id="shareholding")
    if section is None:
        print(f"  WARNING: {ticker} -> shareholding section not found")
        return []

    table = section.find("table")
    if table is None:
        print(f"  WARNING: {ticker} -> no table in shareholding section")
        return []

    # Header row: quarter labels
    header_cells = table.find("thead").find_all("th")[1:]  # skip first blank/label col
    quarters = [th.get_text(strip=True) for th in header_cells]

    rows = {}
    for tr in table.find("tbody").find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        label = cells[0].get_text(strip=True).replace("+", "").strip()
        values = [c.get_text(strip=True).replace("%", "") for c in cells[1:]]
        rows[label] = values

    out = []
    for i, q in enumerate(quarters):
        try:
            out.append({
                "ticker": ticker,
                "quarter_end_date": quarter_to_date(q),
                "promoter_pct": rows.get("Promoters", [None] * len(quarters))[i] or None,
                "fii_pct": rows.get("FIIs", [None] * len(quarters))[i],
                "dii_pct": rows.get("DIIs", [None] * len(quarters))[i],
                "public_retail_pct": rows.get("Public", [None] * len(quarters))[i],
            })
        except (IndexError, KeyError):
            continue
    return out


def main():
    all_rows = []
    for ticker in TICKERS:
        print(f"Scraping {ticker}...")
        rows = scrape_ticker(ticker)
        all_rows.extend(rows)
        print(f"  {len(rows)} quarters loaded")
        time.sleep(3)  # polite delay — don't hammer their server

    with open("data/raw/shareholding.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ticker", "quarter_end_date", "promoter_pct",
                        "fii_pct", "dii_pct", "public_retail_pct"],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nDone. {len(all_rows)} rows written to shareholding.csv")


if __name__ == "__main__":
    main()
