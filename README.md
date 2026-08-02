# Aether

**Desktop presence operating surface for high-agency builders.**

Governed memory (Postgres) · Learning loop · Ollama · Grok Voice · Live X · Computer-use · Action plans

**v0.5.0** — built for years of use. Owned by you. Not affiliated with xAI / Grok / X.

---

## Quick start (durable path)

```bash
git clone https://github.com/AgentMindCloud/aether.git
cd aether
docker compose up -d
pip install -e ".[db,crypto]"
aether --demo
aether --serve
```

Shell:

```bash
cd shell && npm install && npm start
```

---

## Architecture

```
Electron shell
     │ HTTP :7420
     ▼
Python runtime
  · Voice (Think Fast 2.0 path)
  · Governed memory → Postgres (Docker) / file fallback
  · Learning (feedback + distill)
  · Ollama (local embeddings / fallback)
  · Proactive + optional n8n tool
  · GitHub tools · Content · Computer-use gates
  · Kill switch + audit
```

**Memory is local and owned.** n8n is automation muscle only.

---

## Key endpoints

| Area | Endpoints |
|------|-----------|
| Memory | `/memory/write` `/memory/query` `/memory/consent` `/memory/stats` |
| Learning | `/learning/feedback` `/learning/distill` `/learning/status` |
| Voice | `/voice/start` `/voice/turn` `/voice/partial` `/voice/end` |
| Model | `/model` `/switch-model` |
| Ollama | `/ollama` |
| GitHub | `/github/issues` `/github/prs` |
| n8n | `/n8n/webhook` |

---

See [STATUS.md](STATUS.md).
