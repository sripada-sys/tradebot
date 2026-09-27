# 📑 TradeBot Documentation Index

## 🎯 Quick Start (Read First)

1. **`README_STANDARDS.md`** — Quick-start guide to your standards (4.8 KB, 5 min read)
2. **`INSTRUCTIONS_CHEATSHEET.md`** — Fast reference when you need an answer (10 KB, lookup time)
3. **`SIMPLICITY_FIRST.md`** — Deep dive on the 3 rules with examples (11 KB, 15 min read)

---

## 📚 Complete Documentation

### Standards & Guidelines
- **`.github/copilot-instructions.md`** (19 KB) — Master file that agent loads automatically
  - Project context
  - 3 core simplicity rules
  - Code style & conventions
  - Architecture decisions
  - Build & deployment
  - Testing checklist
  - Debugging playbook
  - Key files reference

- **`SIMPLICITY_FIRST.md`** — Why simplicity matters
  - Rule 1: Keep It Simple (no defensive code)
  - Rule 2: Don't Add Code Unless Needed (use SQL instead)
  - Rule 3: Simple Workflow, Not Complex (no async/ML)
  - 15+ code examples
  - Decision tree for complexity

- **`INSTRUCTIONS_CHEATSHEET.md`** — Quick lookup
  - The 3 rules (table format)
  - Architecture quick facts
  - Deployment commands
  - Cost monitoring
  - Testing checklist
  - Debugging playbook
  - Common patterns
  - Environment setup (copy-paste)
  - Red flags & fixes

### How Standards Work
- **`HOW_TO_USE_INSTRUCTIONS.md`** (8.0 KB) — Understanding your standards
  - What changed (before/after)
  - How agent uses standards
  - Example scenarios
  - How to update standards
  - Scope (what they do/don't cover)

- **`README_STANDARDS.md`** (4.8 KB) — Quick-start guide
  - The 3 rules (table)
  - Where to find standards
  - How this works going forward
  - Key highlights
  - Next steps

- **`STANDARDS_SUMMARY.md`** (8.9 KB) — This milestone summary
  - What was done
  - Files created
  - What it means for your project
  - How agent uses standards
  - Status & next steps

### Strategic Guides
- **`TOP_1_PERCENT_PLAYBOOK.md`** (8.8 KB) — Cost & speed optimization
  - Your approach vs. top 1%
  - Time breakdown
  - Cost analysis
  - How to recover time/cost
  - Hybrid approach recommendation

---

## 🚀 Project Architecture

- **`docs/architecture.md`** — System design & component specs
- **`docs/phases.md`** — 4-phase roadmap with effort estimates
- **`docs/signal-format.md`** — MSK signal grammar & regex patterns
- **`docs/cost-controls.md`** — LLM cost tracking & alert thresholds
- **`docs/operations.md`** — Deployment, backup, health check runbook

---

## 🧪 Testing & Results

- **`PHASE1_TEST_RESULTS.md`** — Phase 1 test results & edge cases
- **`CURRENT_STATUS.md`** — Live deployment status & next steps
- **`README_NEXT_STEPS.md`** — Testing guide & troubleshooting
- **`SESSION_CHECKPOINT.md`** — Full state snapshot for resuming work

---

## 🛠️ Infrastructure

- **`infra/stack/docker-compose.yml`** — Service definitions
- **`infra/stack/pg-init/*.sql`** — Database schema (v1, v2, v3)
- **`workflows/phase1-ingest-v2.json`** — Active n8n workflow
- **`.env.example`** — Environment variables template
- **`.gitignore`** — Prevents secrets from being committed

---

## 💻 Scripts

- **`scripts/extract_signals.py`** — Regex signal extraction (offline tool)
- **`scripts/seed_symbols.py`** — Build NSE symbol mapping
- **`scripts/deploy_workflow.py`** — Deploy workflow changes (git-driven)

---

## 📋 Reference Tables

### When You Need...

| Need | File | Type | Read Time |
|------|------|------|-----------|
| Quick answer | INSTRUCTIONS_CHEATSHEET.md | Reference | 5 mins |
| Understand rules | SIMPLICITY_FIRST.md | Guide | 15 mins |
| How agent works | HOW_TO_USE_INSTRUCTIONS.md | Guide | 5 mins |
| Full standards | .github/copilot-instructions.md | Reference | 20 mins |
| Cost/speed analysis | TOP_1_PERCENT_PLAYBOOK.md | Strategic | 10 mins |
| Deployment steps | .github/copilot-instructions.md | Reference | lookup |
| Testing checklist | .github/copilot-instructions.md | Reference | lookup |
| Debugging | INSTRUCTIONS_CHEATSHEET.md | Reference | lookup |
| Architecture | docs/architecture.md | Reference | 20 mins |
| Phases | docs/phases.md | Reference | 10 mins |
| Signal format | docs/signal-format.md | Reference | 10 mins |

---

## 🎯 The 3 Rules (Core)

### Rule 1: Keep It Simple
- No defensive code (you know the 3 groups)
- No over-engineering (MVP first)
- No premature optimization (if it works, keep it)

### Rule 2: Don't Add Code Unless Needed
- No one-time scripts (use SQL)
- No "might be useful" utilities (write when needed)
- No functions with 1 caller (inline it)

### Rule 3: Simple Workflow, Not Complex
- No ML (regex + LLM fallback enough)
- No async (3 groups won't queue)
- No state machines (if/else works)

---

## 📊 Current Status

- **Phase 0** ✅ Infrastructure (VPS, Docker, n8n, Postgres)
- **Phase 1** ✅ Signal capture (regex extraction, tested)
- **Phase 1.5** ⏳ Market context (Fyers price tracking) — Ready to start
- **Phase 2** ⏳ Confirmation (advisor approval)
- **Phase 3** ⏳ Paper trading (mock trades)
- **Phase 4** ⏳ Live trading (real trades)

---

## 🚀 Getting Started With New Work

1. **Open** `README_STANDARDS.md` (quick start)
2. **Read** `SIMPLICITY_FIRST.md` (understand the rules)
3. **Ask** agent to work on feature (e.g., "Add Fyers integration")
4. **Agent** follows all standards automatically
5. **Verify** code matches standards
6. **Commit** with proper message format

---

## 📞 Questions?

| Q | Answer | File |
|---|--------|------|
| How do I deploy? | See "Build & Deploy" section | .github/copilot-instructions.md |
| Is my code too complex? | Check the 3 rules | SIMPLICITY_FIRST.md |
| What's the testing process? | See "Testing Checklist" | .github/copilot-instructions.md |
| How do I debug? | Use the playbook | INSTRUCTIONS_CHEATSHEET.md |
| How do I update standards? | Edit & commit | HOW_TO_USE_INSTRUCTIONS.md |
| What's the project architecture? | System design diagram | docs/architecture.md |
| What are the phases? | 4-phase roadmap | docs/phases.md |
| How are costs controlled? | LLM tracking & alerts | docs/cost-controls.md |

---

## 📁 File Organization

```
tradebot/
├── .github/
│   └── copilot-instructions.md        ← Agent loads this
├── docs/
│   ├── architecture.md
│   ├── phases.md
│   ├── signal-format.md
│   ├── cost-controls.md
│   └── operations.md
├── infra/
│   └── stack/
│       ├── docker-compose.yml
│       └── pg-init/
│           ├── 01-init.sql
│           ├── 02-tradebot-schema.sql
│           ├── 03-tradebot-v2.sql
│           └── 04-llm-usage.sql
├── workflows/
│   └── phase1-ingest-v2.json
├── scripts/
│   ├── extract_signals.py
│   ├── seed_symbols.py
│   └── deploy_workflow.py
├── README_STANDARDS.md               ← Start here!
├── INSTRUCTIONS_CHEATSHEET.md
├── SIMPLICITY_FIRST.md
├── HOW_TO_USE_INSTRUCTIONS.md
├── STANDARDS_SUMMARY.md
├── TOP_1_PERCENT_PLAYBOOK.md
├── README_NEXT_STEPS.md
├── CURRENT_STATUS.md
├── PHASE1_TEST_RESULTS.md
├── SESSION_CHECKPOINT.md
├── INDEX.md                          ← You are here
└── .env                              ← Secrets (not in git)
```

---

## 🎓 Learning Path

### For New Team Members
1. `README_STANDARDS.md` (overview)
2. `docs/architecture.md` (how it works)
3. `.github/copilot-instructions.md` (standards)
4. `SIMPLICITY_FIRST.md` (the 3 rules)
5. `docs/operations.md` (how to deploy)

### For Quick Work
1. `INSTRUCTIONS_CHEATSHEET.md` (quick lookup)
2. Ask agent to work (follows standards automatically)
3. Verify against checklist

### For Strategic Planning
1. `docs/phases.md` (what's coming)
2. `TOP_1_PERCENT_PLAYBOOK.md` (cost/speed)
3. `docs/cost-controls.md` (budget management)

---

## ✅ Status

All documentation complete and committed to GitHub.
Standards are locked and ready for future phases.
Agent knows your project standards automatically.

Ready for Phase 1.5 work! 🚀

---

**Last Updated**: 2026-09-27
**Status**: Standards Complete & Locked ✅
