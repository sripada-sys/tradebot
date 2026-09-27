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
- **Phase 1** (signal capture) — ✅ pipeline verified end-to-end with simulated real signal (webhook → filter → regex → insert). Real advisor signal still pending (waiting on live market chatter).
- **Phase 1.5** (Fyers price + slippage) — ✅ done. Signal insert now triggers live Fyers price lookup + auto slippage calc, verified: RELIANCE @1200 advisor entry vs 1226 live price = +2.167% slippage.
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

## Fixed Bugs (found while wiring Fyers)

These were **latent since Phase 1**, never triggered because no real signal had made it through the full pipeline before:
- `Log raw message`, `Insert signal`, `Log LLM usage`, `Resolve NSE symbol`, `Seed market context` — all used a fragile comma-joined `queryParameters` string that broke on null/boolean values. Fixed to use `options.queryReplacement` with a JS array (the pattern proven working in the Fyers auth-catcher).
- `Merge regex+LLM` was set to `mergeByPosition` mode, which requires "Fields to Match" — but design intent was "take whichever branch has data". Fixed to `append` mode (no field matching needed since only one branch ever has output).
- `symbols` table didn't have RELIANCE seeded (only 190 names from historical chat export). Added directly via SQL. **Action item**: seed more common NSE names as real signals reveal gaps — no code needed, just `INSERT INTO symbols ...`.

**Lesson for future changes**: n8n v2.40.7 sometimes keeps executing a stale in-memory compiled workflow even after DB updates + restart. When node/connection edits don't seem to take effect, do a full delete + reimport (see workflow_history/webhook_entity/workflow_published_version cascade in git history) rather than patching in place.

## Known Non-Issues

- v2 workflow has 20 nodes (17 orig + 3 Fyers) — more than the 3 rules would suggest. Not simplifying yet; will revisit if it causes real pain.

## Fyers Daily Re-Auth (SEBI restriction — no automated refresh)

SEBI disabled the `refresh_token` API for retail apps. `access_token` expires ~24h and must be renewed once/day. **Mobile-friendly — one tap, no laptop needed:**

1. On any phone logged into Fyers, open this bookmark (note: `http`, not `https` — our webhook has no TLS cert):
   `https://api-t1.fyers.in/api/v3/generate-authcode?client_id=E6XKAQNPSE-100&redirect_uri=http://65.20.79.45:5678/webhook/fyers-auth&response_type=code&state=tradebot`
2. Tap authorize. Fyers redirects to our n8n webhook (`fyers-auth-catcher` workflow), which **automatically** exchanges the code and saves the new token to the `fyers_token` DB table. No copy-paste needed.
3. Page shows "Workflow was started" — done. Token is live for other workflows to use (query `SELECT access_token FROM fyers_token WHERE id=1`).

**Verified working end-to-end 2026-09-27 23:46** — real mobile tap → token saved → live RELIANCE quote fetched successfully.

Fyers app redirect URL registered as: `http://65.20.79.45:5678/webhook/fyers-auth` (must match exactly, or you'll get `ERR_SSL_PROTOCOL_ERROR`).

Secrets live in `/opt/stack/.env` on VPS only: `FYERS_APP_ID`, `FYERS_SECRET_KEY`, `FYERS_APP_HASH` (precomputed sha256, used by n8n), `FYERS_ACCESS_TOKEN` (legacy, superseded by DB table), `FYERS_REFRESH_TOKEN` (unused — SEBI block), `FYERS_PIN`.

**Workflow**: `fyersAuthCatcher01` in n8n — webhook `GET /webhook/fyers-auth` → exchange code with Fyers → `INSERT ... ON CONFLICT UPDATE` into `fyers_token` table.

## Next Action

Wait for one real signal in any target group to fully close Phase 1, then start Phase 1.5 (add Fyers price lookup to `Insert signal` node).
