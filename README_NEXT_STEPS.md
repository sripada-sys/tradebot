# Next Steps - Ready for Real WhatsApp Testing

## Current State
✅ **Phase 1 infrastructure is LIVE and TESTED**
- Webhook endpoint active: `http://65.20.79.45:5678/webhook/whatsapp-in`
- Signal extraction: Working (proven with test messages)
- Database: All schemas deployed and operational
- Cost tracking: Ready (under free tier)

## When You're Ready to Test with Real Signal

### Step 1: Get MSK Admin to Send Signal
Ask any MSK group admin to send a trade signal in the standard format:
```
POSITIONAL TRADE
STOCK_NAME
Looks Good ABOVE entry_price
SL stop_loss
Targets target1 target2 target3
```

Example:
```
POSITIONAL TRADE
RELIANCE
Looks Good ABOVE 1250
SL 1230
Targets 1280 1310 1340
```

### Step 2: Verify Reception
Check if signal was captured:
```bash
# SSH to VPS
ssh root@65.20.79.45

# Check signals table (latest entries)
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT id, message_id, nse_symbol, entry_price, stop_loss, confidence, created_at FROM signals ORDER BY created_at DESC LIMIT 5;"

# Check workflow executions
docker exec -i stack-postgres psql -U stackadmin -d n8n -c \
  "SELECT COUNT(*) FROM execution_entity WHERE workflowId = 'bf7e41466a2cfac1' AND status = 'success';"

# Monitor n8n logs in real-time
docker logs -f stack-n8n | grep -i "whatsapp\|error"
```

### Step 3: If Signal Appears ✅
Congratulations! Phase 1 is complete. Move to **Phase 1.5: Price Tracking**

Tasks:
1. Add Fyers API integration to fetch prices at message time
2. Calculate slippage (advisor entry vs. market price)
3. Measure latency (message timestamp vs. capture time)
4. Populate signals_market_context table

### Step 4: If Signal Doesn't Appear ❌
Debug steps:
1. Check n8n logs for errors: `docker logs stack-n8n | tail -100`
2. Verify webhook was triggered: `docker exec -i stack-postgres psql -U stackadmin -d n8n -c "SELECT COUNT(*) FROM execution_entity WHERE workflowId = 'bf7e41466a2cfac1';"`
3. Check if stock is in symbol table: `docker exec -i stack-postgres psql -U stackadmin -d n8n -c "SELECT * FROM symbols WHERE stock_name_raw = 'STOCK_NAME';"`

---

## Infrastructure Access

### n8n Editor
- URL: http://65.20.79.45:5678
- Username: `admin`
- Password: `JTYInY4QXNaXcxXdROeE`

### SSH Access
```bash
ssh root@65.20.79.45
# Uses: ~/.ssh/id_ed25519
```

### Database Access
```bash
ssh root@65.20.79.45 "docker exec -i stack-postgres psql -U stackadmin -d n8n"
```

---

## Cost Status
- VPS: ~$6/month
- Gemini API: $0 (under free tier with 10 test messages)
- **Total: $6/month** ✅

---

## Files Changed This Session
- PHASE1_TEST_RESULTS.md - Detailed test results
- CURRENT_STATUS.md - Live deployment status
- Workflow: Phase 1 v2 → WhatsApp Signal Ingest
- Database: Postgres schemas v1, v2, v3 fully deployed

---

## Troubleshooting Quick Links

**Webhook not firing?**
- Check: `docker exec -i stack-postgres psql -U stackadmin -d n8n -c "SELECT * FROM webhook_entity;"`

**Signal not creating?**
- Check: `docker logs stack-n8n | grep -i "error\|signal"`
- Check: `docker exec -i stack-postgres psql -U stackadmin -d n8n -c "SELECT COUNT(*) FROM signals;"`

**Connection issues?**
- VPS IP: 65.20.79.45
- Firewall allows: TCP 5678 (n8n), 8080 (Evolution API)
- Check: `ssh root@65.20.79.45 "docker ps"`

---

## Git Status
All changes committed:
- `6e8e7f9` - Add current deployment status
- `28344ff` - Phase 1 v2 end-to-end test results
- `1620dff` - Cost controls & OpenRouter setup

Pull latest: `git pull origin main`

---

**Recommendation:** Have an MSK admin send a test signal when convenient. The system is ready! 🚀
