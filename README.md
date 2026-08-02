# Aether

**Desktop presence operating surface for high-agency builders and creators.**

Governed memory · Live X context · Real-time Grok Voice · Computer-use tools · Action plans · Full auditability

Built by AgentMindCloud. Independent community project. Not affiliated with xAI / Grok / X.

---

## Quick Start

### Local demo (zero keys)

```bash
git clone https://github.com/AgentMindCloud/aether.git
cd aether
pip install -e .
aether --demo
```

### Full local (runtime + shell)

```bash
# Terminal 1 — runtime IPC
aether --serve

# Terminal 2 — presence shell
cd shell && npm install && npm start
```

Tray + floating panel. Global hotkey: `Ctrl+Alt+A`.

### Live voice

```bash
cp .env.example .env
# set GROK_VOICE_API_KEY (and optionally XAI_API_KEY / X_BEARER_TOKEN)
aether --check-env
aether --serve
```

---

## What P2 gives you

| Capability | Status |
|------------|--------|
| Voice Think Fast 2.0 path | Ready (live when key present) |
| Governed memory store | File-backed + contracts + consent |
| First-use magic | Audience insight + 3 next moves |
| Computer-use | Screenshot real; confirmation gated |
| Content tools | Ideate / replies / audience insight |
| Action Plan / Make it real | Working |
| IPC | HTTP JSON on :7420 |
| Kill switch | `AETHER_DISABLED=1` |

---

## Architecture

```
Electron shell (tray, panel, hotkeys, screenshot surface)
        │  HTTP :7420
        ▼
Python runtime (.grok/ contracts)
  · Voice client (Think Fast 2.0)
  · Governed memory store
  · Content / engagement tools
  · Computer-use confirmation gate
  · Priority + Action Plan engine
  · Safety + audit
```

---

## Status

**P0 + P1 + P2 complete.** See [STATUS.md](STATUS.md).

**Aether** — presence you can own and audit.
