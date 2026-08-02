"""Aether Governed Memory Store — P5.

Primary: Postgres (Docker) when AETHER_DATABASE_URL or default local is reachable.
Fallback: encrypted file store (~/.aether/memory).
Contracts enforced either way. Learning fields supported (feedback, distill).
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
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except ImportError:
    Fernet = None  # type: ignore
    _HAS_CRYPTO = False

_HAS_PG = False
try:
    import psycopg
    from psycopg.rows import dict_row
    _HAS_PG = True
except ImportError:
    psycopg = None  # type: ignore
    dict_row = None  # type: ignore


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
        if len(key) < 32:
            key = base64.urlsafe_b64encode(key.ljust(32, "0").encode()[:32]).decode()
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        return None


def _default_dsn() -> str:
    return os.getenv(
        "AETHER_DATABASE_URL",
        "postgresql://aether:aether_local_dev@127.0.0.1:5432/aether",
    )


class GovernedMemoryStore:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or os.path.expanduser("~/.aether/memory"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.session_path = self.root / "session.json"
        self.user_path = self.root / "user.json"
        self.consent_path = self.root / "consent.json"
        self._fernet = _get_fernet()
        self.encrypted = self._fernet is not None
        self.backend = "file"
        self._pg = None
        self._session: list[dict[str, Any]] = []
        self._user: list[dict[str, Any]] = []
        self._consent = {"cross_session": False, "updated_at": None}

        if _HAS_PG:
            try:
                self._pg = psycopg.connect(_default_dsn(), row_factory=dict_row, autocommit=True)
                self._ensure_pg_schema()
                self.backend = "postgres"
                self._consent = self._pg_load_consent()
            except Exception:
                self._pg = None
                self.backend = "file"

        if self.backend == "file":
            self._session = self._load(self.session_path)
            self._user = self._load(self.user_path)
            self._consent = self._load_consent_file()

    # ---------- Postgres ----------
    def _ensure_pg_schema(self) -> None:
        assert self._pg is not None
        self._pg.execute(
            """
            CREATE TABLE IF NOT EXISTS aether_facts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL NOT NULL,
                scope TEXT NOT NULL,
                retention_days INTEGER NOT NULL DEFAULT 0,
                write_permission TEXT NOT NULL DEFAULT 'user_only',
                created_at TIMESTAMPTZ NOT NULL,
                last_accessed TIMESTAMPTZ NOT NULL,
                feedback_score REAL NOT NULL DEFAULT 0,
                feedback_count INTEGER NOT NULL DEFAULT 0,
                tags TEXT[] DEFAULT '{}',
                meta JSONB DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS aether_consent (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_facts_scope ON aether_facts(scope);
            CREATE INDEX IF NOT EXISTS idx_facts_content ON aether_facts USING gin (to_tsvector('english', content));
            """
        )

    def _pg_load_consent(self) -> dict[str, Any]:
        assert self._pg is not None
        row = self._pg.execute(
            "SELECT value FROM aether_consent WHERE key = 'cross_session'"
        ).fetchone()
        if not row:
            return {"cross_session": False, "updated_at": None}
        val = row["value"]
        if isinstance(val, str):
            val = json.loads(val)
        return val

    def _pg_write(self, fact: dict[str, Any]) -> dict[str, Any]:
        assert self._pg is not None
        self._pg.execute(
            """
            INSERT INTO aether_facts (
                id, content, source, confidence, scope, retention_days,
                write_permission, created_at, last_accessed, feedback_score, feedback_count, tags, meta
            ) VALUES (
                %(id)s, %(content)s, %(source)s, %(confidence)s, %(scope)s, %(retention_days)s,
                %(write_permission)s, %(created_at)s, %(last_accessed)s,
                %(feedback_score)s, %(feedback_count)s, %(tags)s, %(meta)s
            )
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                confidence = EXCLUDED.confidence,
                last_accessed = EXCLUDED.last_accessed,
                feedback_score = EXCLUDED.feedback_score,
                feedback_count = EXCLUDED.feedback_count,
                meta = EXCLUDED.meta
            """,
            {
                "id": fact["id"],
                "content": fact["content"],
                "source": fact["source"],
                "confidence": float(fact["confidence"]),
                "scope": fact["scope"],
                "retention_days": int(fact.get("retention_days", 0)),
                "write_permission": fact.get("write_permission", "user_only"),
                "created_at": fact["created_at"],
                "last_accessed": fact["last_accessed"],
                "feedback_score": float(fact.get("feedback_score", 0)),
                "feedback_count": int(fact.get("feedback_count", 0)),
                "tags": fact.get("tags") or [],
                "meta": json.dumps(fact.get("meta") or {}),
            },
        )
        return fact

    def _pg_query(self, text: str, max_records: int) -> list[dict[str, Any]]:
        assert self._pg is not None
        scopes = ["session"]
        if self._consent.get("cross_session"):
            scopes.extend(["user", "global"])
        rows = self._pg.execute(
            """
            SELECT * FROM aether_facts
            WHERE scope = ANY(%s)
              AND (
                content ILIKE %s
                OR to_tsvector('english', content) @@ plainto_tsquery('english', %s)
              )
            ORDER BY confidence DESC, last_accessed DESC
            LIMIT %s
            """,
            (scopes, f"%{text}%", text, max_records),
        ).fetchall()
        results = []
        for r in rows:
            fact = dict(r)
            if isinstance(fact.get("meta"), str):
                try:
                    fact["meta"] = json.loads(fact["meta"])
                except Exception:
                    fact["meta"] = {}
            fact["last_accessed"] = _now()
            self._pg.execute(
                "UPDATE aether_facts SET last_accessed = %s WHERE id = %s",
                (fact["last_accessed"], fact["id"]),
            )
            results.append(fact)
        return results

    def _pg_stats(self) -> dict[str, Any]:
        assert self._pg is not None
        session_n = self._pg.execute("SELECT COUNT(*) AS c FROM aether_facts WHERE scope = 'session'").fetchone()["c"]
        user_n = self._pg.execute("SELECT COUNT(*) AS c FROM aether_facts WHERE scope IN ('user','global')").fetchone()["c"]
        return {
            "session_facts": session_n,
            "user_facts": user_n,
            "cross_session_consent": self._consent.get("cross_session", False),
            "encrypted_at_rest": False,
            "backend": "postgres",
            "crypto_available": _HAS_CRYPTO,
        }

    # ---------- File fallback ----------
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

    def _load_consent_file(self) -> dict[str, Any]:
        if not self.consent_path.exists():
            return {"cross_session": False, "updated_at": None}
        try:
            return json.loads(self.consent_path.read_text(encoding="utf-8"))
        except Exception:
            return {"cross_session": False, "updated_at": None}

    # ---------- Shared API ----------
    def set_cross_session_consent(self, granted: bool) -> dict[str, Any]:
        self._consent = {"cross_session": bool(granted), "updated_at": _now()}
        if self.backend == "postgres" and self._pg:
            self._pg.execute(
                """
                INSERT INTO aether_consent (key, value, updated_at)
                VALUES ('cross_session', %s::jsonb, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
                """,
                (json.dumps(self._consent), self._consent["updated_at"]),
            )
        else:
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
        if fact["source"] not in ("user_said", "x_context", "derived", "system", "distilled", "feedback"):
            raise ValueError("invalid source")
        return fact

    def write(self, fact: dict[str, Any]) -> dict[str, Any]:
        fact = dict(fact)
        fact.setdefault("id", f"m-{uuid.uuid4().hex[:10]}")
        fact.setdefault("created_at", _now())
        fact["last_accessed"] = _now()
        fact.setdefault("feedback_score", 0.0)
        fact.setdefault("feedback_count", 0)
        self._validate_contract(fact)

        scope = fact["scope"]
        if scope in ("user", "global") and not self._consent.get("cross_session"):
            fact["scope"] = "session"
            fact["retention_days"] = 0
            scope = "session"

        if self.backend == "postgres" and self._pg:
            return self._pg_write(fact)

        if scope == "session":
            self._session.append(fact)
            self._save(self.session_path, self._session)
        else:
            self._user.append(fact)
            self._save(self.user_path, self._user)
        return fact

    def query(self, text: str, max_records: int = 5) -> list[dict[str, Any]]:
        if self.backend == "postgres" and self._pg:
            return self._pg_query(text, max_records)

        q = text.lower()
        candidates = list(self._session)
        if self._consent.get("cross_session"):
            candidates.extend(self._user)
        scored: list[tuple[float, dict]] = []
        for fact in candidates:
            content = fact.get("content", "").lower()
            score = sum(1.0 for token in q.split() if token in content)
            score *= float(fact.get("confidence", 0.5))
            score += float(fact.get("feedback_score", 0)) * 0.1
            if score > 0:
                fact = dict(fact)
                fact["last_accessed"] = _now()
                scored.append((score, fact))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:max_records]]

    def feedback(self, fact_id: str, useful: bool, note: str = "") -> dict[str, Any]:
        """Learning signal: adjust confidence and feedback_score."""
        delta = 0.08 if useful else -0.12
        if self.backend == "postgres" and self._pg:
            row = self._pg.execute("SELECT * FROM aether_facts WHERE id = %s", (fact_id,)).fetchone()
            if not row:
                return {"error": "fact not found", "id": fact_id}
            conf = max(0.05, min(0.99, float(row["confidence"]) + delta))
            fs = float(row["feedback_score"]) + (1.0 if useful else -1.0)
            fc = int(row["feedback_count"]) + 1
            self._pg.execute(
                "UPDATE aether_facts SET confidence = %s, feedback_score = %s, feedback_count = %s, last_accessed = %s WHERE id = %s",
                (conf, fs, fc, _now(), fact_id),
            )
            return {"id": fact_id, "confidence": conf, "feedback_score": fs, "feedback_count": fc, "useful": useful, "note": note}

        for store in (self._session, self._user):
            for fact in store:
                if fact.get("id") == fact_id:
                    fact["confidence"] = max(0.05, min(0.99, float(fact.get("confidence", 0.5)) + delta))
                    fact["feedback_score"] = float(fact.get("feedback_score", 0)) + (1.0 if useful else -1.0)
                    fact["feedback_count"] = int(fact.get("feedback_count", 0)) + 1
                    fact["last_accessed"] = _now()
                    self._save(self.session_path, self._session)
                    self._save(self.user_path, self._user)
                    return {"id": fact_id, "confidence": fact["confidence"], "feedback_score": fact["feedback_score"], "useful": useful}
        return {"error": "fact not found", "id": fact_id}

    def distill_session_to_user(self, max_facts: int = 5, min_confidence: float = 0.7) -> dict[str, Any]:
        """Propose high-value session facts for promotion to user scope (consent required)."""
        if not self._consent.get("cross_session"):
            return {"status": "blocked", "reason": "cross_session consent required", "proposed": []}

        candidates: list[dict[str, Any]] = []
        if self.backend == "postgres" and self._pg:
            rows = self._pg.execute(
                """
                SELECT * FROM aether_facts
                WHERE scope = 'session' AND confidence >= %s
                ORDER BY confidence DESC, feedback_score DESC
                LIMIT %s
                """,
                (min_confidence, max_facts),
            ).fetchall()
            candidates = [dict(r) for r in rows]
        else:
            candidates = sorted(
                [f for f in self._session if float(f.get("confidence", 0)) >= min_confidence],
                key=lambda f: (float(f.get("confidence", 0)), float(f.get("feedback_score", 0))),
                reverse=True,
            )[:max_facts]

        promoted = []
        for c in candidates:
            new_fact = dict(c)
            new_fact["id"] = f"m-{uuid.uuid4().hex[:10]}"
            new_fact["scope"] = "user"
            new_fact["source"] = "distilled"
            new_fact["created_at"] = _now()
            new_fact["last_accessed"] = _now()
            new_fact["retention_days"] = int(new_fact.get("retention_days") or 365)
            self.write(new_fact)
            promoted.append(new_fact)

        return {"status": "ok", "promoted": len(promoted), "facts": promoted}

    def clear_session(self) -> None:
        if self.backend == "postgres" and self._pg:
            self._pg.execute("DELETE FROM aether_facts WHERE scope = 'session'")
        else:
            self._session = []
            self._save(self.session_path, self._session)

    def stats(self) -> dict[str, Any]:
        if self.backend == "postgres" and self._pg:
            s = self._pg_stats()
            s["root"] = str(self.root)
            return s
        return {
            "session_facts": len(self._session),
            "user_facts": len(self._user),
            "cross_session_consent": self._consent.get("cross_session", False),
            "encrypted_at_rest": self.encrypted,
            "backend": "file",
            "crypto_available": _HAS_CRYPTO,
            "root": str(self.root),
        }


memory_store = GovernedMemoryStore()
