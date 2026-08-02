"""Aether Proactive engine — P3.

Evaluates triggers from .grok/proactive.yaml style config.
Offline-safe: can be fed signals from X or local events.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
import uuid


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProactiveEngine:
    def __init__(self) -> None:
        self.enabled = True
        self.max_per_day = 3
        self.cooldown_minutes = 120
        self.require_opt_in = True
        self.opted_in = False
        self._initiations: list[datetime] = []
        self._last_initiation: datetime | None = None

    def set_opt_in(self, value: bool) -> dict[str, Any]:
        self.opted_in = bool(value)
        return {"opted_in": self.opted_in, "require_opt_in": self.require_opt_in}

    def _can_initiate(self) -> tuple[bool, str]:
        if not self.enabled:
            return False, "proactive disabled"
        if self.require_opt_in and not self.opted_in:
            return False, "user has not opted in"
        now = _now()
        day_ago = now - timedelta(days=1)
        recent = [t for t in self._initiations if t > day_ago]
        self._initiations = recent
        if len(recent) >= self.max_per_day:
            return False, "daily proactive limit reached"
        if self._last_initiation and (now - self._last_initiation) < timedelta(minutes=self.cooldown_minutes):
            return False, "cooldown active"
        return True, "ok"

    def evaluate(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        """Evaluate current signals and optionally offer a proactive session."""
        signals = signals or {}
        can, reason = self._can_initiate()
        offers: list[dict[str, Any]] = []

        mention_spike = int(signals.get("mention_count_15m", 0))
        if mention_spike >= 5:
            offers.append({
                "type": "mention_spike",
                "reason": f"Mention spike detected ({mention_spike} in 15m)",
                "action": "offer_voice_session",
                "announce": f"I noticed a spike in mentions — want to talk about it?",
            })

        high_eng = int(signals.get("high_engagement_opportunities", 0))
        if high_eng >= 1:
            offers.append({
                "type": "high_engagement_reply_opportunity",
                "reason": "High-engagement reply opportunity available",
                "action": "offer_voice_session",
                "announce": "There is a high-signal reply opportunity right now. Want to jump in?",
            })

        if signals.get("scheduled_morning"):
            offers.append({
                "type": "user_scheduled",
                "reason": "Morning briefing window",
                "action": "morning_briefing_voice",
                "announce": "Morning briefing is ready when you are.",
            })

        if not can:
            return {
                "can_initiate": False,
                "reason": reason,
                "offers": [],
                "signals": signals,
            }

        if offers:
            self._last_initiation = _now()
            self._initiations.append(self._last_initiation)

        return {
            "can_initiate": can,
            "reason": reason,
            "offers": offers,
            "signals": signals,
            "id": f"pro-{uuid.uuid4().hex[:8]}",
            "timestamp": _now().isoformat(),
        }

    def status(self) -> dict[str, Any]:
        can, reason = self._can_initiate()
        return {
            "enabled": self.enabled,
            "opted_in": self.opted_in,
            "can_initiate": can,
            "reason": reason,
            "max_per_day": self.max_per_day,
            "cooldown_minutes": self.cooldown_minutes,
            "initiations_today": len(self._initiations),
        }


proactive_engine = ProactiveEngine()
