# TradeBot

Automated pipeline that reads stock recommendations from WhatsApp advisory groups
(MSK Fintech, IIT Madras, IPV Angels), extracts structured trade signals, and
(eventually) executes buy/sell orders via the **Fyers** API.

**Server:** Vultr VPS (Ubuntu 24.04, 1 vCPU / 2 GB RAM)
**Stack:** Docker Compose — Postgres · Redis · Evolution API · n8n

---

## Repository layout

```
tradebot/
├── README.md                    # this file
├── docs/
│   ├── architecture.md          # system design + data flow
│   ├── phases.md                # phased rollout plan
│   ├── signal-format.md         # MSK signal grammar + examples
│   └── operations.md            # runbook, deploy, backup, restore
├── infra/
│   └── stack/
│       ├── docker-compose.yml   # full stack definition
│       ├── .env.example         # template — real .env lives on server only
│       └── pg-init/init.sql     # Postgres bootstrap
├── workflows/                   # n8n workflow JSON exports
├── scripts/
│   ├── extract_signals.py       # local signal extractor (validation)
│   └── deploy.sh                # one-shot deploy from a fresh Ubuntu box
└── .gitignore
```

---

## Quick links

- [Architecture](docs/architecture.md)
- [Phases](docs/phases.md)
- [Signal format](docs/signal-format.md)
- [Operations runbook](docs/operations.md)

---

## Current status

- ✅ **Phase 0 — Infrastructure**: Postgres, Redis, Evolution API, n8n running on Vultr
- 🟡 **Phase 1 — Ingest & log signals** (in progress): connect WhatsApp, build n8n workflow, log to DB
- ⏳ **Phase 2 — Confirmation flow**: bot asks user to approve before acting
- ⏳ **Phase 3 — Paper trading via Fyers**: log orders it *would* have placed
- ⏳ **Phase 4 — Live trading**: hard-capped position sizing, kill switch, HTTPS + firewall

---

## ⚠️ Security notes

- Real secrets (`.env`, API keys, tokens) **never** enter this repo — see `.gitignore`.
- `infra/stack/.env.example` is the template. The live `.env` is only on the server at `/opt/stack/.env`.
- Phase 4 requires: HTTPS reverse proxy (Caddy or nginx + Let's Encrypt), UFW firewall, and Fyers order caps.
