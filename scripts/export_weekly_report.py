#!/usr/bin/env python3
"""
export_weekly_report.py — dump all signals (+ live price/slippage) to CSV.

Run this ON THE VPS (it connects to the local Postgres container) whenever
you want a report — typically once a week.

Usage:
    # last 7 days (default)
    python3 scripts/export_weekly_report.py

    # custom range
    python3 scripts/export_weekly_report.py --days 14
    python3 scripts/export_weekly_report.py --since 2026-09-01 --until 2026-09-28

Output:
    Writes a CSV file to ./reports/signals_<from>_<to>.csv
    Then just download it to your laptop and open/import into Google Sheets:
        scp root@65.20.79.45:/opt/stack/reports/signals_*.csv ~/Downloads/
    In Google Sheets: File > Import > Upload > select the CSV > "Insert new sheet".
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from datetime import date, timedelta


DEFAULT_DB_CONTAINER = os.environ.get("PG_CONTAINER", "stack-postgres")
DEFAULT_DB_NAME = os.environ.get("PG_DB", "n8n")
DEFAULT_DB_USER = os.environ.get("PG_USER", "stackadmin")

QUERY = """
COPY (
  SELECT
    s.id                     AS signal_id,
    s.posted_at              AS posted_at,
    s.source_group           AS source_group,
    s.stock_name_raw         AS stock_name_raw,
    s.nse_symbol             AS nse_symbol,
    s.trade_type             AS trade_type,
    s.entry_price            AS advisor_entry,
    s.stop_loss              AS stop_loss,
    s.targets                AS targets,
    s.confidence             AS confidence,
    s.extractor              AS extractor,
    smc.price_at_capture     AS live_price_at_capture,
    smc.slippage_pct         AS slippage_pct,
    smc.captured_at          AS price_captured_at,
    s.raw_text               AS raw_text
  FROM signals s
  LEFT JOIN signals_market_context smc ON smc.signal_id = s.id
  WHERE s.posted_at BETWEEN %(since)s AND %(until)s
  ORDER BY s.posted_at ASC
) TO STDOUT WITH CSV HEADER
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default 7)")
    parser.add_argument("--since", type=str, default=None, help="Start date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--until", type=str, default=None, help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--out-dir", type=str, default="./reports", help="Output directory (default ./reports)")
    args = parser.parse_args()

    until = args.until or date.today().isoformat()
    since = args.since or (date.today() - timedelta(days=args.days)).isoformat()

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, f"signals_{since}_{until}.csv")

    sql = QUERY.replace("%(since)s", f"'{since}'::timestamptz") \
                .replace("%(until)s", f"'{until} 23:59:59'::timestamptz")

    cmd = [
        "docker", "exec", "-i", DEFAULT_DB_CONTAINER,
        "psql", "-U", DEFAULT_DB_USER, "-d", DEFAULT_DB_NAME,
        "-c", sql,
    ]

    print(f"Exporting signals from {since} to {until} ...", file=sys.stderr)
    with open(out_path, "wb") as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print(result.stderr.decode(), file=sys.stderr)
        return 1

    row_count = sum(1 for _ in open(out_path)) - 1  # minus header
    print(f"✅ Wrote {row_count} signal rows to {out_path}", file=sys.stderr)
    print(f"\nDownload it to your laptop with:", file=sys.stderr)
    print(f"  scp root@65.20.79.45:{os.path.abspath(out_path)} ~/Downloads/", file=sys.stderr)
    print(f"\nThen in Google Sheets: File > Import > Upload > select the file.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
