# 🎯 Standard Instructions Cheat Sheet

## 🚨 The 3 Rules (READ FIRST)

| Rule | What | Why |
|------|------|-----|
| **Keep It Simple** | No defensive code, no over-engineering, no premature optimization | Bot receives 3 known groups → no edge cases to handle |
| **Don't Add Code Unless Needed** | No one-time scripts, no "future" utilities, no 1-caller functions | Use SQL instead, keep it minimal |
| **Simple Workflow, Not Complex** | No async/concurrent, no ML, no state machines, no optimization algorithms | It's just: message → parse → insert → done |

**When adding code, ask**: Is this really needed? Can I do it simpler? Will this be reused? If "no" → delete it.

---

## File Location
```
.github/copilot-instructions.md  ← Agent loads this automatically + learns these 3 rules
```

## What This Means For You

### Before (No Instructions)
```
You: "Add Fyers API integration"
Agent: "Sure. Let me ask 5 questions about your architecture..."
⏱ 5-10 minutes of clarification
```

### After (With Instructions)
```
You: "Add Fyers API integration"
Agent: "I'll add Fyers call to Phase 1.5 Lambda, update signals_market_context table, test with your checklist, commit with proper format."
⏱ Agent just works
```

---

## Key Sections Reference

### 🏗 Architecture
**Location**: `docs/architecture.md`
**Quick facts**:
- Signal extraction: Regex-first ($0) + LLM fallback (Gemini Flash via OpenRouter)
- Pre-filters: Skip if >2000 chars, <20 chars, or contains skip patterns
- Confidence: regex=0.90, llm=0.70 (capped at 0.75)
- Database: Postgres v1→v2→v3 (incremental features)

### 🛠 Deployment
**Location**: `docs/operations.md`
**Quick commands**:
```bash
# Deploy via n8n UI (current)
# OR
# Deploy via Python script
python scripts/deploy_workflow.py workflows/phase1-ingest-v2.json

# OR
# Deploy via raw DB (emergency)
docker exec -i stack-postgres psql -U stackadmin -d n8n << EOF
UPDATE workflow_entity SET nodes = $NDS$[...]$NDS$ WHERE id = 'bf7e41466a2cfac1';
EOF
```

### 💰 Cost Monitoring
**Location**: `docs/cost-controls.md`
**Quick commands**:
```bash
# Daily LLM costs
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT * FROM v_llm_daily_cost WHERE date >= TODAY - INTERVAL '7 days';"

# Kill switch
export LLM_ENABLED=false  # in .env
```

### 🧪 Testing Checklist
**Before commit**:
- [ ] Signal extraction works on 3+ examples
- [ ] Postgres inserts verify
- [ ] No LLM calls for skipped messages
- [ ] Cost tracking logs (if LLM used)
- [ ] Webhook responds (200 OK)
- [ ] No Postgres constraint violations

### 🐛 Debugging Playbook
```bash
# Signals not in DB?
docker logs stack-n8n | grep -i webhook

# Check raw message logged
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT * FROM raw_messages WHERE received_at > NOW() - INTERVAL '5 minutes';"

# Check signal created
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT id, stock_name_raw, nse_symbol, entry_price FROM signals WHERE created_at > NOW() - INTERVAL '5 minutes';"

# LLM errors?
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT * FROM llm_usage WHERE called_at > NOW() - INTERVAL '5 minutes' AND error IS NOT NULL;"
```

---

## Code Style Quick Reference

### Python
```python
# Types required
def extract_signal(message: str) -> Optional[Dict[str, Any]]:
    """Extract trading signal from message.
    
    Args:
        message: Raw WhatsApp message body
        
    Returns:
        Dict with signal data or None if no match.
    """
    # Implementation
    pass

# Format with Black (100 line length)
# Docstrings: Google style
```

### SQL
```sql
-- snake_case for tables/columns
CREATE TABLE signals (
    id BIGSERIAL PRIMARY KEY,
    message_id TEXT NOT NULL UNIQUE,
    nse_symbol VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index on frequently filtered columns
CREATE INDEX idx_signals_created ON signals(created_at DESC);

-- Fully qualified column names
SELECT signals.id, signals.nse_symbol FROM signals
JOIN raw_messages ON signals.message_id = raw_messages.message_id;
```

### JSON (n8n Workflows)
```json
{
  "name": "phase1-ingest-v2",
  "description": "Phase 1 v2: WhatsApp signal ingestion + LLM fallback + cost tracking",
  "nodes": [
    {
      "parameters": {
        "url": "={{ $env.EVOLUTION_API_URL }}",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": true
      }
    }
  ]
}
```

---

## Key Files Reference

| File | What | When to Edit |
|------|------|--------------|
| `.env` | Secrets (NOT in git) | When API keys rotate |
| `.env.example` | Secrets template | When adding new secret type |
| `.github/copilot-instructions.md` | This file (agent instructions) | When practices change |
| `docs/architecture.md` | System design + ERD | Major architecture change |
| `docs/signal-format.md` | MSK signal grammar + regex | New signal pattern |
| `docs/cost-controls.md` | LLM cost tracking rules | Cost strategy changes |
| `docs/phases.md` | 4-phase roadmap | Phase status changes |
| `docs/operations.md` | Deploy & debug runbook | Deployment process changes |
| `infra/stack/docker-compose.yml` | Service definitions | Adding/updating services |
| `infra/stack/pg-init/*.sql` | Database schemas | New feature requiring DB change |
| `workflows/phase1-ingest-v2.json` | Active n8n workflow | Signal extraction logic changes |
| `scripts/extract_signals.py` | Regex extraction (offline) | New regex pattern |
| `CURRENT_STATUS.md` | Live status + next steps | After every session |
| `PHASE1_TEST_RESULTS.md` | Test results + edge cases | After testing phase |
| `SESSION_CHECKPOINT.md` | State snapshot for resume | Before long break |

---

## Common Patterns

### Adding a New Signal Type
1. Add regex to `scripts/extract_signals.py`
2. Test offline: `python scripts/extract_signals.py < chat_export.txt`
3. Update `docs/signal-format.md`
4. Commit to branch, create PR
5. Merge + deploy n8n workflow when ready

### Debugging a Problem
1. Check logs: `docker logs stack-n8n`
2. Check DB: Query relevant table
3. Check webhook: `curl -X GET http://65.20.79.45:5678/webhook-test/...`
4. Document in `CURRENT_STATUS.md`
5. Fix + re-test

### Deploying a Change
1. Make changes (code, workflow, schema)
2. Test using checklist
3. Commit: `git commit -m "Phase X: [feature] — [brief description]"`
4. Deploy (n8n UI, script, or raw DB)
5. Verify: `curl -X POST http://...webhook...`
6. Update `CURRENT_STATUS.md`

### Escalating a Blocker
1. Document in `CURRENT_STATUS.md` under "Blockers"
2. Note root cause (n8n UI issue? API error? Schema mismatch?)
3. Propose mitigation (revert? skip? refactor?)
4. Ping for review

---

## Environment Setup (Copy-Paste)

```bash
# Clone repo
git clone https://github.com/sripada-sys/tradebot.git
cd tradebot

# Install Python deps
pip install -r requirements.txt

# Setup .env
cp .env.example .env
# Fill in: POSTGRES_PASSWORD, N8N_ENCRYPTION_KEY, EVOLUTION_API_KEY, OPENROUTER_API_KEY

# Start stack
cd infra/stack
docker-compose up -d

# Init database
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/01-init.sql
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/02-tradebot-schema.sql
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/03-tradebot-v2.sql
docker exec -i stack-postgres psql -U stackadmin -d n8n < pg-init/04-llm-usage.sql

# Verify services
docker ps  # Should show 4 running containers
curl http://65.20.79.45:5678  # n8n health check
```

---

## Phase Status (Current)

| Phase | Goal | Status | Next |
|-------|------|--------|------|
| 0 | Infrastructure | ✅ Done | — |
| 1 | Signal capture | 🟡 ~90% | Real WhatsApp test |
| 1.5 | Market context | ⏳ Ready | Add Fyers price API |
| 2 | Confirmation | ⏳ Next | Advisor approval flow |
| 3 | Paper trading | ⏳ Later | Mock trades |
| 4 | Live trading | ⏳ Later | Real trades + HTTPS |

**Current**: Awaiting real WhatsApp signal from MSK group for Phase 1 completion.

---

## Red Flags & Quick Fixes

| ⚠️ Problem | 🔍 Check | 🔧 Fix |
|-----------|----------|--------|
| Signals not appearing | Webhook logs | Check n8n node errors |
| LLM costs spiking | `v_llm_daily_cost` | Set `LLM_ENABLED=false` |
| Evolution API offline | `docker logs stack-evolution` | Restart: `docker restart stack-evolution` |
| Postgres disk full | `docker exec postgres df -h` | Delete old test data |
| n8n not responding | `curl http://65.20.79.45:5678` | Restart: `docker restart stack-n8n` |
| Symbol not found | Check `symbols` table | Add to NSE seed list |
| Workflow versioning broken | `workflow_history` table | Manual DB fix (see SESSION_CHECKPOINT.md) |

---

## When Instructions Get Updated

If practices change (e.g., "moving to serverless"):

1. Edit `.github/copilot-instructions.md`
2. Update the relevant section
3. Commit: `git commit -m "docs: Update [section] for [reason]"`
4. Push: `git push origin main`

**Next task onwards**: Agent loads updated instructions automatically. No more updates needed.

---

## Pro Tips

✅ **Do**:
- Update `CURRENT_STATUS.md` after each session
- Link to docs instead of duplicating info
- Use the debugging playbook before asking for help
- Commit with descriptive messages (include phase number)
- Test using the checklist before deployment

❌ **Don't**:
- Commit `.env` (use `.env.example` instead)
- Skip testing (use the checklist!)
- Make changes directly in n8n UI without backing up
- Ignore cost tracking (check daily!)
- Forget to document blockers

---

## Questions?

**"Where do I find X?"** → Check "Key Files Reference" table above
**"How do I debug Y?"** → Check "Debugging Playbook" section
**"What's the test checklist?"** → See "Testing Checklist" section
**"How do I deploy?"** → See "Deployment" section

**If still unsure**: Open `.github/copilot-instructions.md` — it's the source of truth.

---

## TL;DR

**You have**: Professional-grade project instructions file loaded automatically
**Agent knows**: Your architecture, code style, deployment process, testing approach
**Result**: Faster, consistent, professional work every time you ask for help

**Next step**: Ask me to work on Phase 1.5 — I'll follow all instructions automatically! 🚀
