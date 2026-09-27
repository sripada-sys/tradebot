# TradeBot Status

**Last updated**: 2026-09-27
**Budget spent**: ~$17 (pre-standards). Remaining cap: $5 for Phases 1.5 → 4.

## What's Live

| Component | State |
|---|---|
| Vultr VPS (65.20.79.45) | ✅ Up |
| Docker stack (postgres, redis, evolution, n8n) | ✅ Healthy |
| Evolution API → WhatsApp (+91 95000 29155) | ✅ Linked |
| Webhook `messages.upsert` + `messages.update` → n8n | ✅ Firing |
| n8n workflow `bf7e41466a2cfac1` (v2, 17 nodes) | ✅ Active |
| DB schemas v1+v2+v3 | ✅ Applied |
| Fyers API (App ID `E6XKAQNPSE-100`) | ✅ Working — quotes tested live |

## Phase Status

- **Phase 0** (infra) — ✅ done
- **Phase 1** (signal capture) — 🟡 pipeline proven with test signal (RELIANCE, id=1). Awaiting first real signal from MSK/IPV/MoneyMavericks to close.
- **Phase 1.5** (Fyers price + slippage) — ⏳ next
- **Phase 2/3/4** — pending

## Target Groups (hardcoded in workflow)

- `919493561700-1545803250@g.us` — MSK Fintech
- `919930599976-1613022548@g.us` — IPV Angels
- `120363427391049099@g.us` — MoneyMavericks

## Verification Commands

```bash
# Signals in DB
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT id, nse_symbol, entry_price, extractor, created_at FROM signals ORDER BY created_at DESC LIMIT 5;'"

# Recent webhook executions
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT id, status, \"startedAt\" FROM execution_entity ORDER BY \"startedAt\" DESC LIMIT 5;'"

# LLM cost today
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT * FROM v_llm_daily_cost;'"
```

## Known Non-Issues

- `raw_messages` is empty → **by design**. Filter runs before Log node; non-target groups and non-text messages (reactions, receipts) are dropped upstream. If we want raw audit later, move Log before Filter.
- v2 workflow has 17 nodes — more than the 3 rules would suggest. Not simplifying yet; will revisit if it causes real pain.

## Fyers Daily Re-Auth (SEBI restriction — no automated refresh)

SEBI disabled the `refresh_token` API for retail apps. `access_token` expires ~24h and must be renewed once/day. **Mobile-friendly — one tap, no laptop needed:**

1. On any phone logged into Fyers, open this bookmark:
   `https://api-t1.fyers.in/api/v3/generate-authcode?client_id=E6XKAQNPSE-100&redirect_uri=https://65.20.79.45:5678/webhook/fyers-auth&response_type=code&state=tradebot`
2. Tap authorize. Fyers redirects to our n8n webhook (`fyers-auth-catcher` workflow), which **automatically** exchanges the code and saves the new token to the `fyers_token` DB table. No copy-paste needed.
3. Page shows "Workflow was started" — done. Token is live for other workflows to use (query `SELECT access_token FROM fyers_token WHERE id=1`).

Secrets live in `/opt/stack/.env` on VPS only: `FYERS_APP_ID`, `FYERS_SECRET_KEY`, `FYERS_APP_HASH` (precomputed sha256, used by n8n), `FYERS_ACCESS_TOKEN` (legacy, superseded by DB table), `FYERS_REFRESH_TOKEN` (unused — SEBI block), `FYERS_PIN`.

**Workflow**: `fyersAuthCatcher01` in n8n — webhook `GET /webhook/fyers-auth` → exchange code with Fyers → `INSERT ... ON CONFLICT UPDATE` into `fyers_token` table.

## Next Action

Wait for one real signal in any target group to fully close Phase 1, then start Phase 1.5 (add Fyers price lookup to `Insert signal` node).
