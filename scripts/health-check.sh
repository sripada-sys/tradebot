#!/usr/bin/env bash
# On-demand health check for the TradeBot signal pipeline.
# Run on the VPS:  bash scripts/health-check.sh
#
# Assumes Postgres runs in a docker container named `postgres` with
# db=tradebot user=postgres. Adjust PG_CONTAINER / PG_DB / PG_USER if different.

set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-postgres}"
PG_DB="${PG_DB:-tradebot}"
PG_USER="${PG_USER:-postgres}"

psql_run() {
  docker exec -i "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -X -A -F ' | ' -c "$1"
}

echo "=================================================="
echo " TradeBot Health Check — $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "=================================================="

echo
echo "── Fyers token ──"
psql_run "SELECT id, LEFT(access_token, 20) || '…' AS token_preview, updated_at,
                 ROUND(EXTRACT(EPOCH FROM (NOW() - updated_at))/3600, 1) AS hours_old
          FROM fyers_token WHERE id = 1;"

echo
echo "── Signals captured today ──"
psql_run "SELECT COUNT(*) AS signals_today
          FROM signals
          WHERE posted_at::date = CURRENT_DATE;"

echo
echo "── Last 5 signals ──"
psql_run "SELECT s.id, s.nse_symbol, s.entry_price,
                 smc.price_at_capture AS live_price,
                 smc.slippage_pct,
                 s.posted_at
          FROM signals s
          LEFT JOIN signals_market_context smc ON smc.signal_id = s.id
          ORDER BY s.posted_at DESC
          LIMIT 5;"

echo
echo "── LLM errors (last 24h) ──"
psql_run "SELECT COUNT(*) AS llm_errors_24h
          FROM llm_usage
          WHERE error IS NOT NULL AND error <> ''
            AND created_at > NOW() - INTERVAL '24 hours';"

echo
echo "── Signals missing price (last 24h) ──"
psql_run "SELECT COUNT(*) AS missing_price_24h
          FROM signals s
          LEFT JOIN signals_market_context smc ON smc.signal_id = s.id
          WHERE s.posted_at > NOW() - INTERVAL '24 hours'
            AND (smc.price_at_capture IS NULL);"

echo
echo "── Raw messages (last 24h) ──"
psql_run "SELECT COUNT(*) AS raw_msgs_24h
          FROM raw_messages
          WHERE posted_at > NOW() - INTERVAL '24 hours';"

echo
echo "Done. Green means all counts look sane and Fyers token < 20h old."
