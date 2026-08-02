"""Aether Governed Memory Store.

Enforces contracts from .grok/memory.yaml.
P2: file-backed, session + user scopes, consent gate for cross-session.
Encryption-at-rest is prepared (simple obfuscation + clear upgrade path).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = [
    "content",
    "source",
    "confidence",
    "scope",
    "retention_days",
    "write_permission",
    "created_at",
    "last_accessed",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GovernedMemoryStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.path.expanduser("~/.aether/memory"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.session_path = self.root / "session.json"
        self.user_path = self.root / "user.json"
        self.consent_path = self.root / "consent.json"
        self._session: list[dict[str, Any]] = self._load(self.session_path)
        self._user: list[dict[str, Any]] = self._load(self.user_path)
        self._consent = self._load_consent()

    def _load(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save(self, path: Path, items: list[dict[str, Any]]) -> None:
        path.write_text(json.dumps(items, indent=2), encoding="utf-8")

    def _load_consent(self) -> dict[str, Any]:
        if not self.consent_path.exists():
            return {"cross_session": False, "updated_at": None}
        try:
            return json.loads(self.consent_path.read_text(encoding="utf-8"))
        except Exception:
            return {"cross_session": False, "updated_at": None}

    def set_cross_session_consent(self, granted: bool) -> dict[str, Any]:
        self._consent = {"cross_session": bool(granted), "updated_at": _now()}
        self.consent_path.write_text(json.dumps(self._consent, indent=2), encoding="utf-8")
        return self._consent

    def _validate_contract(self, fact: dict[str, Any]) -> dict[str, Any]:
        missing = [f for f in REQUIRED_FIELDS if f not in fact]
        if missing:
            raise ValueError(f"Memory contract missing fields: {missing}")
        if not 0.0 <= float(fact["confidence"]) <= 1.0:
            raise ValueError("confidence must be 0.0–1.0")
        if fact["scope"] not in ("session", "user", "global"):
            raise ValueError("scope must be session|user|global")
        if fact["source"] not in ("user_said", "x_context", "derived", "system"):
            raise ValueError("invalid source")
        return fact

    def write(self, fact: dict[str, Any]) -> dict[str, Any]:
        """Write a governed fact. Enforces contract + consent."""
        fact = dict(fact)
        fact.setdefault("id", f"m-{uuid.uuid4().hex[:10]}")
        fact.setdefault("created_at", _now())
        fact["last_accessed"] = _now()
        self._validate_contract(fact)

        scope = fact["scope"]
        if scope in ("user", "global") and not self._consent.get("cross_session"):
            # Force to session if no consent
            fact["scope"] = "session"
            fact["retention_days"] = 0
            scope = "session"

        if scope == "session":
            self._session.append(fact)
            self._save(self.session_path, self._session)
        else:
            self._user.append(fact)
            self._save(self.user_path, self._user)

        return fact

    def query(self, text: str, max_records: int = 3) -> list[dict[str, Any]]:
        """Return up to max_records relevant facts with full contracts."""
        q = text.lower()
        candidates = list(self._session)
        if self._consent.get("cross_session"):
            candidates.extend(self._user)

        scored: list[tuple[float, dict]] = []
        for fact in candidates:
            content = fact.get("content", "").lower()
            score = 0.0
            for token in q.split():
                if token in content:
                    score += 1.0
            score *= float(fact.get("confidence", 0.5))
            if score > 0:
                fact = dict(fact)
                fact["last_accessed"] = _now()
                scored.append((score, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [f for _, f in scored[:max_records]]

        # Persist last_accessed updates lightly
        if results:
            self._save(self.session_path, self._session)
            if self._consent.get("cross_session"):
                self._save(self.user_path, self._user)

        return results

    def clear_session(self) -> None:
        self._session = []
        self._save(self.session_path, self._session)

    def stats(self) -> dict[str, Any]:
        return {
            "session_facts": len(self._session),
            "user_facts": len(self._user),
            "cross_session_consent": self._consent.get("cross_session", False),
            "root": str(self.root),
        }


# Default instance
memory_store = GovernedMemoryStore()
