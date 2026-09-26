#!/usr/bin/env python3
"""
extract_signals.py — offline validator for the MSK signal grammar.

Reads a WhatsApp chat export (Markdown) and prints extracted signals as JSONL.
Use this to tune the regex before wiring it into n8n.

Usage:
    python3 scripts/extract_signals.py "/path/to/chat.md" > signals.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Iterator


# ------------------------------------------------------------------ regex

MSG_HEADER_RE = re.compile(
    r"^\[(?P<time>\d{1,2}:\d{2})\]\s+\*\*(?P<sender>[^*]+)\*\*:?\s*(?P<body>.*)$"
)
DATE_HEADER_RE = re.compile(r"^##\s+(?P<date>\d{1,2}\s+\w+\s+\d{4})\s*$")

SIGNAL_RE = re.compile(
    r"""
    (?:(?P<trade_type>POSITIONAL\s+TRADE|INTRADAY\s+TRADE|BTST\s+TRADE)\s*[\r\n]+)?
    \s*(?P<stock>[A-Z][A-Z0-9&\.\- ]{1,40}?)\s*[\r\n]+\s*
    Looks\s+Good\s+ABOVE\s+(?P<entry>\d+(?:\.\d+)?)\s*[\r\n]+\s*
    SL\s+(?P<sl>\d+(?:\.\d+)?)\s*[\r\n]+\s*
    Targets?\s+(?P<targets>[\d\.\-\+\s]+?)
    (?P<points>\s*points?\s+from\s+entry)?
    (?:\s*[\r\n]|$)
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)

TARGET_HIT_RE = re.compile(r"🔥.*We shared the research", re.IGNORECASE)


# ------------------------------------------------------------------ data

@dataclass
class Signal:
    posted_date: str
    posted_time: str
    trade_type: str | None
    stock_name_raw: str
    entry_price: float
    stop_loss: float
    targets: list[float] = field(default_factory=list)
    targets_mode: str = "absolute"       # 'absolute' | 'points_from_entry'
    raw_snippet: str = ""


# ------------------------------------------------------------------ parse

def parse_targets(raw: str) -> list[float]:
    # normalise "48-50-53-55+58-60" -> ["48","50","53","55","58","60"]
    cleaned = re.sub(r"[+\s]+", "-", raw.strip().strip("-"))
    parts = [p for p in cleaned.split("-") if p]
    out: list[float] = []
    for p in parts:
        try:
            out.append(float(p))
        except ValueError:
            continue
    return out


def iter_messages(md_path: str) -> Iterator[tuple[str, str, str, str]]:
    """Yield (date, time, sender, body) tuples. Multi-line messages are joined."""
    current_date = ""
    current: dict | None = None
    with open(md_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            dm = DATE_HEADER_RE.match(line)
            if dm:
                current_date = dm.group("date")
                continue
            hm = MSG_HEADER_RE.match(line)
            if hm:
                if current:
                    yield current["date"], current["time"], current["sender"], current["body"]
                current = {
                    "date": current_date,
                    "time": hm.group("time"),
                    "sender": hm.group("sender"),
                    "body": hm.group("body"),
                }
                continue
            if current is not None:
                current["body"] += "\n" + line
    if current:
        yield current["date"], current["time"], current["sender"], current["body"]


def extract_from_body(dt: str, tm: str, body: str) -> Signal | None:
    if TARGET_HIT_RE.search(body):
        return None
    if "[Image]" in body and "Looks Good ABOVE" not in body:
        return None
    m = SIGNAL_RE.search(body)
    if not m:
        return None
    entry = float(m.group("entry"))
    sl = float(m.group("sl"))
    targets = parse_targets(m.group("targets"))
    mode = "points_from_entry" if m.group("points") else "absolute"
    if mode == "points_from_entry":
        targets = [round(entry + t, 2) for t in targets]
    return Signal(
        posted_date=dt,
        posted_time=tm,
        trade_type=(m.group("trade_type") or "").strip().upper() or None,
        stock_name_raw=re.sub(r"\s+", " ", m.group("stock")).strip(),
        entry_price=entry,
        stop_loss=sl,
        targets=targets,
        targets_mode=mode,
        raw_snippet=m.group(0).strip()[:400],
    )


# ------------------------------------------------------------------ main

def main(path: str) -> None:
    n_msgs = n_signals = 0
    for dt, tm, sender, body in iter_messages(path):
        n_msgs += 1
        sig = extract_from_body(dt, tm, body)
        if sig is None:
            continue
        n_signals += 1
        print(json.dumps(asdict(sig), ensure_ascii=False))
    print(
        f"# processed={n_msgs} signals={n_signals}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: extract_signals.py <chat.md>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
