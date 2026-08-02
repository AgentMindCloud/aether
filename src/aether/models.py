"""LLM abstraction — config-driven model selection (P4).

Swap Grok versions via config /env /switch-model without code changes.
"""

from __future__ import annotations

import os
from typing import Any

# In-memory current selection (process lifetime)
_CURRENT_MODEL = os.getenv("AETHER_MODEL", "grok-4.20-multi-agent")
_FALLBACK = ["grok-4.20-multi-agent", "grok-4.6"]


def get_model() -> str:
    return _CURRENT_MODEL


def switch_model(model_id: str) -> dict[str, Any]:
    global _CURRENT_MODEL
    previous = _CURRENT_MODEL
    _CURRENT_MODEL = model_id.strip() or previous
    return {
        "status": "switched",
        "previous": previous,
        "current": _CURRENT_MODEL,
        "note": "Hot-swap applied for this runtime process. Persist via AETHER_MODEL env or .grok/models.yaml default.",
    }


def model_status() -> dict[str, Any]:
    return {
        "current": _CURRENT_MODEL,
        "fallback_chain": list(_FALLBACK),
        "voice_engine": "grok-voice-think-fast-2.0",
        "env_override": os.getenv("AETHER_MODEL"),
        "xai_key_present": bool(
            os.getenv("XAI_API_KEY")
            and not os.getenv("XAI_API_KEY", "").startswith("your_")
        ),
    }
