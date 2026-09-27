# 📋 How Standard Instructions Work

## What I Just Created For You

```
tradebot/
├── .github/
│   └── copilot-instructions.md  ← THIS FILE (loaded automatically)
├── docs/
├── workflows/
└── ...
```

**File**: `.github/copilot-instructions.md` (750 lines)
**Scope**: Applies to ALL future Copilot work in this workspace
**Auto-loaded**: Whenever you open tradebot in VS Code and ask for help

---

## What Happens Next Time You Ask For Help

### Before (Without instructions)
You: "Add Fyers price tracking to Phase 1.5"
Agent: "Sure! But first, which database version? What's your naming convention? Where do you usually test?"
**Result**: Slow, many clarifying questions, possible errors

### After (With instructions)
You: "Add Fyers price tracking to Phase 1.5"
Agent: "Got it. I'll:
1. Check the Phase 1.5 schema (v2 already has signals_market_context table)
2. Add 15-20 lines of Python to Lambda function
3. Use NSE symbol from symbols table for lookup
4. Update docs/phases.md with progress
5. Run testing checklist from copilot-instructions.md
6. Commit with proper message format"
**Result**: Fast, zero questions, consistent with your standards

---

## What's Inside The Instructions File

### 1. Project Context
Your project goal, tech stack, status, links to docs

### 2. Code Style
- **Python**: Type hints, Black formatting, Google docstrings
- **SQL**: snake_case, fully qualified columns, indexed PKs
- **JSON**: Versioned workflows, env variables not hardcoded

### 3. Architecture Decisions
**Why regex-first with LLM fallback?** Cost, speed, control.
**Why Postgres v1→v2→v3 schema?** Incremental features without migrations.
**When to use serverless?** When stateless (most of Phases 1.5+).

### 4. Build & Deploy
Copy-paste commands:
```bash
# Local setup
docker-compose up -d

# Deploy workflow change
python scripts/deploy_workflow.py workflows/phase1-ingest-v2.json

# Debug signals
docker exec -i stack-postgres psql -U stackadmin -d n8n \
  -c "SELECT * FROM signals ORDER BY created_at DESC LIMIT 1;"
```

### 5. Documentation Requirements
What to update after each feature:
- [ ] Architecture decision (if major)
- [ ] Test results (edge cases)
- [ ] Status file (current progress)

### 6. Common Tasks Playbook
- How to debug "signals not appearing"? → Check webhook logs + n8n execution
- How to rollback a workflow? → View versions, revert activeVersionId
- How to monitor costs? → Query v_llm_daily_cost

### 7. Red Flags & Fixes
| Problem | Detection | Fix |
| Signals not in DB | Webhook logs | Check n8n errors |
| LLM costs exceeded | v_llm_daily_cost | Set LLM_ENABLED=false |
| Evolution API down | docker logs | Restart container |

---

## How Agent Uses It (Behind the Scenes)

1. **Loads**: Reads `.github/copilot-instructions.md` automatically
2. **Understands**: Learns your conventions, architecture, deployment process
3. **Applies**: When you ask for code, writes it matching your style
4. **References**: Links to docs instead of asking questions
5. **Tests**: Uses your testing checklist before committing
6. **Commits**: Uses your message format (git commit style guide)

---

## For Every Future Task

When you ask me to work on this project, I will:

✅ **Understand your architecture** (no "why that design?" questions)
✅ **Follow your code style** (types, formatting, docstrings)
✅ **Use the right tools** (n8n vs. serverless decision)
✅ **Test properly** (checklist: webhook responds, signal creates, LLM disabled, etc.)
✅ **Update docs** (architecture.md, CURRENT_STATUS.md, test results)
✅ **Know your phases** (Phase 1.5 = Fyers integration, Phase 2 = confirmation, etc.)
✅ **Monitor costs** (check daily LLM spend, alert if >$0.10)
✅ **Commit cleanly** (descriptive message with phase number)

---

## Examples: How This Helps

### Example 1: "Add market context tracking"
**Old flow** (3 mins reading docs + asking questions):
- "What database version should I use?" → You: "v2"
- "Should I use n8n or write Python?" → You: "Think about speed..."
- "How do I test?" → You: "Check signals table and verify slippage"

**New flow** (0 seconds, instructions already loaded):
Agent: "I see Phase 1.5 uses schema v2 with signals_market_context table. For speed, I'll add Fyers API call as a Python Lambda function. Testing: webhook responds, price logged, slippage calculated. Let me start."

### Example 2: "Deploy the workflow"
**Old flow**: "What's the deployment command again?"
**New flow**: Agent directly runs: `python scripts/deploy_workflow.py workflows/phase1-ingest-v2.json`

### Example 3: "Costs are getting high"
**Old flow**: "How do I check daily costs?" (You explain → 1 min overhead)
**New flow**: Agent runs: `SELECT * FROM v_llm_daily_cost WHERE date >= TODAY - INTERVAL '7 days';`

---

## How to Update Instructions

When your standards change (e.g., "We're using serverless now for all Phases"):

1. Edit `.github/copilot-instructions.md`
2. Update the relevant section (e.g., "Deploy" section)
3. Commit: `git commit -m "docs: Update deployment guide for serverless transition"`
4. Push: `git push origin main`

**Next task onwards**: Agent loads updated instructions automatically.

---

## Scope: What Instructions DO & DON'T Cover

### ✅ DO:
- General conventions (naming, style, formatting)
- Architecture decisions (why this approach)
- Build & deployment steps (how to run)
- Testing checklist (what to verify)
- Debugging playbook (how to fix common issues)
- Documentation requirements (what to update)

### ❌ DON'T:
- Bug-specific fixes (handled per-bug)
- Runtime errors in THIS conversation (still need to debug)
- Questions about unrelated projects (use separate workspace instructions)
- Business logic (what signals mean) — keep in code comments instead

---

## Key Insight

**Instructions are the difference between**:
- Agent asking "how?" every time (slow, annoying)
- Agent knowing "how" and asking "what?" instead (fast, focused)

You've now automated all the "how?" questions. When you say:
- "Add price tracking" → Agent knows HOW (Fyers API call, n8n vs. serverless decision, testing approach)
- "Fix webhook" → Agent knows HOW (debug commands, rollback process)
- "Deploy Phase 1.5" → Agent knows HOW (deploy process, testing checklist, docs to update)

---

## Quick Command Reference

**Check where instructions are:**
```bash
ls -la tradebot/.github/
# Should show: copilot-instructions.md
```

**Edit instructions:**
```bash
# Open in editor
open tradebot/.github/copilot-instructions.md

# Or from VS Code:
# Cmd+K Cmd+O → search "copilot-instructions.md"
```

**Verify they're loaded:**
Ask me: "What's the testing checklist for Phase 1.5?"
I should respond with exact steps from the instructions file.

---

## Summary

| What | Where | When |
|------|-------|------|
| **Standard instructions** | `.github/copilot-instructions.md` | Auto-loaded every time you open project |
| **Project-specific conventions** | Inside instructions (code style section) | Applied to all new code |
| **Deployment process** | Inside instructions (build section) | Referenced when deploying |
| **Testing checklist** | Inside instructions (testing section) | Used before every commit |
| **Architecture decisions** | Inside instructions (architecture section) | Understood before feature planning |
| **Common debugging** | Inside instructions (common tasks) | Referenced when things break |

**Result**: Faster, consistent, professional-grade work every time you ask for help on this project.

---

## Next Steps

1. **Open the instructions file**: `tradebot/.github/copilot-instructions.md`
2. **Customize as needed**: Add/remove sections specific to your workflow
3. **Commit to repo**: `git add .github/copilot-instructions.md && git commit -m "docs: Add standard project instructions"`
4. **Push to GitHub**: `git push origin main`
5. **Start using**: Ask me to work on Phase 1.5 — I'll follow all instructions automatically

**From now on**: Every agent task in this project uses your standards. No more guessing about naming, deployment, testing, or architecture decisions.

Welcome to professional-grade AI-assisted development! 🚀
