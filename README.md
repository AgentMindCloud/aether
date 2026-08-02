# Aether

**Desktop presence operating surface for high-agency builders.**

Always-available tray + floating panel with real-time talk, governed memory, gated computer-use, and an Action Plan loop — *think with me, not just do for me*.

**v0.6.0 — Build 0.1 Felt Presence**  
Owned by you. Not affiliated with xAI / Grok / X.

---

## Quick start

```bash
git clone https://github.com/AgentMindCloud/aether.git
cd aether
docker compose up -d
pip install -e ".[db,crypto]"
cd shell && npm install && npm start
```

One command brings brain + face online. The shell auto-spawns the Python runtime on `:7420`.

**Talk path (no API key required):**
1. Click **Start Session**
2. Type a message (or use the mic button)
3. Agent replies in the session panel **and speaks** via system TTS

Optional live Grok Voice later: set `GROK_VOICE_API_KEY` in `.env`.

---

## What works (Build 0.1)

- Premium dark presence UI (orb states, glass, motion, transcript-first)
- Start Session → high-quality short replies (memory-aware when facts exist)
- **Audible agent** via Web Speech TTS
- Mic input via Web Speech Recognition (permission-gated)
- Governed memory (Postgres primary, file fallback)
- Priority / Bookmarks / Make it real
- Computer-use screenshot (gated)
- Kill switch `AETHER_DISABLED=1`
- Auto-spawn runtime with Windows-friendly fallbacks

See [STATUS.md](STATUS.md) for acceptance table and honest gaps.

---

## Architecture

```
Electron shell (tray · panel · hotkeys · TTS/STT)
     │ HTTP :7420
     ▼
Python runtime
  · Voice (sim + Think Fast 2.0 path)
  · Governed memory → Postgres / file
  · Learning (feedback + distill)
  · Ollama · Proactive · GitHub · Content
  · Computer-use gates · Kill switch · Audit
```

**Mobile later:** same HTTP API. `AETHER_HOST=0.0.0.0` for LAN.

---

## Key endpoints

| Area | Endpoints |
|------|-----------|
| Voice | `/voice/start` `/voice/turn` `/voice/partial` `/voice/end` |
| Memory | `/memory/write` `/memory/query` `/memory/consent` `/memory/stats` |
| Learning | `/learning/feedback` `/learning/distill` `/learning/status` |
| Priority | `/priority` `/priority/add` `/make-it-real` |
| Computer-use | `/computer-use/request` `/computer-use/confirm` |

---

## Safety

Single Constitution + kill switch. Computer-use always requires spoken (or explicit) confirmation before shell execution.
