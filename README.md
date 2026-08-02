# Aether

**Desktop presence surface** for high-agency builders.

Tray + floating panel + hotkeys. Governed local memory. Text talk loop. Action plans.

**v0.6.1 — Build 0.1 finished.**  
Voice partner / Super Agent is a **separate project**. Aether does not need to speak.

Not affiliated with xAI / Grok / X.

---

## Windows 11 — one-time setup

```powershell
cd C:\Users\louis\aether
git pull
docker compose up -d
pip install -e ".[db,crypto]"
cd shell
npm install
powershell -ExecutionPolicy Bypass -File .\create-desktop-shortcut.ps1
```

Then double-click **Aether** on your Desktop every day.

Fallback: `shell\Start-Aether.vbs` (no console) or `shell\Start-Aether.bat`.

Hotkey: **Ctrl+Alt+A** focuses capture.

---

## What it is / is not

| Is | Is not |
|----|--------|
| Presence panel + tray | Super autonomous agent |
| Local Postgres memory | Supabase required |
| Text sessions + priority | Product voice partner (see Partner repo) |
| Kill switch + gated computer-use stub | n8n brain |

---

## Architecture

```
Desktop shortcut → Electron shell
                      ↔ HTTP :7420
                   Python runtime + Postgres
```

---

## Super Grok Voice Agent

Build separately. Handoff prompt: [docs/SUPER_GROK_VOICE_AGENT_PROMPT.md](docs/SUPER_GROK_VOICE_AGENT_PROMPT.md).

---

See [STATUS.md](STATUS.md).
