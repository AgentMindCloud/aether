# Super Grok Voice Agent — Handoff Prompt for Another AI

Copy everything below the line into a new build session. Product owner will later bring the result back to SuperGrok for X/xAI fine-tuning.

---

You are building **Partner** (working name: Super Grok Voice Agent) for a solo high-agency builder. This is NOT the Aether presence UI. Aether is a separate finished product (desktop tray/panel). Partner is the **#1 operating partner brain**: Grok-powered voice + text, deep memory, learning, tools, background jobs, and autonomy under strict safety.

## North Star

A durable personal partner that:
- Speaks and listens via **Grok Voice / Realtime API** (primary)
- Remembers across months (governed memory + learning)
- Runs work while the user is offline (job queue)
- Uses real tools (GitHub, web, X, HTTP, optional Buzz)
- Confirms irreversible actions
- Is reachable from voice, HTTP API, and later Aether / Buzz / phone

## Hard constraints

- **Memory store: Postgres + pgvector** (Docker or VPS). Do not require Supabase.
- **Voice: Grok Voice Agent / Realtime** when `XAI_API_KEY` / voice key present. Compatible with OpenAI Realtime-style APIs where xAI documents it. Fallback TTS only temporary — product voice must not be OS robotic voice.
- **Kill switch** env: `PARTNER_DISABLED=1`.
- **Constitution** YAML: allowed tools, rate limits, confirm-required actions, data residency.
- **No marketplace / multi-agent swarm** until P2 jobs are trusted.
- Optimize for **xAI Grok models** and **X platform** workflows (read/search first; post only with confirm).

## Memory model (critical)

Four layers:
1. **Working** — current session turns + tool results
2. **Episodic** — session summaries
3. **Semantic facts** — content, source, confidence, scope, retention_days, write permission
4. **Procedural preferences** — “how user likes X done”, distilled from feedback

APIs: write, query, consent, feedback, distill. Silent use in replies (never say “I checked the DB”).

Learning loop: explicit feedback → confidence update → scheduled distill job.

## Autonomy / automation (inside the agent, not n8n-first)

- Postgres `jobs` table: scheduled + on-demand
- States: queued | running | needs_confirmation | done | failed
- Worker process on same host/VPS
- Skills as registered tools with JSON schemas
- Optional later: n8n/Windmill/Activepieces as **adapters** only

## Tools to implement (ranked)

P0: memory.*, web_search, web_fetch, datetime/schedule_job  
P1: github_list_issues, github_list_prs, github_search_code (read-only first)  
P2: x_search / x_read (API), job_daily_digest  
P3: github_create_issue / draft_pr (confirm), x_post (confirm), generic HTTP webhook  
P4: Buzz channel read/post if Agent Client Protocol available  
Never: unconstrained computer-use without spoken/button confirm

## Voice session loop

start_session → partial transcripts → process_turn (memory + tools) → speak response → end_session  
Replies: short, calm, concrete, **one next action** when useful.  
Presence states optional for API clients: listening | thinking | speaking | idle | proactive.

## HTTP API (so Aether / mobile / Buzz can attach later)

- `GET /health`
- `POST /voice/start|turn|partial|end`
- `POST /memory/*` `GET /memory/stats`
- `POST /jobs` `GET /jobs` `POST /jobs/:id/confirm`
- `POST /tools/:name`
- Bind `0.0.0.0` only behind firewall/VPS rules when remote

## Deploy target

User has **Hostinger KVM 2** VPS (already runs a Hermes agent with headroom). Prefer:
- Docker Compose: partner API + worker + Postgres
- systemd or compose restart policies
- Secrets via env file, never in git

## What makes this more than an ordinary agent

1. **Durable multi-layer memory + distill** (not chat-log only)
2. **Background jobs that write back into memory**
3. **Tool confirmations + audit log** (operator trust)
4. **X/xAI-native** — Grok models, X search/post patterns, Voice Realtime
5. **Multi-surface** — same brain for voice, HTTP, future Aether/Buzz
6. **Cost + token accounting** per job/session
7. **Constitution** as code, not prompt-only safety
8. **Preference learning** that changes behavior next week, not just next turn

## Deliverables

- Runnable Docker Compose on VPS
- README: env vars, Grok Voice key setup, first voice test, job test
- STATUS.md: what works / doesn’t
- Acceptance: 5-turn voice session with memory recall next day; one scheduled job completes offline; GitHub read tool works with token

## Out of scope v1

Aether UI, Electron, full mobile app, Supabase, agent marketplace, swarm orchestration.

Work in vertical slices. Every slice must leave the partner more usable by voice.
