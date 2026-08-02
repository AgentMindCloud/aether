# Aether Status — 2026-08-02 (P5 complete)

## Long-horizon decisions (locked)

| Need | Solution |
|------|----------|
| Remember across sessions | **Postgres** (Docker) primary + file fallback |
| Learn / get better | **Feedback → confidence** + **distill session → user** (consent) |
| Local models | **Ollama** (embeddings + optional chat) |
| Automation | Aether proactive + **optional n8n webhook tool** |
| Core memory | Owned Postgres on your machine — not Supabase |

n8n is never the brain. Slack/Notion are optional notification targets via n8n, not required for memory or learning.

## P5 shipped

- [x] `docker-compose.yml` — Postgres 16
- [x] Governed memory: Postgres primary, encrypted file fallback
- [x] Learning: `/learning/feedback`, `/learning/distill`, `/learning/status`
- [x] Ollama client + health in `/health`
- [x] Consent-gated cross-session + promotion path
- [x] Version **0.5.0**

## Run (years-grade path)

```bash
docker compose up -d
pip install -e ".[db,crypto]"
# optional: ollama pull nomic-embed-text
aether --demo
aether --serve
cd shell && npm start
```

Default DSN: `postgresql://aether:aether_local_dev@127.0.0.1:5432/aether`  
Override: `AETHER_DATABASE_URL`

## Next (optional)

- Real GitHub connector execution
- Ollama embeddings in query ranking
- Panel UI for feedback + suggested actions
- Live Grok Voice Realtime WebSocket
