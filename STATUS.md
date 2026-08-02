# Aether Status — 2026-08-02 (P5 + learning path)

## Long-horizon decisions (locked)

| Need | Solution |
|------|----------|
| Remember across sessions | **Postgres** primary + file fallback |
| Learn / get better | **Feedback → confidence** + **distill session → user** |
| Local models | **Ollama** |
| Automation | Proactive + optional n8n tool |
| Core memory | Owned Postgres — not Supabase |

## Default Postgres (your machine)

```
Host: localhost
Port: 5432
User: postgres
Password: postgres
Database: postgres
DSN: postgresql://postgres:postgres@127.0.0.1:5432/postgres
```

## Learning path (tasks 1–3) — run with `aether --demo`

1. **Consent** — grant cross-session (`set_cross_session_consent(True)`)
2. **Write** — user preference + session fact into governed store
3. **Feedback** — mark preference useful (confidence + feedback_score update)

Plus: query, distill, final stats.

## Run

```bash
pip install -e ".[db,crypto]"
aether --demo
# Expect: backend = "postgres"
aether --serve
```

## Version

**0.5.0**
