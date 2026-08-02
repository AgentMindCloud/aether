"""Aether runtime entry points.

Compatible with xlOS / grok-install python_module dispatch.
P0: offline --demo of presence loop.
P1: first-use magic, computer-use stubs + spoken confirmation,
     Action Plan / Make it real, local IPC server for shell bridge.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse, parse_qs

# ---------------------------------------------------------------------------
# Core utilities
# ---------------------------------------------------------------------------

def check_kill_switch() -> None:
    if os.getenv("AETHER_DISABLED") == "1":
        raise RuntimeError(
            "Aether kill switch engaged (AETHER_DISABLED=1). "
            "All voice and text activity halted."
        )


def validate_env(required: list[str] | None = None) -> dict[str, str]:
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


# ---------------------------------------------------------------------------
# In-memory stores (P1 — later replaced by encrypted governed store)
# ---------------------------------------------------------------------------

_PRIORITY: list[dict[str, Any]] = [
    {
        "id": "p1",
        "title": "Wire live Grok Voice Think Fast 2.0 path",
        "meta": "High impact · This week",
        "level": "high",
        "source": "system",
        "created_at": _now_iso(),
    },
    {
        "id": "p2",
        "title": "Complete typed IPC bridge + first-use magic",
        "meta": "Architecture · Today",
        "level": "high",
        "source": "system",
        "created_at": _now_iso(),
    },
]

_BOOKMARKS: list[dict[str, Any]] = [
    {
        "id": "b1",
        "category": "Immediate",
        "title": "Grok Voice Think Fast 2.0 now live — integrate Realtime path",
        "source": "x.ai / xAI",
        "score": 9.4,
        "plan": [
            "Confirm API endpoint + auth for Think Fast 2.0",
            "Add voice session start + partial transcript handling in runtime",
            "Push presence updates (listening → thinking → speaking) over IPC",
            "Add graceful fallback to text when STT confidence < floor",
        ],
    },
    {
        "id": "b2",
        "category": "Act soon",
        "title": "Computer-use tools with spoken confirmation gates",
        "source": "Aether design",
        "score": 8.7,
        "plan": [
            "Expose screenshot / window list / type / click surfaces from shell",
            "Require spoken confirmation before any mutating action",
            "Log every computer-use request + confirmation in audit",
            "Surface confirmation prompt in panel + voice",
        ],
    },
    {
        "id": "b3",
        "category": "Possibility",
        "title": "First-use magic: analyze recent activity + 3 next moves",
        "source": "Aether design",
        "score": 8.1,
        "plan": [
            "On first session detect empty memory / first-run flag",
            "Offer 3 concrete next moves without requiring heavy setup",
            "Push accepted move into Priority list via Make it real",
        ],
    },
]

_PENDING_COMPUTER_USE: dict[str, Any] | None = None
_FIRST_USE_DONE = False


# ---------------------------------------------------------------------------
# Memory contracts (demo)
# ---------------------------------------------------------------------------

def _sample_memory_contracts(query: str) -> list[dict[str, Any]]:
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


# ---------------------------------------------------------------------------
# Session + Turn + Presence
# ---------------------------------------------------------------------------

def start_voice_session(user_id: str, mode: str = "reactive") -> dict[str, Any]:
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
    check_kill_switch()
    memories = _sample_memory_contracts(transcript)

    response = (
        "Got it. I kept the context from earlier and stayed under the voice limit."
        if memories
        else "Understood. Ready when you are."
    )

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


# ---------------------------------------------------------------------------
# P1: First-use magic
# ---------------------------------------------------------------------------

def first_use_magic(user_id: str = "local") -> dict[str, Any]:
    """On first interaction offer immediate value without heavy setup."""
    global _FIRST_USE_DONE
    check_kill_switch()

    moves = [
        {
            "id": "m1",
            "title": "Connect live Grok Voice Think Fast 2.0",
            "why": "Unlock real-time voice presence with emotion + barge-in",
            "effort": "low",
            "impact": "high",
        },
        {
            "id": "m2",
            "title": "Run computer-use confirmation flow once",
            "why": "Verify spoken safety gates before any mutating tools",
            "effort": "low",
            "impact": "high",
        },
        {
            "id": "m3",
            "title": "Promote one high-score bookmark into Priority",
            "why": "Exercise the Make it real → Action Plan loop",
            "effort": "low",
            "impact": "medium",
        },
    ]

    _FIRST_USE_DONE = True
    return {
        "type": "first_use_magic",
        "user_id": user_id,
        "message": "Welcome. I looked at the current state of Aether. Here are 3 concrete next moves.",
        "moves": moves,
        "presence": {"expression": "pleased", "status": "speaking", "intensity": 0.8},
        "timestamp": _now_iso(),
    }


# ---------------------------------------------------------------------------
# P1: Computer-use stubs with spoken confirmation gates
# ---------------------------------------------------------------------------

def computer_use_request(action: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Request a computer-use action. Never executes — only stages for confirmation."""
    global _PENDING_COMPUTER_USE
    check_kill_switch()

    allowed = {"screenshot", "list_windows", "focus_window", "type_text", "click", "move_mouse"}
    if action not in allowed:
        return {"error": f"Unknown action: {action}", "allowed": list(allowed)}

    request_id = str(uuid.uuid4())[:8]
    _PENDING_COMPUTER_USE = {
        "request_id": request_id,
        "action": action,
        "details": details or {},
        "status": "awaiting_spoken_confirmation",
        "created_at": _now_iso(),
        "expires_in_seconds": 20,
    }

    return {
        "status": "awaiting_spoken_confirmation",
        "request_id": request_id,
        "action": action,
        "message": f"I need spoken confirmation before I {action}. Say yes or confirm within 20 seconds.",
        "safety": {
            "require_spoken_confirmation": True,
            "never_execute_without_confirm": True,
        },
        "timestamp": _now_iso(),
    }


def computer_use_confirm(request_id: str, spoken_yes: bool = True) -> dict[str, Any]:
    """Confirm or reject a staged computer-use action."""
    global _PENDING_COMPUTER_USE
    check_kill_switch()

    if not _PENDING_COMPUTER_USE or _PENDING_COMPUTER_USE["request_id"] != request_id:
        return {"error": "No matching pending computer-use request", "request_id": request_id}

    pending = _PENDING_COMPUTER_USE
    _PENDING_COMPUTER_USE = None

    if not spoken_yes:
        return {
            "status": "cancelled",
            "request_id": request_id,
            "action": pending["action"],
            "message": "Computer-use action cancelled. No changes made.",
            "timestamp": _now_iso(),
        }

    # Simulated execution (P1 stub)
    return {
        "status": "executed_stub",
        "request_id": request_id,
        "action": pending["action"],
        "details": pending["details"],
        "message": f"Executed (stub): {pending['action']}. Full OS surface comes next.",
        "audit": {
            "confirmed_by": "spoken",
            "executed_at": _now_iso(),
        },
        "timestamp": _now_iso(),
    }


# ---------------------------------------------------------------------------
# P1: Action Plan / Make it real
# ---------------------------------------------------------------------------

def list_priority() -> list[dict[str, Any]]:
    return list(_PRIORITY)


def list_bookmarks() -> list[dict[str, Any]]:
    return list(_BOOKMARKS)


def make_it_real(bookmark_id: str) -> dict[str, Any]:
    """Promote a high-signal bookmark into the Priority list."""
    check_kill_switch()
    bm = next((b for b in _BOOKMARKS if b["id"] == bookmark_id), None)
    if not bm:
        return {"error": f"Bookmark {bookmark_id} not found"}

    new_item = {
        "id": f"p-{uuid.uuid4().hex[:6]}",
        "title": bm["title"],
        "meta": f"From Bookmark Intelligence · {bm['category']} · just now",
        "level": "high",
        "source": "make_it_real",
        "plan": bm.get("plan", []),
        "created_at": _now_iso(),
    }
    _PRIORITY.insert(0, new_item)

    return {
        "status": "promoted",
        "priority_item": new_item,
        "message": f"‘{bm['title']}’ is now in Priority as high impact.",
        "presence": {"expression": "pleased", "status": "speaking", "intensity": 0.7},
        "timestamp": _now_iso(),
    }


def add_priority(title: str, level: str = "high") -> dict[str, Any]:
    check_kill_switch()
    item = {
        "id": f"p-{uuid.uuid4().hex[:6]}",
        "title": title,
        "meta": "Just captured · Now",
        "level": level,
        "source": "capture",
        "created_at": _now_iso(),
    }
    _PRIORITY.insert(0, item)
    return {"status": "added", "item": item}


# ---------------------------------------------------------------------------
# Demo + IPC server
# ---------------------------------------------------------------------------

def run_demo() -> None:
    print("\n════════════════════════════════════════════════════════════")
    print("  AETHER  ·  P1 demo  ·  no API keys required")
    print("════════════════════════════════════════════════════════════\n")

    print("→ Checking kill switch …")
    try:
        check_kill_switch()
        print("  ✓ Kill switch clear\n")
    except RuntimeError as e:
        print(f"  ✗ {e}")
        sys.exit(1)

    print("→ Starting voice session …")
    session = start_voice_session("demo-user-001")
    print(json.dumps(session, indent=2), "\n")

    print("→ First-use magic …")
    magic = first_use_magic()
    print(json.dumps(magic, indent=2), "\n")

    print("→ Handling turn with memory + presence …")
    time.sleep(0.25)
    turn = handle_turn(
        "sess-demo-001",
        "Remember I like short calm answers. What’s happening with presence agents?",
        [{"id": "123", "text": "presence agents trending"}],
    )
    print(json.dumps(turn, indent=2), "\n")

    print("→ Computer-use request (screenshot) — requires spoken confirmation …")
    req = computer_use_request("screenshot", {"reason": "demo"})
    print(json.dumps(req, indent=2), "\n")

    print("→ Confirming computer-use with spoken yes …")
    conf = computer_use_confirm(req["request_id"], spoken_yes=True)
    print(json.dumps(conf, indent=2), "\n")

    print("→ Make it real (promote high-score bookmark) …")
    real = make_it_real("b1")
    print(json.dumps(real, indent=2), "\n")

    print("→ Current Priority list …")
    print(json.dumps(list_priority(), indent=2), "\n")

    print("→ Presence update …")
    print(json.dumps(update_presence("thoughtful", "thinking", 0.65), indent=2), "\n")

    print("════════════════════════════════════════════════════════════")
    print("  P1 demo complete.")
    print("  Features exercised: first-use · computer-use gates · Make it real")
    print("  IPC: aether --serve   then point shell at http://127.0.0.1:7420")
    print("════════════════════════════════════════════════════════════\n")


class AetherHandler(BaseHTTPRequestHandler):
    """Minimal JSON IPC server for shell ↔ runtime."""

    def _json_response(self, code: int, payload: Any) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            check_kill_switch()
            if path == "/health":
                self._json_response(200, {"status": "ok", "version": "0.1.0", "p": "P1"})
            elif path == "/priority":
                self._json_response(200, {"items": list_priority()})
            elif path == "/bookmarks":
                self._json_response(200, {"items": list_bookmarks()})
            elif path == "/presence":
                self._json_response(200, update_presence("neutral", "idle", 0.5))
            elif path == "/first-use":
                self._json_response(200, first_use_magic())
            else:
                self._json_response(404, {"error": "not found"})
        except RuntimeError as e:
            self._json_response(503, {"error": str(e)})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json_response(400, {"error": "invalid json"})
            return

        try:
            check_kill_switch()
            if path == "/session/start":
                result = start_voice_session(data.get("user_id", "local"), data.get("mode", "reactive"))
                self._json_response(200, result)
            elif path == "/turn":
                result = handle_turn(
                    data.get("session_id", "sess"),
                    data.get("transcript", ""),
                    data.get("x_context"),
                )
                self._json_response(200, result)
            elif path == "/presence":
                result = update_presence(
                    data.get("expression", "neutral"),
                    data.get("status", "idle"),
                    float(data.get("intensity", 0.7)),
                )
                self._json_response(200, result)
            elif path == "/computer-use/request":
                result = computer_use_request(data.get("action", "screenshot"), data.get("details"))
                self._json_response(200, result)
            elif path == "/computer-use/confirm":
                result = computer_use_confirm(
                    data.get("request_id", ""),
                    bool(data.get("spoken_yes", True)),
                )
                self._json_response(200, result)
            elif path == "/make-it-real":
                result = make_it_real(data.get("bookmark_id", ""))
                self._json_response(200, result)
            elif path == "/priority/add":
                result = add_priority(data.get("title", "Untitled"), data.get("level", "high"))
                self._json_response(200, result)
            else:
                self._json_response(404, {"error": "not found"})
        except RuntimeError as e:
            self._json_response(503, {"error": str(e)})

    def log_message(self, format: str, *args: Any) -> None:
        # quieter
        pass


def run_serve(host: str = "127.0.0.1", port: int = 7420) -> None:
    check_kill_switch()
    server = HTTPServer((host, port), AetherHandler)
    print(f"Aether IPC server listening on http://{host}:{port}")
    print("Endpoints: /health /priority /bookmarks /first-use /session/start /turn /presence")
    print("           /computer-use/request /computer-use/confirm /make-it-real /priority/add")
    print("Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aether",
        description="Aether — desktop presence operating surface for high-agency builders",
    )
    parser.add_argument("--demo", action="store_true", help="Run full P1 offline demo")
    parser.add_argument("--check-env", action="store_true", help="Validate environment variables")
    parser.add_argument("--session", metavar="USER_ID", help="Start a session (requires live env)")
    parser.add_argument("--serve", action="store_true", help="Start local IPC server for shell")
    parser.add_argument("--port", type=int, default=7420, help="IPC server port (default 7420)")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    if args.serve:
        run_serve(port=args.port)
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

    parser.print_help()
    print("\nQuick start:")
    print("  aether --demo")
    print("  aether --serve          # IPC for shell on :7420")
    print("  cd shell && npm start")


if __name__ == "__main__":
    main()
