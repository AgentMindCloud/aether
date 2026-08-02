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

---

## Quick Start

### Option A — One-command (recommended)

```bash
grok-install install github.com/AgentMindCloud/aether
# or
xlos install github.com/AgentMindCloud/aether
```

### Option B — Local demo (zero keys)

```bash
git clone https://github.com/AgentMindCloud/aether.git
cd aether
pip install -e .
aether --demo
```

Full P1 loop: kill-switch → session → first-use magic → memory contracts → computer-use confirmation → Make it real → presence.

### Option C — Full local (runtime + shell)

```bash
# Terminal 1
aether --serve          # IPC on http://127.0.0.1:7420

# Terminal 2
cd shell && npm install && npm start
```

Tray + floating panel with Priority list, Bookmark Intelligence, Make it real, first-use button, and live presence.

### Live mode (keys required)

```bash
cp .env.example .env
# fill XAI_API_KEY, X_BEARER_TOKEN, GROK_VOICE_API_KEY
aether --check-env
```

---

## Architecture

```
Native Shell (Electron)          Python Runtime (aether)
┌─────────────────────┐         ┌──────────────────────────────┐
│ Tray + Floating     │  HTTP   │ .grok/ contracts             │
│ Panel + Hotkeys     │ ◄─────► │ Swarm + Memory + Voice +     │
│ Priority / Plans    │  :7420  │ Tools + Safety + Presence    │
│ Presence surface    │         │ First-use + Make it real     │
└─────────────────────┘         └──────────────────────────────┘
```

- Shell owns only OS surface.
- All intelligence, memory, safety, voice, and tools live in the Python runtime.
- Computer-use actions always require spoken confirmation before execution.

---

## Status

**P0 + P1 complete.** See [STATUS.md](STATUS.md).

Next focus: live Grok Voice Think Fast 2.0 path + real computer-use surfaces behind the existing safety gates.

---

**Aether** — presence you can own and audit.
