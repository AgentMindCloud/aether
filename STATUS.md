# Aether Status — Build 0.1 (Felt Presence)

**Date:** 2026-08-02  
**Branch / focus:** `build/0.1-felt-presence` → vertical slice that *feels* like the product.

## What works now (acceptance targets)

| Test | Status |
|------|--------|
| `cd shell && npm start` auto-ensures runtime on :7420 | Hardened (aether / py / python fallbacks + PYTHONPATH) |
| Start Session → type or speak → agent replies | Yes |
| Agent reply is **audible** via Web Speech TTS | Yes (no key required) |
| Mic → Web Speech STT → turn (when permission granted) | Yes |
| Orb: listening → thinking → speaking → listening (no flicker loops) | Yes |
| Premium dark presence UI (hierarchy, glass, motion, transcript first-class) | Yes |
| Memory-aware short/calm replies with one next action | Yes (sim path; uses memory query results) |
| Kill switch `AETHER_DISABLED=1` | Intact |
| Governed memory + Postgres / file fallback | Intact |

## Voice path (honest)

| Layer | State |
|-------|--------|
| Agent text replies | High-quality sim (short, calm, concrete, next-action) |
| TTS playback | **Web Speech API** in renderer — user hears the agent |
| Mic / STT | **Web Speech Recognition** (Chrome/Electron) |
| Grok Voice Think Fast 2.0 / Realtime | Structure ready; requires `GROK_VOICE_API_KEY` + streaming client (not blocking this slice) |

Upgrade path: set `GROK_VOICE_API_KEY`, then wire Realtime WS in `voice.py` + stream audio to shell. Same `/voice/*` endpoints.

## Run (one block)

```powershell
# From repo root (once)
docker compose up -d
pip install -e ".[db,crypto]"

# Daily
cd shell
npm start
# Shell auto-spawns runtime. If offline, status bar shows recovery hint.
```

Manual runtime if needed:

```powershell
aether --serve
# or: py -m aether.runtime --serve
```

## Architecture (unchanged)

```
Electron shell (tray + panel + hotkeys + TTS/STT)
    ↔ HTTP JSON :7420
Python runtime (intelligence, memory, safety)
    ↔ Postgres (facts, consent) / file fallback
    ↔ Ollama (optional)
    ↔ Grok Voice API (live when keyed)
```

**Mobile later:** same HTTP API. Bind with `AETHER_HOST=0.0.0.0`.

## Explicit non-goals this slice

- Full mobile app
- Full X firehose
- Multi-agent swarm rewrite
- Marketplace / grok-install packaging
- Tauri migration

## Version

**0.6.0** — Build 0.1 felt presence
