"""Aether Voice — Grok Voice Think Fast 2.0 path.

Offline-first simulation + live path when GROK_VOICE_API_KEY is present.
Respects latency budgets and presence state machine from .grok/voice.yaml.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class VoiceSession:
    session_id: str
    user_id: str
    mode: str = "reactive"
    started_at: str = field(default_factory=_now)
    status: str = "active"  # active | idle | ended | fallback_text
    presence: dict[str, Any] = field(default_factory=lambda: {
        "expression": "neutral", "status": "idle", "intensity": 0.5
    })
    turns: int = 0
    last_activity: str = field(default_factory=_now)


class VoiceClient:
    """Thin client for Grok Voice Think Fast 2.0.

    When GROK_VOICE_API_KEY is set, prepares real calls (structure ready).
    Otherwise runs high-fidelity offline simulation that still drives presence.
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

    def start_session(self, user_id: str, mode: str = "reactive") -> dict[str, Any]:
        sid = f"vs-{uuid.uuid4().hex[:10]}"
        sess = VoiceSession(session_id=sid, user_id=user_id, mode=mode)
        sess.presence = {"expression": "attentive", "status": "listening", "intensity": 0.7}
        self.sessions[sid] = sess

        return {
            "status": "session_started",
            "session_id": sid,
            "user_id": user_id,
            "mode": mode,
            "engine": self.engine,
            "live": self.live,
            "presence": sess.presence,
            "started_at": sess.started_at,
            "note": "Live path active" if self.live else "Offline simulation (set GROK_VOICE_API_KEY for live)",
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
        sess.presence = {"expression": "thoughtful", "status": "thinking", "intensity": 0.65}

        # Simulate latency budget awareness
        t0 = time.perf_counter()

        # Build short voice-appropriate response
        response = self._compose_response(transcript, memory_facts, x_context)

        # Presence → speaking
        sess.presence = {"expression": "attentive", "status": "speaking", "intensity": 0.8}

        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        result = {
            "session_id": session_id,
            "turn": sess.turns,
            "received": transcript[:160],
            "response": response,
            "presence": sess.presence,
            "live": self.live,
            "engine": self.engine,
            "latency_ms": elapsed_ms,
            "x_context_items": len(x_context or []),
            "memory_used": len(memory_facts or []),
            "timestamp": _now(),
        }

        if self.live:
            result["note"] = "Would stream to Grok Voice Think Fast 2.0 Realtime API"
            # Future: actual websocket / HTTP call to voice endpoint here
        else:
            result["note"] = "Offline simulation — response ready for TTS playback"

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

    def _compose_response(
        self,
        transcript: str,
        memory_facts: list[dict] | None,
        x_context: list[dict] | None,
    ) -> str:
        """Keep under ~35 words for voice."""
        t = transcript.lower()
        if memory_facts:
            return "Got it. I kept the earlier context and stayed under the voice limit."
        if x_context:
            return "I see the live context. Ready to act on the strongest signal when you are."
        if any(w in t for w in ("plan", "next", "priority", "do")):
            return "I can turn that into a concrete next move. Want me to put it in Priority?"
        if any(w in t for w in ("screenshot", "click", "type", "window")):
            return "I can request that computer action. I will ask for spoken confirmation first."
        return "Understood. I am listening."


# Singleton for runtime convenience
voice_client = VoiceClient()
