"""GitHub tools for Aether — first-class builder actions (P4).

Uses the user's connected GitHub via the platform connector when available.
Falls back to clear 'not connected / configure token' messages otherwise.
Mutating actions remain confirmation-gated at the runtime layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_issues(owner: str, repo: str, state: str = "open") -> dict[str, Any]:
    """List issues. Real implementation uses connected GitHub tools when available."""
    return {
        "type": "github_list_issues",
        "owner": owner,
        "repo": repo,
        "state": state,
        "status": "ready_for_connector",
        "message": (
            f"Would list {state} issues for {owner}/{repo}. "
            "Wire to connected GitHub (github___* tools) or GITHUB_TOKEN for live results."
        ),
        "items": [],
        "id": f"gh-issues-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
    }


def list_prs(owner: str, repo: str, state: str = "open") -> dict[str, Any]:
    return {
        "type": "github_list_prs",
        "owner": owner,
        "repo": repo,
        "state": state,
        "status": "ready_for_connector",
        "message": f"Would list {state} PRs for {owner}/{repo}.",
        "items": [],
        "id": f"gh-prs-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
    }


def create_issue(owner: str, repo: str, title: str, body: str = "") -> dict[str, Any]:
    """Stage issue creation — still requires UI/spoken confirmation in production path."""
    return {
        "type": "github_create_issue",
        "owner": owner,
        "repo": repo,
        "title": title,
        "body": body,
        "status": "staged",
        "message": (
            f"Staged issue '{title}' on {owner}/{repo}. "
            "Confirm to execute via connected GitHub."
        ),
        "requires_confirmation": True,
        "id": f"gh-issue-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
    }


def n8n_webhook(url: str, payload: dict[str, Any] | None = None, method: str = "POST") -> dict[str, Any]:
    """Optional external orchestration hook — never stores memory."""
    if not url or "n8n" not in url.lower() and not url.startswith("http"):
        return {
            "error": "n8n_webhook requires a user-configured absolute URL",
            "hint": "Set a full webhook URL from your n8n instance",
        }
    return {
        "type": "n8n_webhook",
        "url": url,
        "method": method.upper(),
        "payload": payload or {},
        "status": "ready",
        "message": "Would POST to external n8n webhook. Aether memory remains local.",
        "id": f"n8n-{uuid.uuid4().hex[:8]}",
        "timestamp": _now(),
    }
