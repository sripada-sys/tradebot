#!/usr/bin/env python3
"""
seed_symbols.py — build an initial stock-name → NSE-symbol map from the chat history.

Emits a CSV that a human can review before loading into Postgres.

Usage:
    python3 scripts/extract_signals.py chat.md > signals.jsonl
    python3 scripts/seed_symbols.py signals.jsonl > symbols_draft.csv
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter


def main(path: str) -> None:
    counts: Counter[str] = Counter()
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            counts[obj["stock_name_raw"]] += 1

    writer = csv.writer(sys.stdout)
    writer.writerow(["stock_name_raw", "occurrences", "nse_symbol_guess", "verified"])
    for name, n in counts.most_common():
        guess = name.replace(" LTD", "").replace(" LIMITED", "").replace(" ", "")
        writer.writerow([name, n, guess, "false"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: seed_symbols.py <signals.jsonl>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
