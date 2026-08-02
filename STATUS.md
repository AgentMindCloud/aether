# Aether Status — 2026-08-02 (P4 complete)

## Architecture decision (locked)

**Aether brain stays local and owned.**  
n8n / Supabase are optional *tools*, never the core memory or orchestration brain.  
Hybrid voice + UI buttons + GitHub actions + modular LLM slots are first-class inside the existing Electron + Python + `.grok/` design.

## Ready

### P0–P3
- [x] Presence shell, contracts, kill switch, voice path, encrypted memory, proactive, packaging

### P4 (from console.x.ai voice-agent input — filtered)
- [x] **LLM abstraction** — `.grok/models.yaml` + `/model` + `/switch-model` + `AETHER_MODEL` env
- [x] **Tool registry expansion** — GitHub issues/PRs/create-issue staged tools
- [x] **Optional n8n webhook tool** — explicit external orchestration only; memory never leaves Aether
- [x] **Hybrid action suggestions** — voice turns return `suggested_actions` for floating UI buttons
- [x] Version **0.4.0**

## Explicit non-goals (still)

- Supabase / Postgres as primary memory
- n8n as the agent brain
- Dual-runtime ownership split

## Run

```bash
pip install -e ".[crypto]"
aether --demo
aether --serve
cd shell && npm start
```

## Next high-leverage

- Live GitHub connector calls (use platform GitHub tools for real list/create)
- Panel UI for suggested_actions + recent audit
- Real Grok Voice Realtime WebSocket when keys present
- Richer computer-use (type/click) behind existing gates

**P4 goal achieved: modular model, GitHub tools, optional n8n, hybrid suggestions — without surrendering ownership.**
