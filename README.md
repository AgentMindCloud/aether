# Aether

**Desktop presence operating surface for high-agency builders and creators.**

Governed memory · Live X context · Real-time Grok Voice · Computer-use tools · Action plans · Full auditability

Version **0.3.0** (P3). Built by AgentMindCloud. Not affiliated with xAI / Grok / X.

---

## Quick Start

```bash
git clone https://github.com/AgentMindCloud/aether.git
cd aether
pip install -e ".[crypto]"   # crypto optional but recommended
aether --demo
```

Full local:

```bash
aether --serve               # IPC :7420
cd shell && npm install && npm start
```

Package the shell:

```bash
cd shell && npm run dist     # or dist:win / dist:mac / dist:linux
```

Live voice: set `GROK_VOICE_API_KEY` in `.env`.

---

## Capabilities (P3)

| Area | Status |
|------|--------|
| Voice Think Fast 2.0 + Realtime structure | Ready |
| Partial transcripts | `/voice/partial` |
| Governed memory + Fernet encryption | Ready (optional dep) |
| Proactive (opt-in, cooldown, spikes) | Ready |
| Computer-use (screenshot + gates) | Ready |
| Content ideation / replies / insight | Ready |
| Action Plan / Make it real | Ready |
| electron-builder packaging | Configured |
| Kill switch | `AETHER_DISABLED=1` |

---

## Architecture

```
Electron shell (tray, panel, hotkeys, screenshot)
        │  HTTP :7420
        ▼
Python runtime v0.3
  · Voice client (Think Fast 2.0 / Realtime-ready)
  · Encrypted governed memory store
  · Proactive engine
  · Content tools
  · Computer-use confirmation gate
  · Priority + Action Plan
  · Safety + audit
```

---

See [STATUS.md](STATUS.md) for the full checklist.

**Aether** — presence you can own and audit.
