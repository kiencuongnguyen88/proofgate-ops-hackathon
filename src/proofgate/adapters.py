from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Signal


class AdapterError(RuntimeError):
    pass


class SourceAdapter:
    def read_signal(self, source_id: str) -> Signal:
        raise NotImplementedError


class DriveAdapter:
    def read_runbook(self) -> dict[str, Any]:
        raise NotImplementedError

    def write_receipt(self, run_id: str, receipt_json: str) -> str:
        raise NotImplementedError

    def read_receipt(self, object_id: str) -> str:
        raise NotImplementedError


class GitHubAdapter:
    def upsert_issue(self, idempotency_key: str, title: str, body: str) -> tuple[str, bool]:
        """Return (issue_id, created_new)."""
        raise NotImplementedError

    def read_issue(self, issue_id: str) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class FakeSourceAdapter(SourceAdapter):
    signals: dict[str, Signal]

    def read_signal(self, source_id: str) -> Signal:
        try:
            return self.signals[source_id]
        except KeyError as exc:
            raise AdapterError(f"signal not found: {source_id}") from exc


@dataclass
class FakeDriveAdapter(DriveAdapter):
    runbook: dict[str, Any]
    receipts: dict[str, str] = field(default_factory=dict)
    fail_writes: int = 0

    def read_runbook(self) -> dict[str, Any]:
        return dict(self.runbook)

    def write_receipt(self, run_id: str, receipt_json: str) -> str:
        if self.fail_writes > 0:
            self.fail_writes -= 1
            raise AdapterError("injected Drive write failure")
        object_id = f"drive-receipt-{run_id}"
        self.receipts[object_id] = receipt_json
        return object_id

    def read_receipt(self, object_id: str) -> str:
        if object_id not in self.receipts:
            raise AdapterError(f"receipt not found: {object_id}")
        return self.receipts[object_id]


@dataclass
class FakeGitHubAdapter(GitHubAdapter):
    issues: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_key: dict[str, str] = field(default_factory=dict)
    fail_writes: int = 0

    def upsert_issue(self, idempotency_key: str, title: str, body: str) -> tuple[str, bool]:
        if self.fail_writes > 0:
            self.fail_writes -= 1
            raise AdapterError("injected GitHub write failure")
        if idempotency_key in self.by_key:
            return self.by_key[idempotency_key], False
        issue_id = str(len(self.issues) + 1)
        self.by_key[idempotency_key] = issue_id
        self.issues[issue_id] = {
            "id": issue_id,
            "title": title,
            "body": body,
            "idempotency_key": idempotency_key,
            "state": "open",
        }
        return issue_id, True

    def read_issue(self, issue_id: str) -> dict[str, Any]:
        if issue_id not in self.issues:
            raise AdapterError(f"issue not found: {issue_id}")
        return dict(self.issues[issue_id])
