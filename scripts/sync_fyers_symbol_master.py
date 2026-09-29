#!/usr/bin/env python3
"""Refresh the local NSE cash equity symbol master from Fyers."""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

MASTER_URL = "https://public.fyers.in/sym_details/NSE_CM.csv"
DB_CONTAINER = "stack-postgres"
DB_NAME = "n8n"
DB_USER = "stackadmin"

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS fyers_nse_symbols (
    nse_symbol TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    isin TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS fyers_nse_symbols_staging (
    nse_symbol TEXT NOT NULL,
    company_name TEXT NOT NULL,
    isin TEXT
);
"""


def normalize(value: str) -> str:
    return "".join(char for char in value.upper() if char.isalnum())


def read_master() -> list[tuple[str, str, str | None]]:
    request = urllib.request.Request(MASTER_URL, headers={"User-Agent": "TradeBot/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        rows = csv.reader(io.StringIO(response.read().decode("utf-8-sig")))
        instruments: dict[str, tuple[str, str | None]] = {}
        for row in rows:
            if len(row) <= 9:
                continue
            full_symbol = row[9].strip()
            if not full_symbol.startswith("NSE:") or not full_symbol.endswith("-EQ"):
                continue
            symbol = full_symbol[4:-3]
            company_name = row[1].strip()
            isin = row[5].strip() or None
            if symbol and company_name:
                instruments[symbol] = (company_name, isin)

    if len(instruments) < 1000:
        raise RuntimeError(f"Fyers master looked incomplete: only {len(instruments)} EQ symbols")
    return [(symbol, name, isin) for symbol, (name, isin) in instruments.items()]


def resolve_name(name: str, instruments: list[tuple[str, str, str | None]]) -> tuple[str | None, str, list[str]]:
    key = normalize(name)
    if len(key) < 4:
        return None, "unresolved", []

    matches = [(symbol, normalize(company)) for symbol, company, _ in instruments]
    exact = sorted({symbol for symbol, company in matches if company == key})
    candidates = exact or sorted({symbol for symbol, company in matches if company.startswith(key)})
    if len(candidates) == 1:
        return candidates[0], "resolved", candidates
    return None, "ambiguous" if candidates else "unresolved", candidates


def psql(sql: str, *, data: str | None = None) -> subprocess.CompletedProcess[str]:
    command = ["docker", "exec", "-i", DB_CONTAINER, "psql", "-X", "-v", "ON_ERROR_STOP=1", "-U", DB_USER, "-d", DB_NAME]
    if data is None:
        command.extend(["-c", sql])
    else:
        command.extend(["-c", sql])
    return subprocess.run(command, input=data, text=True, capture_output=True, check=True)


def refresh(instruments: list[tuple[str, str, str | None]]) -> None:
    psql(CREATE_TABLES_SQL)
    psql("TRUNCATE fyers_nse_symbols_staging")

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerows(instruments)
    psql("COPY fyers_nse_symbols_staging (nse_symbol, company_name, isin) FROM STDIN WITH (FORMAT CSV)", data=output.getvalue())

    psql("""
BEGIN;
DELETE FROM fyers_nse_symbols;
INSERT INTO fyers_nse_symbols (nse_symbol, company_name, isin, updated_at)
SELECT nse_symbol, company_name, isin, NOW()
FROM fyers_nse_symbols_staging
ON CONFLICT (nse_symbol) DO UPDATE
SET company_name = EXCLUDED.company_name, isin = EXCLUDED.isin, updated_at = NOW();
TRUNCATE fyers_nse_symbols_staging;
COMMIT;
""")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Download and test common names without updating Postgres")
    args = parser.parse_args()

    try:
        instruments = read_master()
        print(f"Read {len(instruments)} Fyers NSE cash EQ instruments.")
        for name in ("PRASOL CHEM", "MANIPAL PAYMENT", "AZAD", "CHENNAI PETRO", "HERO MOTORS"):
            symbol, status, candidates = resolve_name(name, instruments)
            print(f"{name}: {status}; ticker={symbol or '-'}; candidates={','.join(candidates) or '-'}")
        if not args.check_only:
            refresh(instruments)
            print(f"Updated fyers_nse_symbols at {datetime.now(timezone.utc).isoformat()}.")
    except Exception as error:
        print(f"Symbol-master refresh failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
