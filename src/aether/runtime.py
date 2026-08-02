"""Aether runtime — Build 0.1 felt presence

Talk-friendly defaults, memory-aware turns, optional bind host for mobile LAN.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

from aether.voice import voice_client
from aether.memory import memory_store
from aether.proactive import proactive_engine
from aether import content as content_tools
from aether import models as model_layer
from aether import github_tools
from aether import learning
from aether.ollama_client import ollama

VERSION = "0.6.0"


def check_kill_switch() -> None:
    if os.getenv("AETHER_DISABLED") == "1":
        raise RuntimeError("Aether kill switch engaged (AETHER_DISABLED=1). All activity halted.")


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
    {"id": "p1", "title": "Start Session and speak or type", "meta": "Talk loop · Now", "level": "medium", "source": "system", "created_at": _now_iso()},
    {"id": "p2", "title": "Optional: GROK_VOICE_API_KEY for live voice later", "meta": "Later", "level": "low", "source": "system", "created_at": _now_iso()},
]

_BOOKMARKS: list[dict[str, Any]] = [
    {
        "id": "b1", "category": "Immediate", "title": "Talk path is live (TTS + text, mic when allowed)",
        "source": "Aether", "score": 9.5,
        "plan": ["Start Session", "Type or use mic", "Hear agent reply"],
    },
]

_PENDING_COMPUTER_USE: dict[str, Any] | None = None
_AUDIT: list[dict[str, Any]] = []


def _audit(event: str, payload: dict[str, Any]) -> None:
    _AUDIT.append({"event": event, "at": _now_iso(), **payload})
    if len(_AUDIT) > 400:
        del _AUDIT[:80]


def start_voice_session(user_id: str, mode: str = "reactive") -> dict[str, Any]:
    check_kill_switch()
    result = voice_client.start_session(user_id, mode)
    result["model"] = model_layer.get_model()
    result["memory_backend"] = memory_store.stats().get("backend")
    _audit("session_start", {"session_id": result.get("session_id")})
    return result


def handle_turn(session_id: str, transcript: str, x_context: list[dict] | None = None) -> dict[str, Any]:
    check_kill_switch()
    memories = memory_store.query(transcript, max_records=5)
    result = voice_client.process_turn(session_id, transcript, x_context, memories)
    result["memory_contracts"] = memories
    result["model"] = model_layer.get_model()
    result["memory_backend"] = memory_store.stats().get("backend")
    t = transcript.lower()
    suggestions = []
    if any(w in t for w in ("issue", "github", "pr", "pull")):
        suggestions += [{"action": "github_list_issues", "label": "List issues"}, {"action": "github_list_prs", "label": "List PRs"}]
    if any(w in t for w in ("remember", "learn", "forget", "feedback")):
        suggestions.append({"action": "learning_status", "label": "Learning status"})
    if any(w in t for w in ("screenshot", "screen")):
        suggestions.append({"action": "computer_use_screenshot", "label": "Screenshot"})
    if any(w in t for w in ("thread", "post", "idea")):
        suggestions.append({"action": "content_ideate", "label": "Ideate"})
    result["suggested_actions"] = suggestions
    _audit("turn", {"session_id": session_id})
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
    return {"expression": expression, "status": status, "intensity": intensity, "timestamp": _now_iso()}


def first_use_magic(user_id: str = "local") -> dict[str, Any]:
    check_kill_switch()
    return {
        "type": "first_use_magic",
        "message": "Ready. Start Session, then speak or type.",
        "moves": [
            {"id": "m1", "title": "Start Session and speak or type", "why": "Talk loop + TTS works now", "effort": "low", "impact": "high"},
            {"id": "m2", "title": "Optional live Grok Voice key later", "why": "Same path, Realtime stream", "effort": "low", "impact": "medium"},
            {"id": "m3", "title": "Mobile later uses same HTTP API", "why": "One brain, many surfaces", "effort": "low", "impact": "medium"},
        ],
        "memory": memory_store.stats(),
        "ollama": ollama.status(),
        "learning": learning.learning_status(),
        "model": model_layer.model_status(),
        "proactive": proactive_engine.status(),
        "presence": {"expression": "pleased", "status": "speaking", "intensity": 0.8},
        "timestamp": _now_iso(),
    }


def computer_use_request(action: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    global _PENDING_COMPUTER_USE
    check_kill_switch()
    allowed = {"screenshot", "list_windows", "focus_window", "type_text", "click", "move_mouse"}
    if action not in allowed:
        return {"error": f"Unknown action: {action}", "allowed": list(allowed)}
    request_id = str(uuid.uuid4())[:8]
    _PENDING_COMPUTER_USE = {"request_id": request_id, "action": action, "details": details or {}, "status": "awaiting_spoken_confirmation", "created_at": _now_iso()}
    _audit("computer_use_request", {"request_id": request_id, "action": action})
    return {
        "status": "awaiting_spoken_confirmation",
        "request_id": request_id,
        "action": action,
        "message": f"Spoken confirmation required before {action}.",
        "safety": {"require_spoken_confirmation": True},
        "timestamp": _now_iso(),
    }


def computer_use_confirm(request_id: str, spoken_yes: bool = True) -> dict[str, Any]:
    global _PENDING_COMPUTER_USE
    check_kill_switch()
    if not _PENDING_COMPUTER_USE or _PENDING_COMPUTER_USE["request_id"] != request_id:
        return {"error": "No matching pending request"}
    pending = _PENDING_COMPUTER_USE
    _PENDING_COMPUTER_USE = None
    if not spoken_yes:
        return {"status": "cancelled", "request_id": request_id, "action": pending["action"]}
    _audit("computer_use_confirmed", {"request_id": request_id})
    return {
        "status": "confirmed_execute",
        "request_id": request_id,
        "action": pending["action"],
        "details": pending["details"],
        "execute_on_shell": True,
        "timestamp": _now_iso(),
    }


def list_priority() -> list[dict[str, Any]]:
    return list(_PRIORITY)


def list_bookmarks() -> list[dict[str, Any]]:
    return list(_BOOKMARKS)


def make_it_real(bookmark_id: str) -> dict[str, Any]:
    check_kill_switch()
    bm = next((b for b in _BOOKMARKS if b["id"] == bookmark_id), None)
    if not bm:
        return {"error": f"Bookmark {bookmark_id} not found"}
    item = {"id": f"p-{uuid.uuid4().hex[:6]}", "title": bm["title"], "meta": f"From Bookmark · just now", "level": "medium", "source": "make_it_real", "plan": bm.get("plan", []), "created_at": _now_iso()}
    _PRIORITY.insert(0, item)
    return {"status": "promoted", "priority_item": item, "timestamp": _now_iso()}


def add_priority(title: str, level: str = "medium") -> dict[str, Any]:
    item = {"id": f"p-{uuid.uuid4().hex[:6]}", "title": title, "meta": "Captured · Now", "level": level, "source": "capture", "created_at": _now_iso()}
    _PRIORITY.insert(0, item)
    return {"status": "added", "item": item}


def run_demo() -> None:
    print("\n════════════════════════════════════════════════════════════")
    print(f"  AETHER  ·  Build 0.1  ·  v{VERSION}")
    print("════════════════════════════════════════════════════════════\n")
    check_kill_switch()
    print(json.dumps(memory_store.stats(), indent=2))
    print(json.dumps(first_use_magic(), indent=2))
    print("OK\n")


class AetherHandler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: Any) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
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
                    "status": "ok", "version": VERSION, "p": "0.1",
                    "voice_live": voice_client.live,
                    "memory": memory_store.stats(),
                    "ollama": ollama.status(),
                    "learning": learning.learning_status(),
                    "model": model_layer.model_status(),
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
            elif path == "/learning/status":
                self._json(200, learning.learning_status())
            elif path == "/ollama":
                self._json(200, ollama.status())
            elif path == "/proactive/status":
                self._json(200, proactive_engine.status())
            elif path == "/model":
                self._json(200, model_layer.model_status())
            elif path == "/audit":
                self._json(200, {"events": _AUDIT[-50:]})
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
                self._json(200, add_priority(data.get("title", "Untitled"), data.get("level", "medium")))
            elif path == "/memory/write":
                self._json(200, memory_store.write(data))
            elif path == "/memory/query":
                self._json(200, {"facts": memory_store.query(data.get("text", ""), data.get("max", 5))})
            elif path == "/memory/consent":
                self._json(200, memory_store.set_cross_session_consent(bool(data.get("granted", False))))
            elif path == "/learning/feedback":
                self._json(200, learning.record_feedback(data.get("fact_id", ""), bool(data.get("useful", True)), data.get("note", "")))
            elif path == "/learning/distill":
                self._json(200, learning.distill(int(data.get("max_facts", 5)), float(data.get("min_confidence", 0.7))))
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
            elif path == "/switch-model":
                self._json(200, model_layer.switch_model(data.get("model", "")))
            elif path == "/github/issues":
                self._json(200, github_tools.list_issues(data.get("owner", "AgentMindCloud"), data.get("repo", "aether"), data.get("state", "open")))
            elif path == "/github/prs":
                self._json(200, github_tools.list_prs(data.get("owner", "AgentMindCloud"), data.get("repo", "aether"), data.get("state", "open")))
            elif path == "/github/issue/create":
                self._json(200, github_tools.create_issue(data.get("owner", ""), data.get("repo", ""), data.get("title", ""), data.get("body", "")))
            elif path == "/n8n/webhook":
                self._json(200, github_tools.n8n_webhook(data.get("url", ""), data.get("payload"), data.get("method", "POST")))
            else:
                self._json(404, {"error": "not found"})
        except (RuntimeError, ValueError) as e:
            self._json(400 if isinstance(e, ValueError) else 503, {"error": str(e)})

    def log_message(self, format: str, *args: Any) -> None:
        pass


def run_serve(host: str | None = None, port: int = 7420) -> None:
    check_kill_switch()
    host = host or os.getenv("AETHER_HOST", "127.0.0.1")
    # For phone access on LAN later: AETHER_HOST=0.0.0.0
    server = HTTPServer((host, port), AetherHandler)
    print(f"Aether Build 0.1 IPC http://{host}:{port}  v{VERSION}")
    print(f"Memory backend: {memory_store.stats().get('backend')} | Ollama: {ollama.available}")
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
    parser.add_argument("--host", default=None, help="Bind host (default 127.0.0.1; use 0.0.0.0 for LAN/mobile)")
    args = parser.parse_args()
    if args.demo:
        run_demo()
        return
    if args.serve:
        run_serve(host=args.host, port=args.port)
        return
    if args.check_env:
        try:
            found = validate_env()
            print("Environment OK:")
            for k, v in found.items():
                print(f"  {k}: {v}")
            print("Memory:", memory_store.stats())
            print("Ollama:", ollama.status())
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


if __name__ == "__main__":
    main()
