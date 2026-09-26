# Signal format (MSK Fintech)

Derived from 17,847 lines of exported chat history — 881 signal-related messages.

## Canonical grammar

```
<TRADE_TYPE>            # POSITIONAL TRADE | INTRADAY TRADE | BTST TRADE
<STOCK NAME>            # free-form, mapped to NSE symbol separately
Looks Good ABOVE <p>    # entry trigger price
SL <p>                  # stop-loss (absolute)
Targets <t1-t2-...>     # dash-separated
[points from entry]     # optional; if present, targets are relative
Hold few days|weeks     # rough horizon
```

## Examples

### Absolute-target style
```
POSITIONAL TRADE

SAKSOFT
Looks Good ABOVE 173

SL 155

Targets 176-180-185-190-195-200

Hold few weeks
```

### Points-from-entry style
```
POSITIONAL TRADE

M&M
Looks Good ABOVE 3150

SL 3120

Targets 15-30-45-69-75  points from entry

Hold few days
```

## Non-signal messages (must be filtered out)

- **Target-hit celebration** (contains `🔥` + `We shared the research`):
  ```
  SAKSOFT🔥 - We shared the research yesterday only that it looks good above 173
  Today only, it hit a high of 203 potential move of approximately of 18.71% in few days
  ```
- **Reminders / "trail your SL" / motivational text**
- **Image-only messages** (`[Image]`)
- **Member add/remove system messages** (`added +91 ...`)

## Regex extractor (v1)

```python
import re

SIGNAL_RE = re.compile(
    r"""
    (?P<trade_type>POSITIONAL\s+TRADE|INTRADAY\s+TRADE|BTST\s+TRADE)?  # optional header
    .*?
    (?P<stock>[A-Z][A-Z0-9 &\-\.]{1,40})            # ALL-CAPS-ish stock name
    \s*[\r\n]+
    Looks\s+Good\s+ABOVE\s+(?P<entry>\d+(?:\.\d+)?) # entry
    \s*[\r\n]+\s*
    SL\s+(?P<sl>\d+(?:\.\d+)?)                      # stop-loss
    \s*[\r\n]+\s*
    Targets?\s+(?P<targets>[\d\.\-\+ ]+)            # dash-separated numbers
    (?P<points>\s*points?\s+from\s+entry)?          # relative flag
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)
```

## Symbol resolution

Stock names in chat are **display names**, not NSE tickers. Examples of mismatches:

| Chat name       | NSE symbol   |
|-----------------|--------------|
| OLA ELECTRIC    | OLAELEC      |
| CAR TRADE       | CARTRADE     |
| M&M             | M&M          |
| NUVAMA WEALTH   | NUVAMA       |
| SAMMAN CAPITAL  | SAMMANCAP    |
| GLAND PHARMA    | GLAND        |
| ARVIND LTD      | ARVIND       |

Strategy:
1. Look up in `symbols` table (seeded manually + from history).
2. Fall back to fuzzy-match against Fyers symbol master CSV.
3. Log unresolved names to `unresolved_symbols` for manual review.

See `scripts/seed_symbols.py`.

## Points-from-entry conversion

When `points from entry` flag is set:

```python
targets_absolute = [entry + p for p in targets_relative]
```

Otherwise use the parsed numbers as-is.

## Deduplication

- Key: `(nse_symbol, entry_price, DATE(posted_at))`.
- Same signal repeated within 24h → ignore.
- Follow-up 🔥 message about the *same* symbol → not a new signal.
