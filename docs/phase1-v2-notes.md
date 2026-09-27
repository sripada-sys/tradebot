# Phase 1 v2 — Enhanced Ingestion

## What's New vs. v1

| Feature | v1 | v2 |
|---|---|---|
| Regex extractor | ✅ 1 pattern | ✅ 2 patterns (MSK + generic Buy/SL/Tgt) |
| LLM fallback | ❌ | ✅ Gemini Flash via OpenRouter |
| Latency tracking | ❌ | ✅ `received_at`, `processed_at` |
| Media messages | Dropped | Logged to `raw_messages` (URL captured) |
| Edit tracking | ❌ | ✅ `MESSAGES_UPDATE` → `message_edits` |
| Market context | ❌ | 🟡 Stub row inserted (Fyers TBD) |
| Self-DM alerts | ❌ | ✅ WhatsApp DM per captured signal |
| Confidence score | Fixed 0.9 | Regex 0.9 / LLM 0.6–0.75 |

## Flow

```
Webhook → Filter/normalize → [Log raw]  (always)
                          ↳ Text? → Regex extract → OK? ─┐
                                                  ↳ Miss → LLM (Gemini Flash) → Signal? ─┘
                                                                                          ↓
                                            Resolve NSE symbol → Insert signal → [Market ctx stub]
                                                                              → [Build alert → Self-DM]
```

## Cost Estimate

- Regex handles ~70–80% of signals → 0 cost
- LLM sees ~20–30% (misses + non-signals)
- Gemini 2.0 Flash Exp is **free tier** on OpenRouter (rate-limited)
- Fallback: `google/gemini-2.0-flash-001` at ~$0.075/1M input tokens

## Confidence Model

Base score by extractor (from `extractor_confidence` table):
- `regex`: 0.90
- `llm`: 0.70 (capped at 0.75 even if LLM reports higher)
- `manual`: 1.00

Future multipliers (Phase 2):
- Latency penalty (older signals → lower confidence)
- Slippage penalty (price already moved > 1% → lower confidence)
- Advisor accuracy (historical win rate)

## Fyers Integration Plan (Later)

The `Seed market context (Fyers TBD)` node currently inserts a stub row with
`source='pending'`. When Fyers is ready:

1. Add HTTP node after that inserts calling Fyers `/quotes` API
2. Update the row with `price_at_message`, `slippage_pct`, `source='fyers'`
3. Backfill pending rows via a scheduled workflow

## Import Checklist

1. In n8n UI → Workflows → Import → `phase1-ingest-v2.json`
2. Fix credential on 4 Postgres nodes → `tradebot-postgres`
3. **Deactivate v1** workflow first (so webhooks route to v2)
4. Activate v2
5. Test by sending yourself a message in one of the 3 groups
