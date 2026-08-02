"""Aether Governed Memory Store — P3.

Contract enforcement from .grok/memory.yaml.
File-backed with optional Fernet encryption-at-rest when cryptography is installed
and AETHER_MEMORY_KEY (or auto-generated local key) is available.
"""

from __future__ import annotations

import base64
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

try:
    from cryptography.fernet import Fernet, InvalidToken
    _HAS_CRYPTO = True
except ImportError:
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore
    _HAS_CRYPTO = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_fernet() -> Any | None:
    if not _HAS_CRYPTO:
        return None
    key = os.getenv("AETHER_MEMORY_KEY", "").strip()
    key_path = Path(os.path.expanduser("~/.aether/memory.key"))
    if not key:
        if key_path.exists():
            key = key_path.read_text(encoding="utf-8").strip()
        else:
            key = Fernet.generate_key().decode("utf-8")
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_text(key, encoding="utf-8")
            try:
                os.chmod(key_path, 0o600)
            except OSError:
                pass
    try:
        # Accept raw url-safe base64 or generate from passphrase-like string
        if len(key) < 32:
            key = base64.urlsafe_b64encode(key.ljust(32, "0").encode()[:32]).decode()
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        return None


class GovernedMemoryStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.path.expanduser("~/.aether/memory"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.session_path = self.root / "session.json"
        self.user_path = self.root / "user.json"
        self.consent_path = self.root / "consent.json"
        self._fernet = _get_fernet()
        self.encrypted = self._fernet is not None
        self._session: list[dict[str, Any]] = self._load(self.session_path)
        self._user: list[dict[str, Any]] = self._load(self.user_path)
        self._consent = self._load_consent()

    def _encode(self, data: list[dict[str, Any]]) -> str:
        raw = json.dumps(data)
        if self._fernet:
            return self._fernet.encrypt(raw.encode("utf-8")).decode("utf-8")
        return raw

    def _decode(self, text: str) -> list[dict[str, Any]]:
        if not text.strip():
            return []
        if self._fernet:
            try:
                raw = self._fernet.decrypt(text.encode("utf-8")).decode("utf-8")
                data = json.loads(raw)
                return data if isinstance(data, list) else []
            except Exception:
                # Fallback: try plain JSON (migration from unencrypted)
                try:
                    data = json.loads(text)
                    return data if isinstance(data, list) else []
                except Exception:
                    return []
        try:
            data = json.loads(text)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _load(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            return self._decode(path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, path: Path, items: list[dict[str, Any]]) -> None:
        path.write_text(self._encode(items), encoding="utf-8")

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
        fact = dict(fact)
        fact.setdefault("id", f"m-{uuid.uuid4().hex[:10]}")
        fact.setdefault("created_at", _now())
        fact["last_accessed"] = _now()
        self._validate_contract(fact)

        scope = fact["scope"]
        if scope in ("user", "global") and not self._consent.get("cross_session"):
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
        q = text.lower()
        candidates = list(self._session)
        if self._consent.get("cross_session"):
            candidates.extend(self._user)

        scored: list[tuple[float, dict]] = []
        for fact in candidates:
            content = fact.get("content", "").lower()
            score = sum(1.0 for token in q.split() if token in content)
            score *= float(fact.get("confidence", 0.5))
            if score > 0:
                fact = dict(fact)
                fact["last_accessed"] = _now()
                scored.append((score, fact))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [f for _, f in scored[:max_records]]
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
            "encrypted_at_rest": self.encrypted,
            "crypto_available": _HAS_CRYPTO,
            "root": str(self.root),
        }


memory_store = GovernedMemoryStore()
