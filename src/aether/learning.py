"""Aether learning loop — feedback + distillation (P5).

Makes the agent improve over years of use without external cloud brain.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aether.memory import memory_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_feedback(fact_id: str, useful: bool, note: str = "") -> dict[str, Any]:
    result = memory_store.feedback(fact_id, useful, note)
    result["timestamp"] = _now()
    return result


def distill(max_facts: int = 5, min_confidence: float = 0.7) -> dict[str, Any]:
    """Promote high-signal session facts → user scope (requires consent)."""
    result = memory_store.distill_session_to_user(max_facts=max_facts, min_confidence=min_confidence)
    result["timestamp"] = _now()
    return result


def learning_status() -> dict[str, Any]:
    stats = memory_store.stats()
    return {
        "backend": stats.get("backend"),
        "session_facts": stats.get("session_facts"),
        "user_facts": stats.get("user_facts"),
        "cross_session_consent": stats.get("cross_session_consent"),
        "can_distill": bool(stats.get("cross_session_consent")),
        "note": "Feedback adjusts confidence; distill promotes session → user with consent.",
    }
