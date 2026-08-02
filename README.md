# Aether

**Desktop presence operating surface for high-agency builders and creators.**

Governed memory · Live X context · Real-time Grok Voice · Computer-use tools · Action plans · Full auditability

```
Always-available visual presence (tray + floating panel + hotkeys)
+ real-time Grok Voice as first-class citizen
+ governed memory contracts
+ proactive initiation
+ one safety Constitution + kill switch
```

Built by AgentMindCloud. Independent community project. Not affiliated with xAI / Grok / X.

---

## Honest positioning

Aether is **not** a replacement for free Grok Voice on X.

It exists for builders who want:
- An agent they can **inspect, extend, and own**
- **Governed cross-session memory** under their control
- **Proactive behavior** + computer-use tools with spoken safety gates
- Full safety Constitution + kill switch they control
- A single coherent presence surface (tray + voice + action plans)

If you just want good voice conversations, use free Grok Voice.  
If you want a transparent, composable, memory-contract-based presence OS that lives in *your* environment, Aether is for you.

---

## Quick Start

### Option A — One-command (recommended)

```bash
grok-install install github.com/AgentMindCloud/aether
# or
xlos install github.com/AgentMindCloud/aether
```

### Option B — Local demo (zero keys, works offline right now)

```bash
git clone https://github.com/AgentMindCloud/aether.git
cd aether
pip install -e .
aether --demo
# or
python -m aether.runtime --demo
```

You will see the full P0 loop: kill-switch check → session start → governed memory contracts → presence update.

### Option C — Electron shell (tray + panel)

```bash
cd shell
npm install
npm start
```

Tray icon + floating panel appear. Global hotkey: `Ctrl+Alt+A`.

### Live mode (keys required)

```bash
cp .env.example .env
# fill XAI_API_KEY, X_BEARER_TOKEN, GROK_VOICE_API_KEY
aether --check-env
```

---

## Architecture (P0)

```
Native Shell (Electron)          Python Runtime (aether)
┌─────────────────────┐         ┌──────────────────────────────┐
│ Tray + Floating     │  IPC    │ .grok/ contracts             │
│ Panel + Hotkeys     │ ◄─────► │ Swarm + Memory + Voice +     │
│ Presence surface    │         │ Tools + Safety + Presence    │
└─────────────────────┘         └──────────────────────────────┘
```

- Shell owns only OS surface (tray, window, hotkeys, audio routing, screenshot surface).
- All intelligence, memory, safety, voice, and tools live in the Python runtime.
- One process model, one memory model, one safety model, one presence model.

---

## Status

**P0 core scaffold is complete.** See [STATUS.md](STATUS.md).

Next: live Grok Voice Think Fast 2.0 path + full IPC bridge + first-use magic.

---

**Aether** — presence you can own and audit.
