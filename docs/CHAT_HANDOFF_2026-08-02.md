# Aether Chat Handoff — 2026-08-02

## Product intent (North Star)

**Aether** is a desktop presence operating surface for high-agency builders and tech-curious creators.

One-sentence definition:  
*Always-available presence (tray + floating panel + hotkeys) with real-time Grok Voice, governed memory, live X context, gated computer-use, and an Action Plan / “Make it real” loop — think with me, not just do for me.*

### Core requirements (original)
- Desktop presence: system tray + floating panel + global hotkeys
- Real-time end-to-end Grok Voice (Think Fast 2.0 / Realtime API) as first-class
- Governed memory contracts (provenance, confidence, scope, retention, write permission)
- Live X context injection
- Computer-use tools with spoken safety confirmation gates
- Proactive initiation (opt-in, rate-limited)
- Single safety Constitution + kill switch
- Content ideation / engagement tools + audience insights
- Personalization via governed memory across sessions
- Action Plan / “Make it real” system
- First-use magic without heavy setup
- Progressive power: natural language default; YAML/power-user later
- Magical install path via grok-install / xlOS (later)
- **Mobile surface later** — same brain (HTTP API), phone can talk to agent

Source material only (do **not** merge codebases):
- Creator X Companion (Electron tray + priority/bookmarks/action plan UI)
- Vesper (Python voice agent, memory contracts, swarm, safety)

Repo: https://github.com/AgentMindCloud/aether

---

## What works today (P0–P5.1)

| Area | Status |
|------|--------|
| Clean repo scaffold + `.grok/` contracts | Done |
| Electron shell (tray, panel, hotkey Ctrl+Alt+A) | Done |
| Python runtime IPC on `:7420` | Done |
| Auto-spawn runtime from shell (mostly 1-window) | Done |
| Postgres memory backend + file fallback | Done |
| Consent, write, feedback, distill learning path | Done (`aether --demo`) |
| Ollama health detection | Done |
| First-use Magic API + button | Done |
| Start Session → text turn → simulated reply | Done (sim path only) |
| Presence orb states (no IPC feedback loop) | Done |
| Priority / Bookmarks / Make it real (basic) | Done |
| Computer-use screenshot (gated + shell execute) | Stub works |
| Kill switch `AETHER_DISABLED=1` | Done |

### How user runs it
```powershell
cd $HOME\aether\shell
npm start
# shell auto-spawns aether --serve if needed
# Postgres: docker compose up -d from repo root if needed
```

### Confirmed on user machine
- Docker Postgres `aether-postgres` healthy on 5432
- `backend: postgres` in demo
- Ollama available with multiple local models
- Shell shows Runtime: connected
- First-use Magic works
- Start Session shows listening; text turns can reply in sim mode

---

## What is NOT working / missing (user pain)

1. **Speaking never really worked**  
   - No real Grok Voice Think Fast 2.0 / Realtime audio path wired end-to-end  
   - No mic capture, no STT streaming, no TTS playback in the shell  
   - “Listening” is a UI state only; agent does not hear the user  
   - Simulated text replies are weak / not felt as “doing something”

2. **Agent feels inert**  
   - After Start Session, user expectation is conversation + action  
   - Turn responses must be higher quality (memory-aware, short, next-action oriented)  
   - Need clear “agent did X” feedback (not just status labels)

3. **UI is not premium**  
   - Current panel is functional dark UI, not the premium presence surface described  
   - Missing polish: motion design, hierarchy, density, typography, glass/depth, micro-interactions  
   - Companion-era Priority/Bookmarks feel bolted on, not redesigned  
   - User stated: *“the way the app looks is not good, it has not updated to the more premium feel at all”*

4. **Grok Voice Agent design notes (pasted earlier by user) not implemented**  
   - Any specific visual/interaction/voice-agent UX updates from that design pass were not carried into shell  
   - Treat this as a gap: re-read user-pasted voice-agent direction and implement systematically

5. **Two-process mental model still fragile**  
   - Auto-spawn exists but can fail silently depending on PATH/`aether` install  
   - Need reliable single entry: one shortcut / one `npm start` always brings brain + face online

6. **Mobile**  
   - Not built  
   - Architecture note only: same HTTP API; bind `0.0.0.0` for LAN later

7. **Live X context, real proactive, full computer-use, marketplace, grok-install packaging**  
   - Mostly stubs or contracts only

---

## Architecture (current)

```
Electron shell (tray + panel)
    ↔ HTTP JSON :7420
Python runtime (intelligence)
    ↔ Postgres (facts, consent)
    ↔ Ollama (local models optional)
    ↔ Grok Voice API (not live yet — needs key + streaming client + shell audio)
```

Irreversible choices already made:
- Electron thin shell (not Tauri) for speed of P0
- Python owns memory, voice session logic, tools, safety
- HTTP IPC (not raw Electron IPC for intelligence) so mobile can share the brain later

---

## User environment notes

- Windows (PowerShell), path `C:\Users\louis\aether`
- Docker available; Postgres via `docker compose` in repo
- Ollama running with models including `llama3.1:8b`, `nomic-embed-text`, etc.
- SuperGrok user; product owner is building AgentMindCloud / creator tooling

---

## Honest assessment

We have a **scaffold with a working local memory/learning loop and a basic presence shell**.  
We do **not** yet have the product the North Star describes: a voice-first presence that speaks, listens, looks premium, and continuously earns trust through useful action.

Next work must prioritize **felt experience**: audio voice path, premium UI, and agent turns that clearly help — not more backend surface area alone.
