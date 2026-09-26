# n8n workflows

Export workflows from n8n and commit them here as JSON.

**Never** commit workflow exports that contain live credentials. Suggested naming:

- `phase1-ingest.json` — WhatsApp webhook → regex extract → Postgres insert
- `phase2-confirm.json` — signal → WhatsApp proposal → wait-for-reply → mark approved
- `phase3-paper.json` — approved signals → Fyers quotes → paper_orders logging
- `phase4-live.json` — full live path with kill-switch and caps

To export from n8n UI: open a workflow → `⋯` menu → **Download**.

## Import into a fresh n8n

n8n UI → `Workflows` → `Import from file` → pick JSON.

After import, re-attach credentials (Postgres, Evolution API, LLM) — these are
intentionally *not* in the JSON exports.
