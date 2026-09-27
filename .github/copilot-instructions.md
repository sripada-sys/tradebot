# TradeBot Project Standards

## 🚨 BUDGET RULES (HIGHEST PRIORITY — READ FIRST)

**Total budget for entire bot experiment: $5 USD. Not a dollar more.**

Every action, every tool call, every model choice must respect this ceiling.

### Rule A: Total Budget = $0 (HARD STOP)
- **Already spent**: ~$37 total (Opus/Sonnet overuse — learning tax, don't repeat)
- **Going forward**: **$0 budget for Phase 2 onwards**
- **No more Opus or Sonnet** — terminal + grep + Haiku only
- **If a task cannot be done without LLM reasoning**: Stop, pause, ask user explicitly before proceeding
- **If user approves an exception**: Get written confirmation + budget allocation first

### Rule B: Don't Burn Tokens
- **This is a simple trading bot.** Do not treat it like a research project.
- **No exploratory reads** — read only files needed for the current task
- **No re-reading files** already in context (they're summarized above)
- **No verbose explanations** unless asked — short, direct answers
- **No decorative markdown** (no giant ASCII banners, no 8-file doc suites for 1 task)
- **Batch tool calls** in parallel whenever possible (1 turn instead of 5)
- **Prefer terminal one-liners** over creating new files
- **Delete/consolidate** existing bloated docs instead of adding more

### Rule C: Model Selection (HAIKU ONLY for Phase 2+)

**No exceptions.** Phase 2 onwards = **Haiku only**. Period.

| Task Type | Model | Why |
|-----------|-------|-----|
| All edits, queries, deployments, debugging | **Haiku** | $0.003 per 1K tokens vs Sonnet $0.003/$0.015 — 80% savings |
| Terminal commands, grep, script testing | **No LLM** | Just run it |
| Architecture/logic that needs reasoning | **PAUSE** | Stop, ask user, get budget approval first |

**This is non-negotiable.** Opus is banned. Sonnet is banned. Terminal work costs $0.

### Rule D: Budget-Aware Task Execution ($0 Phase 2+)
- **All work is terminal/grep/file-edit based** — no exploratory reads, no LLM calls
- **If a task genuinely requires reasoning**: STOP. Don't guess. Pause and ask.
- **When in doubt**: Use `grep -r`, `ssh`, `docker exec` — these are free
- **Example**: "Need to add advisor approval logic?" → Write it on the VPS in a terminal scratch file first, test it, then commit. No LLM reasoning needed.

### Rule E: What Counts as Wasteful (Don't Do This)
- ❌ Creating 8 documentation files when 1 would do
- ❌ Reading the same file 3 times in one session
- ❌ Long philosophical explanations of trade-offs when a 1-line answer suffices
- ❌ Generating ASCII art / banners / decorative output
- ❌ Re-summarizing what was just done ("Let me summarize what I built...")
- ❌ Committing every micro-change separately (batch them)
- ❌ Using Opus for tasks Haiku can handle

### Rule F: Budget Tracking & Enforcement
- **$0 budget is hard stop** — no exceptions without explicit written user approval + new budget allocation
- **If I slip and use Sonnet/Opus**: User is entitled to refuse paying for it, full stop
- **Cost breakdown per session**: All Phase 2+ work should cost <$0.50 total (mostly Haiku for final review, if any)
- **Transparent**: If a task genuinely cannot be done within $0 budget, I stop and explain why upfront

---

## Project Context

**Goal**: Automated WhatsApp trading signal ingestion from 3 advisory groups (MSK Fintech, IPV Angels, MoneyMavericks) → Postgres database → market analysis → live trading.
## Project Context

Simple WhatsApp trading-signal bot. Reads messages from 3 advisory groups, extracts signals with regex (LLM fallback), stores in Postgres. Live at `65.20.79.45`.

**Stack**: Vultr VPS (Ubuntu 24.04, 2GB) → Docker Compose → { Postgres 16, Redis, Evolution API v2.3.7, n8n v2.40.7 }. LLM = Gemini Flash via OpenRouter.

**Target groups** (hardcoded in workflow filter):
- `919493561700-1545803250@g.us` — MSK Fintech
- `919930599976-1613022548@g.us` — IPV Angels
- `120363427391049099@g.us` — MoneyMavericks

**Active workflow**: `bf7e41466a2cfac1` (n8n, 17 nodes, regex+LLM+alert).

See `STATUS.md` for current phase & verification commands.

---

## 🎯 Design Principles

1. **Keep it simple.** No defensive code. No over-engineering. No premature optimization.
2. **Don't add code unless needed.** One-time usage → do it in SQL/shell, don't commit a script. Function with 1 caller → inline it.
3. **This is a simple workflow, not a complex algorithm.** No async, no state machines, no ML — regex + insert + done.

**Simplicity hierarchy** (pick the simplest that works): SQL → shell one-liner → Python REPL → simple function → n8n node → module/class → async → external service.

**Before adding any code, ask**: Really needed? Simpler way exists? Reused >1 time? If any "no" → don't add it.

---

## Code Conventions (short)

- **Python**: type hints, one-liner docstrings, ≤30 lines per function, no defensive validation.
- **SQL**: snake_case, index FKs and hot filter columns, comments only where non-obvious.
- **Secrets**: only in `.env` (never committed). Template = `.env.example`.
- **Commits**: one line, prefix with phase (`phase1.5: add fyers price lookup`).

---

## Operational Runbook

**SSH**: `ssh root@65.20.79.45` (ed25519 key)
**Stack dir on VPS**: `/opt/stack/`
**Env file**: `/opt/stack/.env`

### Health checks
```bash
ssh root@65.20.79.45 "docker ps"
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT COUNT(*) FROM signals;'"
```

### Debug a missing signal
```bash
# Recent webhook hits
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT id, status, \"startedAt\" FROM execution_entity ORDER BY \"startedAt\" DESC LIMIT 5;'"

# LLM errors
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT * FROM llm_usage WHERE error IS NOT NULL ORDER BY called_at DESC LIMIT 5;'"
```

### Cost check
```bash
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT * FROM v_llm_daily_cost;'"
```
Kill switch: set `LLM_ENABLED=false` in `/opt/stack/.env` and `docker restart stack-n8n`.

### Restart a service
```bash
ssh root@65.20.79.45 "docker restart stack-n8n"   # or stack-evolution
```

---

## Key Files

| Path | Purpose |
|---|---|
| `.github/copilot-instructions.md` | This file — agent standards |
| `STATUS.md` | Current phase, live state, next action |
| `README.md` | Repo landing page |
| `docs/architecture.md`, `phases.md`, `signal-format.md`, `cost-controls.md`, `operations.md` | Domain reference |
| `infra/stack/docker-compose.yml` | Service definitions |
| `infra/stack/pg-init/*.sql` | DB schema (v1 → v2 → v3) |
| `workflows/phase1-ingest-v2.json` | Active n8n workflow (export) |
| `scripts/extract_signals.py` | Offline regex validator |
| `scripts/deploy.sh` | Deploy helper |
| `.env` | Secrets (gitignored) |

---

## Red Flags Cheat Sheet

| Problem | First check | Fix |
|---|---|---|
| No signals inserted | `execution_entity` for recent runs | If runs exist → node error in exec_data; if no runs → webhook broken |
| LLM cost > $0.10/day | `v_llm_daily_cost` | Set `LLM_ENABLED=false` |
| Evolution disconnected | `docker logs stack-evolution` | Restart; re-scan QR if needed |
| n8n webhook 404 | `webhook_entity` row missing | Rebind webhook path to active workflow |
| Postgres FK errors | Check `workflow_published_version` refs | Null `activeVersionId` before delete |
