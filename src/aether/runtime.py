"""Aether runtime — P0 → P3.

P3 adds: encrypted memory, proactive engine, voice partials / realtime structure,
richer IPC, packaging readiness.
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
from urllib.parse import urlparse

from aether.voice import voice_client
from aether.memory import memory_store
from aether.proactive import proactive_engine
from aether import content as content_tools

VERSION = "0.3.0"


def check_kill_switch() -> None:
    if os.getenv("AETHER_DISABLED") == "1":
        raise RuntimeError(
            "Aether kill switch engaged (AETHER_DISABLED=1). "
            "All voice and text activity halted."
        )


def validate_env(required: list[str] | None = None) -> dict[str, str]:
    required = required or ["XAI_API_KEY", "X_BEARER_TOKEN", "GROK_VOICE_API_KEY"]
    missing, found = [], {}
    for key in required:
        val = os.getenv(key)
        if not val or val.startswith("your_") or val.endswith("_here"):
            missing.append(key)
        else:
            found[key] = val[:8] + "…" if len(val) > 12 else val
    if missing:
        raise EnvironmentError(
            "Missing or placeholder environment variables:\n"
            + "\n".join(f"  - {k}" for k in missing)
            + "\n\nCopy .env.example → .env and fill real values."
        )
    return found


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_PRIORITY: list[dict[str, Any]] = [
    {
        "id": "p1",
        "title": "Run first live voice session with Think Fast 2.0 key",
        "meta": "High impact · Now",
        "level": "high",
        "source": "system",
        "created_at": _now_iso(),
    },
    {
        "id": "p2",
        "title": "Confirm encrypted memory + opt into proactive",
        "meta": "Safety · Today",
        "level": "medium",
        "source": "system",
        "created_at": _now_iso(),
    },
]

_BOOKMARKS: list[dict[str, Any]] = [
    {
        "id": "b1",
        "category": "Immediate",
        "title": "Grok Voice Realtime path — stream first session",
        "source": "x.ai",
        "score": 9.6,
        "plan": [
            "Set GROK_VOICE_API_KEY",
            "aether --serve + shell",
            "Start voice session and verify presence states",
            "Test partial transcript path",
        ],
    },
    {
        "id": "b2",
        "category": "Act soon",
        "title": "Proactive opt-in + first mention-spike offer",
        "source": "Aether",
        "score": 8.8,
        "plan": [
            "POST /proactive/opt-in",
            "Feed sample signals to /proactive/evaluate",
            "Accept one offer into Priority",
        ],
    },
    {
        "id": "b3",
        "category": "Possibility",
        "title": "Package shell with electron-builder",
        "source": "Aether",
        "score": 8.0,
        "plan": [
            "cd shell && npm run dist",
            "Verify tray app on target OS",
            "Document unsigned-build warning",
        ],
    },
]

_PENDING_COMPUTER_USE: dict[str, Any] | None = None
_AUDIT: list[dict[str, Any]] = []


def _audit(event: str, payload: dict[str, Any]) -> None:
    _AUDIT.append({"event": event, "at": _now_iso(), **payload})
    if len(_AUDIT) > 300:
        del _AUDIT[:50]


def start_voice_session(user_id: str, mode: str = "reactive") -> dict[str, Any]:
    check_kill_switch()
    result = voice_client.start_session(user_id, mode)
    _audit("session_start", {"session_id": result.get("session_id"), "live": result.get("live")})
    return result


def handle_turn(
    session_id: str,
    transcript: str,
    x_context: list[dict] | None = None,
) -> dict[str, Any]:
    check_kill_switch()
    memories = memory_store.query(transcript, max_records=3)
    result = voice_client.process_turn(session_id, transcript, x_context, memories)
    result["memory_contracts"] = memories
    _audit("turn", {"session_id": session_id, "turns": result.get("turn")})
    return result


def handle_partial(session_id: str, text: str) -> dict[str, Any]:
    check_kill_switch()
    return voice_client.partial(session_id, text)


def update_presence(expression: str, status: str, intensity: float = 0.7) -> dict[str, Any]:
    check_kill_switch()
    valid_expr = {"calm", "attentive", "thoughtful", "pleased", "concerned", "neutral"}
    valid_status = {"listening", "thinking", "speaking", "idle", "proactive"}
    if expression not in valid_expr:
        expression = "neutral"
    if status not in valid_status:
        status = "idle"
    intensity = max(0.0, min(1.0, float(intensity)))
    return {
        "expression": expression,
        "status": status,
        "intensity": intensity,
        "avatar": "updated",
        "timestamp": _now_iso(),
    }


def first_use_magic(user_id: str = "local") -> dict[str, Any]:
    check_kill_switch()
    insight = content_tools.audience_insight()
    moves = [
        {"id": "m1", "title": "Start a live voice session", "why": "Presence becomes real with voice", "effort": "low", "impact": "high"},
        {"id": "m2", "title": "Opt into proactive + run evaluate once", "why": "Unlock mention-spike offers", "effort": "low", "impact": "high"},
        {"id": "m3", "title": "Confirm memory encryption + take one screenshot", "why": "Safety + computer-use gate verified", "effort": "low", "impact": "medium"},
    ]
    return {
        "type": "first_use_magic",
        "user_id": user_id,
        "message": "Welcome. Signal snapshot and three concrete next moves.",
        "audience_insight": insight,
        "moves": moves,
        "presence": {"expression": "pleased", "status": "speaking", "intensity": 0.8},
        "memory_stats": memory_store.stats(),
        "proactive": proactive_engine.status(),
        "timestamp": _now_iso(),
    }


def computer_use_request(action: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
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
    _audit("computer_use_request", {"request_id": request_id, "action": action})
    return {
        "status": "awaiting_spoken_confirmation",
        "request_id": request_id,
        "action": action,
        "message": f"I need spoken confirmation before I {action}. Say yes within 20 seconds.",
        "safety": {"require_spoken_confirmation": True, "never_execute_without_confirm": True},
        "timestamp": _now_iso(),
    }


def computer_use_confirm(request_id: str, spoken_yes: bool = True) -> dict[str, Any]:
    global _PENDING_COMPUTER_USE
    check_kill_switch()
    if not _PENDING_COMPUTER_USE or _PENDING_COMPUTER_USE["request_id"] != request_id:
        return {"error": "No matching pending computer-use request", "request_id": request_id}
    pending = _PENDING_COMPUTER_USE
    _PENDING_COMPUTER_USE = None
    if not spoken_yes:
        _audit("computer_use_cancelled", {"request_id": request_id})
        return {
            "status": "cancelled",
            "request_id": request_id,
            "action": pending["action"],
            "message": "Cancelled. No changes made.",
            "timestamp": _now_iso(),
        }
    result = {
        "status": "confirmed_execute",
        "request_id": request_id,
        "action": pending["action"],
        "details": pending["details"],
        "message": f"Confirmed. Shell may now execute: {pending['action']}",
        "execute_on_shell": True,
        "audit": {"confirmed_by": "spoken", "executed_at": _now_iso()},
        "timestamp": _now_iso(),
    }
    _audit("computer_use_confirmed", {"request_id": request_id, "action": pending["action"]})
    return result


def list_priority() -> list[dict[str, Any]]:
    return list(_PRIORITY)


def list_bookmarks() -> list[dict[str, Any]]:
    return list(_BOOKMARKS)


def make_it_real(bookmark_id: str) -> dict[str, Any]:
    check_kill_switch()
    bm = next((b for b in _BOOKMARKS if b["id"] == bookmark_id), None)
    if not bm:
        return {"error": f"Bookmark {bookmark_id} not found"}
    new_item = {
        "id": f"p-{uuid.uuid4().hex[:6]}",
        "title": bm["title"],
        "meta": f"From Bookmark · {bm['category']} · just now",
        "level": "high",
        "source": "make_it_real",
        "plan": bm.get("plan", []),
        "created_at": _now_iso(),
    }
    _PRIORITY.insert(0, new_item)
    _audit("make_it_real", {"bookmark_id": bookmark_id})
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


def run_demo() -> None:
    print("\n════════════════════════════════════════════════════════════")
    print(f"  AETHER  ·  P3 demo  ·  v{VERSION}")
    print("════════════════════════════════════════════════════════════\n")

    print("→ Kill switch …")
    check_kill_switch()
    print("  ✓ clear\n")

    print("→ Voice session (Realtime-ready path) …")
    sess = start_voice_session("demo-user")
    print(json.dumps(sess, indent=2), "\n")

    print("→ Partial transcript …")
    print(json.dumps(handle_partial(sess["session_id"], "I want to"), indent=2), "\n")

    print("→ First-use + proactive status …")
    print(json.dumps(first_use_magic(), indent=2), "\n")

    print("→ Memory write (encrypted if cryptography present) …")
    memory_store.write({
        "content": "User prefers short calm voice answers under 35 words.",
        "source": "user_said",
        "confidence": 0.94,
        "scope": "session",
        "retention_days": 0,
        "write_permission": "user_only",
        "created_at": _now_iso(),
        "last_accessed": _now_iso(),
    })
    print(json.dumps(memory_store.stats(), indent=2), "\n")

    print("→ Voice turn …")
    print(json.dumps(handle_turn(sess["session_id"], "Remember I like short answers. Next move?"), indent=2), "\n")

    print("→ Proactive opt-in + evaluate …")
    proactive_engine.set_opt_in(True)
    print(json.dumps(proactive_engine.evaluate({"mention_count_15m": 7}), indent=2), "\n")

    print("→ Content ideation …")
    print(json.dumps(content_tools.ideate_thread("presence agents"), indent=2), "\n")

    print("→ Computer-use request + confirm …")
    req = computer_use_request("screenshot", {"reason": "P3"})
    print(json.dumps(req, indent=2))
    print(json.dumps(computer_use_confirm(req["request_id"], True), indent=2), "\n")

    print("→ Make it real …")
    print(json.dumps(make_it_real("b1"), indent=2), "\n")

    print("════════════════════════════════════════════════════════════")
    print("  P3 demo complete.")
    print("  Encrypted memory · proactive · voice partials · packaging ready")
    print("════════════════════════════════════════════════════════════\n")


class AetherHandler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: Any) -> None:
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
                self._json(200, {
                    "status": "ok",
                    "version": VERSION,
                    "p": "P3",
                    "voice_live": voice_client.live,
                    "realtime_ready": voice_client.realtime_ready,
                    "memory": memory_store.stats(),
                    "proactive": proactive_engine.status(),
                })
            elif path == "/priority":
                self._json(200, {"items": list_priority()})
            elif path == "/bookmarks":
                self._json(200, {"items": list_bookmarks()})
            elif path == "/presence":
                self._json(200, update_presence("neutral", "idle", 0.5))
            elif path == "/first-use":
                self._json(200, first_use_magic())
            elif path == "/memory/stats":
                self._json(200, memory_store.stats())
            elif path == "/proactive/status":
                self._json(200, proactive_engine.status())
            elif path == "/audit":
                self._json(200, {"events": _AUDIT[-40:]})
            else:
                self._json(404, {"error": "not found"})
        except RuntimeError as e:
            self._json(503, {"error": str(e)})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return

        try:
            check_kill_switch()
            if path in ("/session/start", "/voice/start"):
                self._json(200, start_voice_session(data.get("user_id", "local"), data.get("mode", "reactive")))
            elif path in ("/turn", "/voice/turn"):
                self._json(200, handle_turn(data.get("session_id", ""), data.get("transcript", ""), data.get("x_context")))
            elif path == "/voice/partial":
                self._json(200, handle_partial(data.get("session_id", ""), data.get("text", "")))
            elif path == "/voice/end":
                self._json(200, voice_client.end_session(data.get("session_id", "")))
            elif path == "/presence":
                self._json(200, update_presence(data.get("expression", "neutral"), data.get("status", "idle"), float(data.get("intensity", 0.7))))
            elif path == "/computer-use/request":
                self._json(200, computer_use_request(data.get("action", "screenshot"), data.get("details")))
            elif path == "/computer-use/confirm":
                self._json(200, computer_use_confirm(data.get("request_id", ""), bool(data.get("spoken_yes", True))))
            elif path == "/make-it-real":
                self._json(200, make_it_real(data.get("bookmark_id", "")))
            elif path == "/priority/add":
                self._json(200, add_priority(data.get("title", "Untitled"), data.get("level", "high")))
            elif path == "/memory/write":
                self._json(200, memory_store.write(data))
            elif path == "/memory/query":
                self._json(200, {"facts": memory_store.query(data.get("text", ""), data.get("max", 3))})
            elif path == "/memory/consent":
                self._json(200, memory_store.set_cross_session_consent(bool(data.get("granted", False))))
            elif path == "/proactive/opt-in":
                self._json(200, proactive_engine.set_opt_in(bool(data.get("opted_in", True))))
            elif path == "/proactive/evaluate":
                self._json(200, proactive_engine.evaluate(data.get("signals") or data))
            elif path == "/content/ideate":
                self._json(200, content_tools.ideate_thread(data.get("topic", "AI agents"), data.get("voice", "builder")))
            elif path == "/content/replies":
                self._json(200, content_tools.suggest_replies(data.get("post", ""), data.get("voice", "builder")))
            elif path == "/content/insight":
                self._json(200, content_tools.audience_insight(data.get("niche", "AI agents / builders")))
            else:
                self._json(404, {"error": "not found"})
        except (RuntimeError, ValueError) as e:
            self._json(400 if isinstance(e, ValueError) else 503, {"error": str(e)})

    def log_message(self, format: str, *args: Any) -> None:
        pass


def run_serve(host: str = "127.0.0.1", port: int = 7420) -> None:
    check_kill_switch()
    server = HTTPServer((host, port), AetherHandler)
    print(f"Aether P3 IPC on http://{host}:{port}  (v{VERSION})")
    print("Voice · Memory(encrypted) · Proactive · Content · Computer-use · Audit")
    print("Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="aether", description="Aether presence OS")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--check-env", action="store_true")
    parser.add_argument("--session", metavar="USER_ID")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=7420)
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
            print("Memory:", memory_store.stats())
        except EnvironmentError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return
    if args.session:
        try:
            validate_env()
            print(json.dumps(start_voice_session(args.session), indent=2))
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()
    print(f"\n  aether --demo          # P3 offline loop (v{VERSION})")
    print("  aether --serve")
    print("  cd shell && npm start")
    print("  cd shell && npm run dist   # package with electron-builder")


if __name__ == "__main__":
    main()
