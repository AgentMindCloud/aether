"""Aether runtime entry points.

Compatible with xlOS / grok-install python_module dispatch.
Provides a full local --demo mode that exercises the presence swarm,
governed memory contracts, presence updates, and kill switch without
requiring live API keys or voice endpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any


def check_kill_switch() -> None:
    """Halt immediately if the kill switch is engaged."""
    if os.getenv("AETHER_DISABLED") == "1":
        raise RuntimeError(
            "Aether kill switch engaged (AETHER_DISABLED=1). "
            "All voice and text activity halted."
        )


def validate_env(required: list[str] | None = None) -> dict[str, str]:
    """Validate required environment variables. Returns found values."""
    required = required or [
        "XAI_API_KEY",
        "X_BEARER_TOKEN",
        "GROK_VOICE_API_KEY",
    ]
    missing = []
    found: dict[str, str] = {}
    for key in required:
        val = os.getenv(key)
        if not val or val.startswith("your_") or val.endswith("_here"):
            missing.append(key)
        else:
            found[key] = val[:8] + "…" if len(val) > 12 else val
    if missing:
        msg = (
            "Missing or placeholder environment variables:\n"
            + "\n".join(f"  - {k}" for k in missing)
            + "\n\nCopy .env.example → .env and fill real values.\n"
            "Get keys from:\n"
            "  XAI_API_KEY        → https://console.x.ai\n"
            "  X_BEARER_TOKEN     → https://developer.x.com\n"
            "  GROK_VOICE_API_KEY → Grok / xAI voice access\n"
        )
        raise EnvironmentError(msg)
    return found


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sample_memory_contracts(query: str) -> list[dict[str, Any]]:
    """Return sample governed memory contracts for demo mode."""
    samples = [
        {
            "content": "User prefers short, calm voice answers under 35 words.",
            "source": "user_said",
            "confidence": 0.92,
            "scope": "user",
            "retention_days": 90,
            "write_permission": "user_only",
            "created_at": "2026-07-28T09:14:00Z",
            "last_accessed": _now_iso(),
        },
        {
            "content": "Recent high-signal topic: multi-agent safety patterns and presence agents.",
            "source": "x_context",
            "confidence": 0.81,
            "scope": "session",
            "retention_days": 0,
            "write_permission": "agent",
            "created_at": _now_iso(),
            "last_accessed": _now_iso(),
        },
        {
            "content": "User is building Aether — desktop presence OS with governed memory.",
            "source": "derived",
            "confidence": 0.88,
            "scope": "user",
            "retention_days": 30,
            "write_permission": "agent",
            "created_at": _now_iso(),
            "last_accessed": _now_iso(),
        },
    ]
    q = query.lower()
    if "memory" in q or "remember" in q or "prefer" in q:
        return samples[:1]
    if "x" in q or "mention" in q or "topic" in q or "aether" in q:
        return samples[1:]
    return samples[:2]


def start_voice_session(user_id: str, mode: str = "reactive") -> dict[str, Any]:
    """Start a new voice session (reactive or proactive)."""
    check_kill_switch()
    return {
        "status": "session_started",
        "user_id": user_id,
        "mode": mode,
        "swarm": "aether-presence-swarm",
        "memory": "governed-contracts",
        "presence": "enabled",
        "started_at": _now_iso(),
    }


def handle_turn(
    session_id: str,
    transcript: str,
    x_context: list[dict] | None = None,
) -> dict[str, Any]:
    """Process one voice turn with optional live X context."""
    check_kill_switch()

    memories = _sample_memory_contracts(transcript)

    # Coordinator response (simulated, respects 35-word constraint)
    if memories:
        response = (
            "Got it. I kept the context from earlier and stayed under the voice limit."
        )
    else:
        response = "Understood. Ready when you are."

    presence = {
        "expression": "attentive",
        "status": "speaking",
        "intensity": 0.75,
    }

    return {
        "session_id": session_id,
        "received": transcript[:120],
        "x_context_items": len(x_context or []),
        "memory_contracts": memories,
        "coordinator_response": response,
        "presence": presence,
        "action": "coordinator_delegates",
        "next": "tts_playback + optional avatar update",
        "timestamp": _now_iso(),
    }


def update_presence(
    expression: str, status: str, intensity: float = 0.7
) -> dict[str, Any]:
    """Update the reactive visual presence."""
    check_kill_switch()
    valid_expr = {"calm", "attentive", "thoughtful", "pleased", "concerned", "neutral"}
    valid_status = {"listening", "thinking", "speaking", "idle", "proactive"}
    if expression not in valid_expr:
        expression = "neutral"
    if status not in valid_status:
        status = "idle"
    intensity = max(0.0, min(1.0, intensity))
    return {
        "expression": expression,
        "status": status,
        "intensity": intensity,
        "avatar": "updated",
        "timestamp": _now_iso(),
    }


def run_demo() -> None:
    """Fully offline demonstration of the Aether presence loop."""
    print("\n════════════════════════════════════════════════════════════")
    print("  AETHER  ·  local demo mode  ·  no API keys required")
    print("════════════════════════════════════════════════════════════\n")

    # 1. Kill switch check
    print("→ Checking kill switch …")
    try:
        check_kill_switch()
        print("  ✓ Kill switch clear (AETHER_DISABLED not set to 1)\n")
    except RuntimeError as e:
        print(f"  ✗ {e}")
        sys.exit(1)

    # 2. Start session
    print("→ Starting voice session (reactive) …")
    session = start_voice_session(user_id="demo-user-001", mode="reactive")
    print(json.dumps(session, indent=2))
    print()

    # 3. Simulated turn with memory + presence
    print("→ Handling turn (transcript + simulated X context) …")
    time.sleep(0.35)
    turn = handle_turn(
        session_id="sess-demo-001",
        transcript="Can you remember that I like short calm answers and also what people are saying about presence agents and multi-agent safety?",
        x_context=[{"id": "123", "text": "presence agents and multi-agent safety patterns trending"}],
    )
    print(json.dumps(turn, indent=2))
    print()

    # 4. Presence update
    print("→ Updating visual presence …")
    presence = update_presence("thoughtful", "thinking", 0.65)
    print(json.dumps(presence, indent=2))
    print()

    # 5. Proactive policy note
    print("→ Proactive policy (from .grok/proactive.yaml)")
    print("  Triggers: mention_spike (≥5 in 15m), high engagement, scheduled")
    print("  Policy: max 3/day, require opt-in, 120m cooldown, announce reason")
    print()

    # 6. Memory contract explanation
    print("→ Governed memory contracts in action")
    print("  Every fact carries: content, source, confidence, scope,")
    print("  retention_days, write_permission, timestamps.")
    print("  Cross-session memory is OFF by default and requires consent.\n")

    # 7. Computer-use safety note
    print("→ Computer-use safety (from .grok/safety.yaml + tools.yaml)")
    print("  Any mutating action requires spoken confirmation before execution.")
    print("  Never executes without explicit user approval.\n")

    print("════════════════════════════════════════════════════════════")
    print("  Demo complete. Core P0 presence loop exercised end-to-end.")
    print("  For live voice: set keys in .env and use grok-install / xlOS.")
    print("  Shell: cd shell && npm install && npm start")
    print("════════════════════════════════════════════════════════════\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aether",
        description="Aether — desktop presence operating surface for high-agency builders",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run fully offline demonstration of swarm + memory + presence",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Validate required environment variables and exit",
    )
    parser.add_argument(
        "--session",
        metavar="USER_ID",
        help="Start a session for the given user_id (requires live env)",
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    if args.check_env:
        try:
            found = validate_env()
            print("Environment OK:")
            for k, v in found.items():
                print(f"  {k}: {v}")
        except EnvironmentError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return

    if args.session:
        try:
            validate_env()
            result = start_voice_session(args.session)
            print(json.dumps(result, indent=2))
        except (EnvironmentError, RuntimeError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return

    # Default: show help + quick tip
    parser.print_help()
    print("\nQuick start:")
    print("  python -m aether.runtime --demo")
    print("  # or after pip install -e .")
    print("  aether --demo")


if __name__ == "__main__":
    main()
