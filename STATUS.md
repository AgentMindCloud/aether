# Aether Status — Build 0.1 FINISHED (Presence)

**Date:** 2026-08-03  
**Decision:** Aether is the **presence surface only**. Super Grok Voice Agent is a **separate project**. Aether does not need to speak.

## Done criteria

| Item | Status |
|------|--------|
| Electron tray + panel + Ctrl+Alt+A | Done |
| Auto-spawn Python runtime `:7420` | Done |
| Text session turns (memory-aware sim) | Done |
| Priority / Bookmarks / Make it real | Done |
| Postgres memory + file fallback | Done |
| Kill switch `AETHER_DISABLED=1` | Done |
| **Windows Desktop shortcut** | Done — run `shell/create-desktop-shortcut.ps1` once |
| One-click launch (no manual PowerShell path) | Done — Desktop “Aether” or `Start-Aether.vbs` |

## How to run (Windows 11)

**Once:**

```powershell
cd C:\Users\louis\aether
git pull origin main
cd shell
npm install
powershell -ExecutionPolicy Bypass -File .\create-desktop-shortcut.ps1
```

Also from repo root (once): `docker compose up -d` and `pip install -e ".[db,crypto]"` if not already.

**Daily:** double-click **Aether** on the Desktop.

## Scope freeze (do not expand)

- No Super Agent tools/jobs here
- No requirement for natural voice TTS
- No Supabase, no n8n core
- Mobile = future thin client to same HTTP API only

## Super Agent

See `docs/SUPER_GROK_VOICE_AGENT_PROMPT.md` — build in a **new repo**. Optional later: Aether calls Partner HTTP API.

## Version

**0.6.1** — Build 0.1 finished (presence + desktop launch)
