# Operations runbook

## Server access

```bash
ssh root@65.20.79.45           # passwordless via ~/.ssh/id_ed25519
```

## Deploy from scratch on a fresh Ubuntu 24.04 box

```bash
# 1. Install Docker (once)
apt update && apt install -y ca-certificates curl gnupg git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 2. Get stack files
mkdir -p /opt/stack && cd /opt/stack
# (copy docker-compose.yml, .env, pg-init/init.sql from this repo)

# 3. Generate real secrets in .env, then:
docker compose pull
docker compose up -d
docker compose ps
```

## Daily commands

```bash
# Status
docker compose -f /opt/stack/docker-compose.yml ps

# Logs (one service)
docker logs -f stack-n8n
docker logs -f stack-evolution
docker logs -f stack-postgres

# Restart a service
docker compose -f /opt/stack/docker-compose.yml restart n8n

# Resource use
docker stats --no-stream
free -h
df -h
```

## Backup

```bash
# Postgres nightly dump
docker exec stack-postgres pg_dumpall -U stackadmin \
  | gzip > /opt/backups/pg-$(date +%F).sql.gz

# n8n workflows are already in Postgres, so the above covers them.

# Evolution WhatsApp session (so you don't need to re-scan QR)
docker run --rm -v stack_evolution_instances:/data -v /opt/backups:/backup \
  alpine tar -czf /backup/evo-instances-$(date +%F).tgz -C /data .
```

Add to `/etc/cron.d/tradebot-backup`:
```
0 2 * * * root /opt/scripts/backup.sh
```

## Restore

```bash
# Postgres
gunzip -c /opt/backups/pg-2026-09-26.sql.gz | \
  docker exec -i stack-postgres psql -U stackadmin

# Evolution session
docker run --rm -v stack_evolution_instances:/data -v /opt/backups:/backup \
  alpine tar -xzf /backup/evo-instances-2026-09-26.tgz -C /data
```

## Rotating secrets

1. Edit `/opt/stack/.env` on server.
2. `docker compose -f /opt/stack/docker-compose.yml up -d` (recreates containers with new envs).
3. If you rotate `N8N_ENCRYPTION_KEY`, all stored credentials become unreadable — **don't rotate unless you're prepared to re-enter them**.

## Health checks

```bash
curl -s http://65.20.79.45:8080 | jq .          # Evolution should return status 200
curl -sI http://65.20.79.45:5678 | head -1      # n8n should return 200 or 401
```

## Kill switch (Phase 4)

```sql
UPDATE system_flags SET trading_enabled = false;
```

Or from WhatsApp: message the bot with `STOP` (n8n workflow handles it).

## Common issues

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| n8n 401 on all requests | wrong basic-auth password | check `.env`, restart n8n |
| Evolution QR keeps refreshing | phone can't reach server | check firewall on port 8080 |
| Signals not appearing | webhook not set in Evolution | re-set webhook via API (see below) |
| High memory / OOM | too many n8n executions | prune history: `n8n executions:prune` |

### Setting Evolution webhook to n8n

```bash
curl -X POST http://65.20.79.45:8080/webhook/set/msk-bot \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://n8n:5678/webhook/whatsapp-in",
    "webhook_by_events": false,
    "events": ["MESSAGES_UPSERT"]
  }'
```

(Note: `n8n:5678` because containers share the `stacknet` network.)
