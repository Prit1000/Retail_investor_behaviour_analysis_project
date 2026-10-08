-- stocks: one row per NSE-listed company in the universe
CREATE TABLE IF NOT EXISTS stocks (
    ticker              TEXT PRIMARY KEY,  -- NSE symbol without .NS (e.g. HDFCBANK)
    company_name        TEXT NOT NULL,
    sector              TEXT NOT NULL,     -- 'Finance' or 'Manufacturing'
    expected_retail_tilt TEXT             -- Low / Low-Medium / Medium / Medium-High / High
);

-- shareholding: one row per stock per quarter from screener.in script pulling
CREATE TABLE IF NOT EXISTS shareholding (
    ticker              TEXT NOT NULL,
    quarter_end_date    TEXT NOT NULL,     -- ISO date e.g. 2024-03-31
    promoter_pct        REAL,
    fii_pct             REAL,
    dii_pct             REAL,
    public_retail_pct   REAL,             -- the key independent variable
    results_date        TEXT,              -- ISO date of quarterly results announcement
    PRIMARY KEY (ticker, quarter_end_date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- price_data: daily OHLCV from yfinance, auto_adjust=True
CREATE TABLE IF NOT EXISTS price_data (
    ticker              TEXT NOT NULL,
    trade_date          TEXT NOT NULL,     -- ISO date e.g. 2024-01-15
    open                REAL,
    high                REAL,
    low                 REAL,
    close               REAL,
    volume              INTEGER,
    PRIMARY KEY (ticker, trade_date),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);

-- metrics_results: computed event-window metrics, one row per stock-quarter-window
CREATE TABLE IF NOT EXISTS metrics_results (
    ticker              TEXT NOT NULL,
    quarter_end_date    TEXT NOT NULL,
    results_date        TEXT NOT NULL,     -- actual announcement date from screener.in
    window_days         INTEGER NOT NULL,  -- 3 (primary) or 5 (robustness)
    volume_spike_ratio  REAL,             -- Metric A: event avg volume / baseline avg volume
    price_range_pct     REAL,             -- Metric A: event avg daily range / baseline avg daily range
    realized_vol        REAL,             -- Metric B: std dev of log returns over event window
    bucket              TEXT,             -- 'High' or 'Low' retail (within-sector median split)
    PRIMARY KEY (ticker, quarter_end_date, window_days),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker)
);
