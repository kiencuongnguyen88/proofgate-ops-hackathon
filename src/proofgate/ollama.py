from __future__ import annotations

import json
import urllib.error
import urllib.request

from .models import Decision, DecisionResult, Signal


SYSTEM = """You classify one operations email for a safety-gated agent.
Return JSON only with keys decision, confidence, reason.
decision must be exactly ACTION, REVIEW, or NO_ACTION.
ACTION only when the message contains a concrete material request/deadline/status requiring follow-up.
REVIEW when intent is ambiguous or evidence is insufficient.
NO_ACTION for clearly informational messages.
Never invent facts outside the supplied email."""


def classify_with_ollama(
    signal: Signal,
    *,
    base_url: str = "http://127.0.0.1:11434",
    model: str = "qwen3:4b",
    timeout: float = 30.0,
) -> DecisionResult:
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "source_id": signal.source_id,
                        "subject": signal.subject,
                        "body": signal.body,
                        "sender": signal.sender,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Ollama decision failed: {exc}") from exc

    raw = outer.get("message", {}).get("content", "")
    try:
        data = json.loads(raw)
        decision = Decision(str(data["decision"]).upper())
        confidence = float(data["confidence"])
        reason = str(data["reason"])
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid Ollama decision payload: {raw!r}") from exc

    confidence = max(0.0, min(1.0, confidence))
    return DecisionResult(decision, confidence, reason)
