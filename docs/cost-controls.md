# Cost Controls — Keep Recurring Bill Near Zero

## LLM Model Allowlist

Only Gemini-family low-cost models. **Never** GPT-4/Claude Opus/Gemini Pro.

| Model | Input $/1M | Output $/1M | Used For |
|---|---|---|---|
| `google/gemini-2.0-flash-exp:free` | **$0** | **$0** | **Default** — free tier |
| `google/gemini-flash-1.5-8b` | $0.038 | $0.15 | Paid fallback if free rate-limited |
| `google/gemini-flash-1.5` | $0.075 | $0.30 | Emergency fallback only |

Configured in the workflow's LLM node — do not change to any other model.

## Pre-LLM Filters (No-Cost Skips)

The regex extractor node **short-circuits before calling LLM** if the message:

- Is > 2000 chars (likely article/copy-paste)
- Is < 20 chars (likely emoji reply)
- Matches skip patterns: `🔥`, "target hit", "booked", "profit booked", "good morning", "thank", emojis
- Matches PnL update patterns: `+5%`, `-2%`, "profit of", "return of"
- Is a bare URL (YouTube, Telegram, HTTP link)
- Has no numbers OR no signal keywords (buy/sell/target/sl/entry/etc.)

Result: **~80% of noise never touches the LLM.**

## Hard Budget Caps

- `max_tokens: 300` on every LLM call
- `temperature: 0` (deterministic, no wasted retries)
- 15-second timeout per call
- Response format: `json_object` (no verbose prose)

## Kill Switch

```bash
# Disable LLM entirely (regex-only mode)
ssh root@65.20.79.45 "cd /opt/stack && sed -i 's/^LLM_ENABLED=.*/LLM_ENABLED=false/' .env && docker compose up -d n8n"

# Re-enable
ssh root@65.20.79.45 "cd /opt/stack && sed -i 's/^LLM_ENABLED=.*/LLM_ENABLED=true/' .env && docker compose up -d n8n"
```

## Usage Tracking

Every LLM call logged to `llm_usage` table with token counts + cost estimate.

### Daily cost check
```sql
SELECT * FROM v_llm_daily_cost LIMIT 14;
```

### Monthly total
```sql
SELECT * FROM v_llm_monthly_cost LIMIT 6;
```

### Quick command
```bash
ssh root@65.20.79.45 "docker exec stack-postgres psql -U stackadmin -d n8n -c 'SELECT * FROM v_llm_monthly_cost LIMIT 3;'"
```

## Expected Costs

**Baseline scenario** (200 msgs/day across 3 groups):

| Layer | Volume | Cost |
|---|---|---|
| Regex catch | ~140 msgs | $0 |
| Pre-LLM filter skips | ~40 msgs | $0 |
| LLM (free tier) | ~20 calls | **$0** |
| **Total** | | **$0/month** |

**Worst case** (free tier throttled, all calls hit paid 8b):
- 20 calls × 30 days × 500 tokens avg = 300k tokens = **~$0.02/month**

## Other Recurring Costs

| Item | Cost |
|---|---|
| Vultr VPS (2GB) | ~$6/month |
| Domain (optional, Phase 4) | ~$1/month |
| Postgres/Redis/Evolution/n8n | $0 (self-hosted) |
| OpenRouter LLM | ~$0/month |
| **Total** | **~$6/month** |

## Alerts (Future — Phase 2)

Add a scheduled workflow to email/DM you if:
- Daily LLM cost > $0.10
- Monthly LLM cost > $2
- LLM call count > 500/day (potential loop)
