# TradeBot Project Standards

## Project Context

**Goal**: Automated WhatsApp trading signal ingestion from 3 advisory groups (MSK Fintech, IPV Angels, MoneyMavericks) → Postgres database → market analysis → live trading.

**Status**: Phase 1 complete (signal capture working). Phases 1.5-4 pending.

**Technology Stack**:
- Backend: Python (serverless preferred for Phases 1.5+; n8n v2.40.7 for existing workflows)
- Database: PostgreSQL 16 (Postgres)
- Message Integration: Evolution API v2.3.7 (WhatsApp via Baileys)
- LLM: Gemini Flash (via OpenRouter, cost-controlled)
- Infrastructure: Vultr VPS (Ubuntu 24.04 LTS, 2GB RAM)
- Orchestration: n8n v2.40.7 (workflow engine)

See `docs/architecture.md` for full system diagram and component specs.

---

## 🎯 Design Principles (MUST READ)

**These 3 rules supersede everything else. When in doubt, choose simpler.**

### Rule 1: Keep It Simple
- **No defensive code** (error handling for edge cases that won't happen)
- **No over-engineering** (building for hypothetical future scenarios)
- **No premature optimization** (speed matters only if it's actually slow)
- **No abstractions unless absolutely needed**

**Example - WRONG** ❌:
```python
# Over-engineered
def extract_signal(message: str) -> Optional[Dict[str, Any]]:
    """Extract signal with comprehensive error handling."""
    if not message:
        raise ValueError("Message cannot be None")
    if not isinstance(message, str):
        raise TypeError("Message must be string")
    try:
        # Try multiple regex patterns
        for pattern in [pattern1, pattern2, pattern3, pattern4]:
            match = pattern.search(message)
            if match:
                # Validate each field
                result = validate_fields(match.groups())
                if result:
                    return result
    except Exception as e:
        log_error(e)
        return None
    return None
```

**Example - RIGHT** ✅:
```python
def extract_signal(message: str) -> Optional[Dict[str, Any]]:
    """Extract signal from message."""
    match = pattern.search(message)
    return match.groupdict() if match else None
```

**Why**: Your bot receives messages from 3 known WhatsApp groups with consistent format. You don't need to handle random edge cases that will never happen.

---

### Rule 2: Don't Add Code Unless Needed
- **One-time usage code**: Eliminate it or move it to a SQL query
- **"Might be useful later"**: Don't add it now
- **Utility functions for 1 caller**: Inline it
- **Config constants for 1 value**: Hardcode it (for MVP)

**Example - WRONG** ❌:
```python
# One-time script that formats symbols
def format_symbol(symbol: str) -> str:
    return symbol.upper().strip()

# Called once during seed
formatted = format_symbol(raw_symbol)
```

**Example - RIGHT** ✅:
```sql
-- Do it directly in SQL (one command, no code)
INSERT INTO symbols (stock_name_raw, nse_symbol)
SELECT DISTINCT raw_symbol, UPPER(TRIM(raw_symbol)) FROM temp_symbols;
```

**For temporary/one-use code**:
- Use SQL directly
- Use shell one-liners
- Use Python REPL
- Then delete it

**Example - Python one-liner instead of script**:
```bash
# Instead of creating scripts/clean_data.py that's used once:
python -c "import json; print(json.dumps(data, indent=2))" < input.json
```

---

### Rule 3: This Is a Simple Workflow, Not Complex Algorithm
- **No machine learning** (regex + simple LLM is enough)
- **No optimization algorithms** (linear search is fine for 3 groups)
- **No state machines** (if/else logic is clearer)
- **No async/concurrent code** unless messaging queue builds up (it won't, yet)

**The workflow is**:
```
WhatsApp message → Parse signal (regex) → Insert to DB → Done
```

**That's it.** Nothing more complex than this.

**Example - WRONG** ❌:
```python
# Async/concurrent (unnecessary complexity)
async def process_messages():
    tasks = [process_signal(msg) for msg in messages]
    await asyncio.gather(*tasks)

# State machine (too complex)
class SignalProcessor:
    def __init__(self):
        self.state = "waiting"
    def on_message(self, msg):
        if self.state == "waiting":
            self.state = "parsing"
        elif self.state == "parsing":
            self.state = "inserting"
        # ... 20 more lines
```

**Example - RIGHT** ✅:
```python
# Simple linear logic
for msg in messages:
    signal = extract_signal(msg)
    if signal:
        insert_signal(signal)
```

---

### How to Apply These Rules

**Before adding ANY code, ask**:
1. Is this really needed? (Not "might be useful")
2. Can I do it simpler? (Can SQL replace Python? Can a loop replace async?)
3. Will this be reused? (Only add if >1 caller)

**If answer is "no" to any**: Delete/simplify the code.

**Preferred complexity order** (simplest first):
1. **SQL query** (no code, just data)
2. **Shell one-liner** (temporary, then deleted)
3. **Simple Python function** (<20 lines, one job)
4. **n8n workflow node** (existing infrastructure)
5. **Class/module** (only if >3 callers need it)
6. **Async/concurrent** (only if queue backs up)
7. **External service** (only if nothing else works)

---

## Code Style & Conventions

### Python
- Use **type hints** for all function signatures (PEP 484)
- Format with **Black** (line length 100)
- Lint with **ruff** or **flake8**
- Docstrings: Google style (one-liner + full description for public APIs)

**Example**:
```python
def extract_signal(message: str, pattern: re.Pattern) -> Optional[Dict[str, Any]]:
    """Extract trading signal from message text using regex pattern.
    
    Args:
        message: Raw WhatsApp message body
        pattern: Compiled regex pattern for signal matching
        
    Returns:
        Dict with keys (trade_type, stock_name_raw, entry_price, stop_loss, targets)
        or None if no match found.
    """
    match = pattern.search(message)
    if not match:
        return None
    # ... implementation
```

### SQL
- Use **snake_case** for table/column names
- Fully qualified column names in joins (e.g., `signals.id`, not just `id`)
- Add indexes on foreign keys and frequently filtered columns
- Comment non-obvious logic (e.g., confidence scoring rules)

**Example**:
```sql
CREATE TABLE signals (
    id BIGSERIAL PRIMARY KEY,
    message_id TEXT NOT NULL UNIQUE,
    nse_symbol VARCHAR(10) NOT NULL,
    entry_price NUMERIC(10, 2) NOT NULL,
    confidence NUMERIC(3, 2) NOT NULL,  -- 0.00 to 1.00; 0.90 = regex, 0.70 = LLM
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_signals_symbol ON signals(nse_symbol);
CREATE INDEX idx_signals_created ON signals(created_at DESC);
```

### JSON/n8n Workflows
- Export workflows as `.json` files (use n8n UI "Download" button)
- Version exported files: `workflows/phase1-ingest-v1.json`, `workflows/phase1-ingest-v2.json`
- Never commit live credentials; use environment variables ($env.X)
- Add comments in workflow description: "Phase 1 v2: WhatsApp signal ingestion + LLM fallback + cost tracking"

---

## Architecture Decisions

### Signal Extraction Strategy
**MVP Approach**: Regex-first with LLM fallback
- **Regex**: Fast, deterministic, cost $0. Pattern library in `scripts/extract_signals.py`
- **LLM (Gemini Flash)**: Catches non-standard formats. Cost tracked in `llm_usage` table
- **Confidence Scoring**: regex=0.90, llm=min(0.75, parsed_confidence)
- Pre-LLM Filters: Skip if message >2000 chars, <20 chars, or contains skip patterns (🔥, "booked", "target hit", greetings)

See `docs/signal-format.md` for full MSK signal grammar and examples.

### Cost Controls (Phase 1.5+)
- LLM Model Allowlist: **Gemini Flash only** (via `OPENROUTER_API_KEY`)
- Kill switch: `LLM_ENABLED=false` in `.env` disables all LLM calls
- Daily cap: Alert if >$0.10/day
- Monthly cap: Alert if >$2/month
- Track all costs in `llm_usage` table with `was_signal`, `error`, and model fields

See `docs/cost-controls.md` for detailed tracking and alerting rules.

### Database Schema
- v1 (Phase 1): Core `signals` table (17 columns: id, source_group, trade_type, stock_name_raw, nse_symbol, entry_price, stop_loss, targets[], targets_mode, extractor, confidence, posted_at, received_at, created_at, processed_at)
- v2 (Phase 1.5): Add `signals_market_context`, `message_edits`, `extractor_confidence` tables
- v3 (Phase 1.5): Add `llm_usage` table and views for cost tracking

Scripts: `infra/stack/pg-init/01-init.sql`, `02-tradebot-schema.sql`, `03-tradebot-v2.sql`, `04-llm-usage.sql`

See `docs/architecture.md` for full ERD.

### Deployment Strategy
**Current**: n8n v2.40.7 on Vultr VPS (proven working)
**Future (Phases 1.5+)**: Consider serverless (AWS Lambda, Railway, Render) for 3-4x faster iteration
- Rationale: Signal extraction is stateless, perfect for functions-as-a-service
- Cost: Same or lower ($0 for free tiers)
- Benefit: Git-driven deployment (no UI debugging)

See `TOP_1_PERCENT_PLAYBOOK.md` for cost/speed comparison.

---

## Build & Deployment

### Local Setup
```bash
# Clone repo
git clone https://github.com/sripada-sys/tradebot.git
cd tradebot

# Install Python deps (for signal extraction scripts)
pip install -r requirements.txt

# Environment setup
cp .env.example .env  # Fill in secrets (Postgres, OpenRouter, Evolution API key)

# Docker stack (all services)
cd infra/stack
docker-compose up -d

# Verify services
docker ps  # Should show postgres, redis, evolution, n8n
docker logs stack-n8n | grep "n8n" | head -5
```

### Database Setup
```bash
# Init schemas (auto-run on docker-compose up)
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/01-init.sql
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/02-tradebot-schema.sql
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/03-tradebot-v2.sql
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/04-llm-usage.sql

# Verify
docker exec -i stack-postgres psql -U stackadmin -d n8n -c "SELECT COUNT(*) FROM signals;"
```

### Deploying Workflow Changes
**Option 1** (Current): n8n UI
1. Edit workflow in UI
2. Click "Save" then "Publish"
3. Verify webhook responds: `curl -X GET http://65.20.79.45:5678/webhook-test/...`

**Option 2** (Recommended for Phases 1.5+): Git + Python Script
1. Edit workflow locally in `workflows/phase1-ingest-v2.json`
2. Run: `python scripts/deploy_workflow.py workflows/phase1-ingest-v2.json`
3. Verify in n8n UI

**Option 3** (Raw DB): Direct PostgreSQL
```bash
# For emergency fixes or CLI-based deployment
docker exec -i stack-postgres psql -U stackadmin -d n8n << EOF
UPDATE workflow_entity 
SET nodes = $NDS$[...updated workflow JSON...]$NDS$
WHERE id = 'bf7e41466a2cfac1';

INSERT INTO workflow_history (...) VALUES (...);
UPDATE workflow_entity SET activeVersionId = ... WHERE id = ...;
EOF
```

See `docs/operations.md` for full runbook.

### Testing Checklist Before Merge
- [ ] Signal extraction works on 3+ example messages (see `PHASE1_TEST_RESULTS.md`)
- [ ] Postgres inserts verify: `SELECT * FROM signals ORDER BY created_at DESC LIMIT 1;`
- [ ] No LLM calls for skipped messages (pre-filter working)
- [ ] Cost tracking logs: `SELECT SUM(cost_usd) FROM llm_usage WHERE DATE(called_at) = TODAY;`
- [ ] Webhook responds (200 OK): `curl -X POST http://65.20.79.45:5678/webhook/...`
- [ ] No Postgres constraint violations in logs

---

## Documentation Requirements

### For New Features
1. **Architecture decision**: `docs/` folder (new file if major feature)
   - "Why this approach?" (trade-offs vs. alternatives)
   - Costs/latency impact
   - Example workflow
   
2. **Implementation notes**: Inline code comments for non-obvious logic
   - Why this regex pattern?
   - Why this confidence threshold?
   
3. **Test results**: Commit results to `PHASE1_TEST_RESULTS.md` (or `PHASE2_TEST_RESULTS.md`, etc.)
   - Example inputs
   - Expected outputs
   - Edge cases handled

### For Bug Fixes
- Link to issue or conversation (GitHub issue, this chat, etc.)
- Root cause explanation (1-2 lines)
- Test verification (how to reproduce + how to verify fix)

### Status Tracking
Update `CURRENT_STATUS.md` after each milestone:
- Which phase? (0 ✅, 1 🟡, 2-4 ⏳)
- What works? (✅ checklist)
- What's broken? (❌ blockers)
- Next step? (explicit action item)

---

## Key Files & Their Purposes

| Path | Purpose | Owner |
|------|---------|-------|
| `docs/architecture.md` | System design, ERD, component specs | Tech lead |
| `docs/signal-format.md` | MSK signal grammar, regex patterns, examples | Signal expert |
| `docs/phases.md` | 4-phase roadmap with effort estimates | PM |
| `docs/cost-controls.md` | LLM cost tracking, alert thresholds | DevOps |
| `docs/operations.md` | Deployment, backup, health check runbook | DevOps |
| `infra/stack/docker-compose.yml` | Service definitions (Postgres, Redis, Evolution, n8n) | DevOps |
| `infra/stack/pg-init/*.sql` | Database schema versions | DBA |
| `scripts/extract_signals.py` | Regex signal extraction (offline tool) | Signal engineer |
| `scripts/seed_symbols.py` | Build NSE symbol mapping | Data engineer |
| `workflows/phase1-ingest-v2.json` | Active n8n workflow (17 nodes) | Workflow engineer |
| `.env` | Secrets (NOT in git; use .env.example as template) | DevOps |
| `CURRENT_STATUS.md` | Live deployment status & next steps | Tech lead |
| `PHASE1_TEST_RESULTS.md` | Test results & edge cases handled | QA |
| `SESSION_CHECKPOINT.md` | State snapshot for resuming work | Tech lead |

---

## Common Tasks & Quick References

### Adding a New Signal Pattern
1. Add regex to `scripts/extract_signals.py` (test offline first)
2. Verify with 5+ real examples: `python scripts/extract_signals.py < chat_export.txt`
3. Update `docs/signal-format.md` with new pattern + examples
4. Commit to `patterns/` branch, PR to main
5. Deploy n8n workflow when merged

### Debugging Signal Ingestion
```bash
# 1. Check webhook received message
docker logs stack-n8n | grep -i webhook | tail -20

# 2. Check raw message was logged
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT * FROM raw_messages WHERE received_at > NOW() - INTERVAL '5 minutes' ORDER BY received_at DESC;"

# 3. Check signal extraction
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT id, stock_name_raw, nse_symbol, entry_price, extractor, confidence FROM signals WHERE created_at > NOW() - INTERVAL '5 minutes' ORDER BY created_at DESC;"

# 4. Check for LLM errors (if used)
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT * FROM llm_usage WHERE called_at > NOW() - INTERVAL '5 minutes' AND error IS NOT NULL;"
```

### Rolling Back a Workflow Change
```bash
# 1. View workflow versions
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT id, versionId, description FROM workflow_history WHERE workflowId = 'bf7e41466a2cfac1' ORDER BY createdAt DESC LIMIT 5;"

# 2. Revert to previous version
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "UPDATE workflow_entity SET activeVersionId = 'old-version-id' WHERE id = 'bf7e41466a2cfac1';"

# 3. Verify webhook returns 200
curl -X GET http://65.20.79.45:5678/webhook-test/msk-bot
```

### Monitoring Costs
```bash
# Daily LLM spend
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT * FROM v_llm_daily_cost WHERE date >= TODAY - INTERVAL '7 days';"

# Monthly total
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT * FROM v_llm_monthly_cost;"
```

---

## When to Use Serverless (Phases 1.5+)

**Consider migration from n8n to serverless if**:
- Feature involves stateless HTTP → DB pipeline (90% of our use cases)
- Iteration cycle > 30 mins (debugging n8n nodes)
- Want code reviews + Git versioning (no UI-only deployments)

**Deploy serverless using**:
- AWS Lambda + RDS (Postgres free tier) — most control, slightly steeper setup
- Railway/Render + Postgres addon — easiest, free tier sufficient for MVP

**Rationale**: See `TOP_1_PERCENT_PLAYBOOK.md` for cost/speed comparison (current: 4hrs, $17 | serverless: 1hr, $2).

---

## Reporting & Communication

### Status Updates
- Update `CURRENT_STATUS.md` daily during active work
- Include: completed tasks, blockers, next steps, estimated time to Phase completion

### Escalations
If task takes >50% longer than estimate:
1. Document the blocker in `CURRENT_STATUS.md`
2. Note root cause (n8n UI issue, API error, schema mismatch, etc.)
3. Propose mitigation (revert, skip, refactor)

### Before Taking a Break
- Commit all changes with descriptive message: `git commit -m "Phase 1.5: Add Fyers price lookup, fix slippage calc"`
- Update `SESSION_CHECKPOINT.md` with: current phase, tests passing, next action
- Push to GitHub: `git push origin main`

---

## Environment Variables

**Required** (in `.env`):
```bash
POSTGRES_USER=stackadmin
POSTGRES_PASSWORD=<32-char hash>
N8N_ENCRYPTION_KEY=<base64 string>
N8N_BASIC_AUTH_HASH=admin/JTYInY4QXNaXcxXdROeE
EVOLUTION_API_KEY=<key from Evolution dashboard>
OPENROUTER_API_KEY=sk-or-v1-...
LLM_ENABLED=true|false
```

**Template**: `.env.example` (commit to repo)
**Never commit**: Actual `.env` file (add to `.gitignore`)

---

## Red Flags & How to Handle

| Issue | Check | Action |
|-------|-------|--------|
| Signals not appearing in DB | webhook logs + n8n execution log | Check n8n nodes for errors; verify Postgres connection |
| LLM calls exceeded budget | `v_llm_daily_cost` | Set `LLM_ENABLED=false`; review pre-filters |
| Evolution API disconnected | `docker logs stack-evolution` | Restart: `docker restart stack-evolution`; verify API key |
| Postgres out of disk | `docker exec postgres df -h /var/lib/postgresql` | Delete old test data; increase VPS disk |
| n8n not accessible | `curl http://65.20.79.45:5678` | Check firewall; restart n8n: `docker restart stack-n8n` |

---

## Links to Key Resources

- **GitHub Repo**: https://github.com/sripada-sys/tradebot
- **WhatsApp Groups** (3 target advisory groups — see `CURRENT_STATUS.md`)
- **Evolution API Docs**: https://github.com/EvolutionAPI/evolution-api
- **n8n Docs**: https://docs.n8n.io/
- **Gemini Flash Pricing**: https://ai.google.dev/pricing (via OpenRouter: $0.075/M input, $0.30/M output)
- **Fyers API**: https://api.fyers.in/apidocs/
- **NSE Symbol List**: Built into `symbols` table (190 stocks pre-seeded)

---

## Phase Roadmap Quick Reference

| Phase | Goal | Status | ETA |
|-------|------|--------|-----|
| 0 | Infrastructure (VPS, Postgres, Evolution, n8n) | ✅ Done | — |
| 1 | Signal capture & logging (regex extraction) | 🟡 ~90% | 1 week |
| 1.5 | Market context (price @ message time, slippage) | ⏳ Ready to start | 1-2 weeks |
| 2 | Confirmation flow (advisor approval before trade) | ⏳ Not started | 2-3 weeks |
| 3 | Paper trading (simulate trades, measure PnL) | ⏳ Not started | 3-4 weeks |
| 4 | Live trading + HTTPS + firewall lockdown | ⏳ Not started | 4-6 weeks |

See `docs/phases.md` for full details.

---

## Questions?

- **Architecture decisions**: See `docs/` folder + this file
- **How to deploy**: See `docs/operations.md`
- **How to debug**: See "Common Tasks" section above
- **Cost concerns**: See `docs/cost-controls.md`
- **Existing issues**: See `CURRENT_STATUS.md` for known blockers
