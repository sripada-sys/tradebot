# Phased rollout

## Phase 0 — Infrastructure ✅

- Vultr VPS: Ubuntu 24.04, 1 vCPU, 2 GB RAM, 52 GB disk
- Docker + Compose installed
- Stack: Postgres, Redis, Evolution API, n8n running
- SSH key auth from developer laptop
- Credentials generated and stored in `/opt/stack/.env` (server only)

**Exit criteria:** all 4 containers `Up`, n8n reachable on `:5678`, Evolution reachable on `:8080`.

---

## Phase 1 — Ingest & log signals 🟡

**Goal:** capture every message from the 3 advisory groups, extract structured signals, log to Postgres. **No trading.**

Steps:
1. Open Evolution Manager, create instance `msk-bot`, scan QR from personal WhatsApp.
2. Confirm instance status = `open` and messages start flowing.
3. Create Postgres schema (see `docs/architecture.md`).
4. Set Evolution webhook to n8n endpoint `/webhook/whatsapp-in`.
5. Build n8n workflow:
   - webhook trigger
   - filter by group JID allow-list
   - regex extractor node (see `docs/signal-format.md`)
   - fallback LLM node (Gemini Flash) when regex fails
   - symbol resolver (lookup from `symbols` table)
   - Postgres insert
6. Run for **1 week** and review `signals` table nightly.

**Exit criteria:** ≥ 90% of real "Looks Good ABOVE" signals correctly parsed, < 5% false positives on 🔥 update messages.

---

## Phase 2 — Confirmation flow ⏳

**Goal:** user approval loop before any trade action.

Steps:
1. Add `pending_confirmations` table.
2. When a valid signal is extracted, n8n sends a WhatsApp message back to the user (via Evolution) with a formatted proposal:
   ```
   📈 New signal from MSK
   Stock: SAKSOFT (SAKSOFT.NS)
   Entry: ≥ 173.00
   SL:    155.00
   Targets: 176 / 180 / 185 / 190 / 195 / 200
   Type:  POSITIONAL
   Qty:   57  (₹10,000 / 173)
   
   Reply YES 8421 to confirm, NO 8421 to skip.
   ```
3. n8n listens for a reply matching the token. On YES → mark approved. On NO or 30-min timeout → mark rejected.

**Exit criteria:** end-to-end approve/reject flow works over WhatsApp with no misses.

---

## Phase 3 — Paper trading via Fyers ⏳

**Goal:** simulate execution against real market data — no capital at risk.

Steps:
1. Register Fyers app; store `FYERS_APP_ID` / `FYERS_SECRET_KEY` in server `.env`.
2. Implement daily auto-login using TOTP.
3. On approved signals:
   - fetch current LTP via Fyers quotes API,
   - if LTP ≥ entry, log a *would-place* order to `paper_orders`,
   - track SL / target hits over time using minute candles.
4. Nightly summary WhatsApp back to user: paper P&L.

**Exit criteria:** 2 weeks of paper trades with plausible fill prices and P&L close to what a manual trader would see.

---

## Phase 4 — Live trading ⏳

**Goal:** real orders, small size, hard limits.

Steps:
1. Add HTTPS (Caddy) + UFW firewall (allow 22/80/443 only).
2. Move Evolution + n8n behind reverse proxy, close 5678/8080 to the public.
3. Hardcode order caps:
   - `MAX_ORDER_VALUE_INR = 5000`
   - `MAX_OPEN_POSITIONS = 3`
   - `MAX_DAILY_LOSS_INR = 2000` (kill-switch)
   - trading window 09:15–15:15 IST
   - single-symbol dedupe within 10 min
4. Live order = Fyers **BUY LIMIT** at entry with server-side SL order.
5. `system_flags.trading_enabled` boolean to halt everything instantly via WhatsApp command.

**Exit criteria:** 30 days live with no unexpected orders, all safety caps observed, weekly review PDF generated.

---

## Non-goals (for now)

- No shorting.
- No F&O.
- No portfolio-level risk optimization.
- No auto-exits beyond the SL/target set by the signal.
