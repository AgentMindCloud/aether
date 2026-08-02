"""Aether Voice — Grok Voice Think Fast 2.0 + Realtime-oriented path.

Offline-first simulation with structure ready for live WebSocket / Realtime API
when GROK_VOICE_API_KEY is present. Supports partial transcripts and presence
state machine aligned with .grok/voice.yaml latency budgets.

Build 0.1: replies are short, calm, concrete, and propose one next action.
Memory facts are used silently when relevant. TTS-ready text only.
"""

from __future__ import annotations

import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class VoiceSession:
    session_id: str
    user_id: str
    mode: str = "reactive"
    started_at: str = field(default_factory=_now)
    status: str = "active"  # active | idle | ended | fallback_text | streaming
    presence: dict[str, Any] = field(default_factory=lambda: {
        "expression": "neutral", "status": "idle", "intensity": 0.5
    })
    turns: int = 0
    last_activity: str = field(default_factory=_now)
    partial_transcript: str = ""


class VoiceClient:
    """Client for Grok Voice Think Fast 2.0 / Realtime.

    Live mode prepares the call shape for streaming endpoints.
    Offline mode still drives presence and short voice-appropriate replies.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GROK_VOICE_API_KEY", "")
        self.live = bool(
            self.api_key
            and not self.api_key.startswith("your_")
            and not self.api_key.endswith("_here")
        )
        self.sessions: dict[str, VoiceSession] = {}
        self.engine = "grok-voice-think-fast-2.0"
        self.realtime_ready = True  # structure present for WS upgrade

    def start_session(self, user_id: str, mode: str = "reactive") -> dict[str, Any]:
        sid = f"vs-{uuid.uuid4().hex[:10]}"
        sess = VoiceSession(session_id=sid, user_id=user_id, mode=mode)
        sess.presence = {"expression": "attentive", "status": "listening", "intensity": 0.75}
        sess.status = "streaming" if self.live else "active"
        self.sessions[sid] = sess

        return {
            "status": "session_started",
            "session_id": sid,
            "user_id": user_id,
            "mode": mode,
            "engine": self.engine,
            "live": self.live,
            "realtime_ready": self.realtime_ready,
            "presence": sess.presence,
            "started_at": sess.started_at,
            "greeting": "Listening. Speak or type when ready.",
            "note": (
                "Live path — connect Realtime / WS endpoint with key"
                if self.live
                else "Offline simulation (set GROK_VOICE_API_KEY for live)"
            ),
        }

    def partial(self, session_id: str, text: str) -> dict[str, Any]:
        """Ingest partial STT transcript (for barge-in / live UI)."""
        sess = self.sessions.get(session_id)
        if not sess or sess.status == "ended":
            return {"error": "No active session"}
        sess.partial_transcript = text
        sess.presence = {"expression": "attentive", "status": "listening", "intensity": 0.8}
        sess.last_activity = _now()
        return {
            "session_id": session_id,
            "partial": text[:200],
            "presence": sess.presence,
            "timestamp": _now(),
        }

    def process_turn(
        self,
        session_id: str,
        transcript: str,
        x_context: list[dict] | None = None,
        memory_facts: list[dict] | None = None,
    ) -> dict[str, Any]:
        sess = self.sessions.get(session_id)
        if not sess or sess.status == "ended":
            return {"error": "No active voice session", "session_id": session_id}

        sess.turns += 1
        sess.last_activity = _now()
        sess.partial_transcript = ""
        sess.presence = {"expression": "thoughtful", "status": "thinking", "intensity": 0.65}

        t0 = time.perf_counter()
        response = self._compose_response(transcript, memory_facts, x_context)
        sess.presence = {"expression": "attentive", "status": "speaking", "intensity": 0.85}
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        result = {
            "session_id": session_id,
            "turn": sess.turns,
            "received": transcript[:160],
            "response": response,
            "presence": sess.presence,
            "live": self.live,
            "realtime_ready": self.realtime_ready,
            "engine": self.engine,
            "latency_ms": elapsed_ms,
            "x_context_items": len(x_context or []),
            "memory_used": len(memory_facts or []),
            "timestamp": _now(),
            "tts_ready": True,
        }
        if self.live:
            result["note"] = "Stream-ready — wire to Grok Voice Realtime / Think Fast 2.0 endpoint"
        else:
            result["note"] = "Offline simulation — response ready for TTS"
        return result

    def end_session(self, session_id: str) -> dict[str, Any]:
        sess = self.sessions.get(session_id)
        if not sess:
            return {"error": "Session not found"}
        sess.status = "ended"
        sess.presence = {"expression": "calm", "status": "idle", "intensity": 0.4}
        return {
            "status": "ended",
            "session_id": session_id,
            "turns": sess.turns,
            "presence": sess.presence,
            "timestamp": _now(),
        }

    def get_presence(self, session_id: str) -> dict[str, Any]:
        sess = self.sessions.get(session_id)
        if not sess:
            return {"expression": "neutral", "status": "idle", "intensity": 0.5}
        return sess.presence

    def _extract_fact_snippets(self, memory_facts: list[dict] | None, limit: int = 2) -> list[str]:
        if not memory_facts:
            return []
        snippets: list[str] = []
        for f in memory_facts[:6]:
            content = (
                f.get("content")
                or f.get("text")
                or f.get("fact")
                or f.get("value")
                or ""
            )
            content = str(content).strip()
            if not content:
                continue
            lower = content.lower()
            if any(k in lower for k in ("prefer", "short", "calm", "concrete", "next action", "style")):
                snippets.insert(0, content[:120])
            else:
                snippets.append(content[:120])
            if len(snippets) >= limit:
                break
        return snippets[:limit]

    def _compose_response(
        self,
        transcript: str,
        memory_facts: list[dict] | None,
        x_context: list[dict] | None,
    ) -> str:
        """Short, calm, concrete replies. Max ~35 words. One next action when useful."""
        t = (transcript or "").strip()
        tl = t.lower()
        facts = self._extract_fact_snippets(memory_facts)

        def reply(text: str) -> str:
            words = text.split()
            if len(words) > 38:
                text = " ".join(words[:36]).rstrip(",.;:") + "."
            return text

        if re.search(r"\b(hi|hello|hey|good morning|good evening)\b", tl) or tl in ("yo", "sup"):
            if facts:
                return reply("Here. I have prior context. What do you want to move first?")
            return reply("Here. Ready when you are. What is the highest-leverage next move?")

        if any(w in tl for w in ("remember", "preference", "my style", "how i like")):
            if facts:
                snippet = facts[0]
                return reply(f"Noted earlier: {snippet[:80]}. I will keep replies short and concrete.")
            return reply("I can store a preference. Tell me the style you want — short, calm, one next action.")

        if any(w in tl for w in ("plan", "next", "priority", "what should", "do next", "focus")):
            return reply("Put the single highest-leverage item in Priority, then execute it in the next 25 minutes.")

        if any(w in tl for w in ("screenshot", "screen", "click", "type", "window", "mouse")):
            return reply("I can request that computer action. I will ask for spoken confirmation before executing.")

        if any(w in tl for w in ("thread", "post", "idea", "hook", "tweet", "content")):
            return reply("I can draft three hooks. Say the topic and the audience in one sentence.")

        if any(w in tl for w in ("github", "issue", "pr", "pull request", "repo")):
            return reply("I can list issues or open PRs on AgentMindCloud/aether. Which one do you need?")

        if any(w in tl for w in ("status", "how are you", "working", "online", "ready")):
            mode = "live voice" if self.live else "sim voice with TTS"
            return reply(f"Online. Session active, {mode}. Tell me the next concrete step.")

        if any(w in tl for w in ("help", "what can you", "capabilities")):
            return reply("Talk, capture priorities, request screenshots with confirmation, ideate content, and use governed memory.")

        if any(w in tl for w in ("make it real", "promote", "bookmark")):
            return reply("Open Bookmarks, pick the item, then press Make it real. It lands in Priority.")

        if facts:
            return reply(f"I have that context. {facts[0][:70]}. What is the one action you want right now?")

        if x_context:
            return reply("Live context is available. Point me at the strongest signal and I will act on it.")

        if len(t) < 12:
            return reply("Got it. Give me a bit more detail or name the next action.")

        return reply("Understood. I am with you. Name the single next action and I will help execute it.")


voice_client = VoiceClient()
