from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import FakeDriveAdapter, FakeGitHubAdapter, FakeSourceAdapter
from .engine import ProofGateEngine
from .models import Signal
from .ollama import classify_with_ollama


def load_fixture(path: Path) -> Signal:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Signal(**data)


def main() -> None:
    p = argparse.ArgumentParser(description="Run ProofGate Ops against a local fixture.")
    p.add_argument("fixture", type=Path)
    p.add_argument("--replay", action="store_true", help="Run the same input twice to prove idempotency.")
    p.add_argument("--ollama", action="store_true", help="Use a local Ollama model for ACTION/REVIEW/NO_ACTION.")
    p.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    p.add_argument("--model", default="qwen3:4b")
    args = p.parse_args()

    signal = load_fixture(args.fixture)
    source = FakeSourceAdapter({signal.source_id: signal})
    drive = FakeDriveAdapter({
        "runbook_id": "rb-hackathon-demo-v1",
        "allowed_actions": ["create_or_update_issue"],
        "target_repo": "demo/repo",
    })
    github = FakeGitHubAdapter()
    if args.ollama:
        decider = lambda s: classify_with_ollama(s, base_url=args.ollama_url, model=args.model)
    else:
        from .policy import classify
        decider = classify
    engine = ProofGateEngine(source, drive, github, decider=decider)

    first = engine.run(signal.source_id)
    print(json.dumps(first.to_dict(), ensure_ascii=False, indent=2))
    if args.replay:
        print("\n--- replay ---")
        second = engine.run(signal.source_id)
        print(json.dumps(second.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
