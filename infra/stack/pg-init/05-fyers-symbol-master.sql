CREATE TABLE IF NOT EXISTS fyers_nse_symbols (
  nse_symbol   TEXT PRIMARY KEY,
  company_name TEXT NOT NULL,
  isin         TEXT,
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fyers_nse_symbols_staging (
  nse_symbol   TEXT NOT NULL,
  company_name TEXT NOT NULL,
  isin         TEXT
);
