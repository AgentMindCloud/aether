# Grok Build 0.1 — Prompt (copy into next build session)

You are operating in full SuperGrok Personalized God Mode with Ultra Grok Expanded Skill System for AgentMindCloud / Aether.

Repo: https://github.com/AgentMindCloud/aether  
Read first: `docs/CHAT_HANDOFF_2026-08-02.md`

## Mission

Close the gap between **scaffold** and **felt product**. The user confirmed: listening state works, speaking has never worked, the agent “does nothing,” and the UI is not premium. Do not expand feature surface randomly. Deliver a vertical slice that *feels* like Aether.

## Non-negotiables

- Do NOT merge Vesper or Creator X Companion codebases; patterns only.
- Keep dual-runtime: Electron shell + Python `:7420` brain (mobile-ready HTTP).
- Keep governed memory contracts + kill switch.
- One-window start must remain: `cd shell && npm start` auto-ensures runtime.
- Be maximally truth-seeking; if Voice API cannot be live without keys, make sim path *excellent* and document the one env var for live.

## P0 outcome for this build (must ship)

### 1. Agent actually converses (felt)
- After **Start Session**, user can talk via **text now** and see high-quality replies that:
  - use memory query results when relevant
  - stay short, calm, concrete (honor stored preference)
  - propose **one** next action when appropriate
- Presence must track turns: listening → thinking → speaking → listening (no vibration loops).
- “Speaking” must be visible and timed (orb + optional status line with last reply snippet).
- If `GROK_VOICE_API_KEY` / Realtime is available, wire **best-effort live path**; otherwise ship a **premium sim** that still feels alive (typed “voice” turns + optional browser TTS for agent line).

### 2. Real speaking path (minimum viable audio)
Priority order:
1. Agent reply → **speech synthesis playback** in shell (Web Speech API or better) so “speaking” is audible.
2. Mic capture → transcript → `/voice/turn` (even if STT is Web Speech API) so “listening” is real.
3. Document upgrade path to Grok Voice Think Fast 2.0 Realtime streaming.

User must hear the agent at least once without extra setup.

### 3. Premium presence UI (visual rewrite of shell)
Redesign `shell/` panel to premium dark presence product — not a generic todo list:
- Strong hierarchy: Presence hero → Talk → Priority as secondary
- Typography, spacing, subtle motion, glass/depth, refined orb
- Session transcript as first-class, not a cramped add-on
- Priority items not screaming all-red; severity is rare
- Empty/listening/speaking states must feel intentional
- Keep tray + frameless + Ctrl+Alt+A

### 4. Reliability
- Auto-spawn runtime rock-solid on Windows (PATH, `py -m aether.runtime --serve` fallback)
- Clear UI when runtime/Postgres/Ollama is down (no silent “listening”)
- Restart instructions in README one block only

## Explicit non-goals this slice
- Full mobile app
- Full X firehose
- Multi-agent swarm rewrite
- Marketplace / grok-install packaging polish
- Tauri migration

## Implementation order
1. Shell UI redesign (HTML/CSS/JS) — presence + transcript first
2. Mic + TTS in renderer (permissions, buttons, states)
3. Runtime turn quality (memory-aware, preference-aligned replies; improve `voice.py` sim)
4. Live Voice stub only if keys present — do not block on it
5. STATUS.md + README “What works / what doesn’t”

## Acceptance tests (user will run)
1. `npm start` alone → Runtime connected without second window (or clear recovery).
2. Start Session → **speak or type** → agent **audible or clearly spoken-state reply** within a few seconds.
3. Orb shows thinking then speaking without flicker loops.
4. UI looks intentionally premium vs previous panel.
5. Preference “short calm answers + concrete next actions” is reflected in replies when fact exists in Postgres.

## Deliverables
- Working code on `main`
- Updated `STATUS.md`
- Short note on mobile: same API, `AETHER_HOST=0.0.0.0` later

No questions if path is clear. Build until the acceptance tests pass or document the single blocker (e.g. missing mic permission) with the fix.

Start with the handoff doc, inspect current `shell/` + `src/aether/voice.py`, then ship the vertical slice.
