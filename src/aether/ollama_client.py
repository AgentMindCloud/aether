"""Ollama integration — local embeddings + optional generation (P5).

Default: http://127.0.0.1:11434
Used for semantic ranking assist and model fallback in the abstraction layer.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class OllamaClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base = (base_url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self.embed_model = os.getenv("AETHER_OLLAMA_EMBED", "nomic-embed-text")
        self.chat_model = os.getenv("AETHER_OLLAMA_CHAT", "llama3.2")
        self.available = False
        self._probe()

    def _probe(self) -> None:
        try:
            with urllib.request.urlopen(f"{self.base}/api/tags", timeout=2) as r:
                self.available = r.status == 200
        except Exception:
            self.available = False

    def status(self) -> dict[str, Any]:
        models: list[str] = []
        if self.available:
            try:
                with urllib.request.urlopen(f"{self.base}/api/tags", timeout=3) as r:
                    data = json.loads(r.read().decode())
                    models = [m.get("name", "") for m in data.get("models", [])]
            except Exception:
                pass
        return {
            "available": self.available,
            "base": self.base,
            "embed_model": self.embed_model,
            "chat_model": self.chat_model,
            "models": models[:20],
        }

    def embed(self, text: str) -> list[float] | None:
        if not self.available or not text.strip():
            return None
        payload = json.dumps({"model": self.embed_model, "prompt": text}).encode()
        req = urllib.request.Request(
            f"{self.base}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode())
                return data.get("embedding")
        except Exception:
            return None

    def generate(self, prompt: str, system: str = "") -> str | None:
        if not self.available:
            return None
        body: dict[str, Any] = {
            "model": self.chat_model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            body["system"] = system
        req = urllib.request.Request(
            f"{self.base}/api/generate",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
                return data.get("response")
        except Exception:
            return None


ollama = OllamaClient()
