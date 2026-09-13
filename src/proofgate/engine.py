from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .adapters import AdapterError, DriveAdapter, GitHubAdapter, SourceAdapter
from .models import Decision, RunReceipt, StepResult
from .policy import classify


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fingerprint_signal(source_id: str, subject: str, body: str) -> str:
    normalized = "\n".join([source_id.strip(), subject.strip(), body.strip()])
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class ProofGateEngine:
    source: SourceAdapter
    drive: DriveAdapter
    github: GitHubAdapter
    max_attempts: int = 2
    decider: object = classify
    replay_ledger: dict[str, RunReceipt] = field(default_factory=dict)

    def _retry(self, fn, *, step: str, app: str, object_id: str | None = None):
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                value = fn()
                return value, StepResult(
                    step=step,
                    app=app,
                    status="PASS",
                    object_id=object_id,
                    attempts=attempt,
                )
            except AdapterError as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    time.sleep(0.01)
        raise AdapterError(f"{step} failed after {self.max_attempts} attempts: {last_error}")

    def run(self, source_id: str) -> RunReceipt:
        started_at = utc_now()
        run_id = uuid.uuid4().hex[:12]
        steps: list[StepResult] = []
        errors: list[str] = []
        outputs: dict[str, str] = {}

        try:
            signal = self.source.read_signal(source_id)
            steps.append(StepResult("read_source", signal.source_app, "PASS", signal.source_id, readback_verified=True))
        except AdapterError as exc:
            finished_at = utc_now()
            return RunReceipt(run_id, source_id, "", "REVIEW", 0.0, "FAILED_SOURCE_READ", started_at, finished_at,
                              [StepResult("read_source", "Gmail", "FAIL", detail=str(exc))], {}, [str(exc)])

        fp = fingerprint_signal(signal.source_id, signal.subject, signal.body)
        if fp in self.replay_ledger:
            prior = self.replay_ledger[fp]
            finished_at = utc_now()
            return RunReceipt(
                run_id=run_id,
                source_id=signal.source_id,
                fingerprint=fp,
                decision=prior.decision,
                confidence=prior.confidence,
                status="DUPLICATE_REPLAY_NO_NEW_ACTION",
                started_at=started_at,
                finished_at=finished_at,
                steps=[StepResult("idempotency_check", "Core", "PASS", detail="fingerprint already completed")],
                output_object_ids=dict(prior.output_object_ids),
                replay_of_run_id=prior.run_id,
            )

        decision = self.decider(signal)
        steps.append(StepResult("decide", "Core", "PASS", detail=decision.reason))

        if decision.decision in (Decision.REVIEW, Decision.NO_ACTION):
            finished_at = utc_now()
            receipt = RunReceipt(
                run_id, signal.source_id, fp, decision.decision.value, decision.confidence,
                "SAFE_STOP", started_at, finished_at, steps, outputs, errors
            )
            self.replay_ledger[fp] = receipt
            return receipt

        try:
            runbook = self.drive.read_runbook()
            steps.append(StepResult("read_runbook", "Google Drive", "PASS", str(runbook.get("runbook_id", "runbook")), readback_verified=True))
        except AdapterError as exc:
            errors.append(str(exc))
            finished_at = utc_now()
            receipt = RunReceipt(run_id, signal.source_id, fp, decision.decision.value, decision.confidence,
                                 "FAILED_BEFORE_ACTION", started_at, finished_at, steps + [StepResult("read_runbook", "Google Drive", "FAIL", detail=str(exc))], outputs, errors)
            return receipt

        if "create_or_update_issue" not in runbook.get("allowed_actions", []):
            finished_at = utc_now()
            receipt = RunReceipt(run_id, signal.source_id, fp, "REVIEW", 0.40, "RUNBOOK_DENIED_ACTION", started_at, finished_at,
                                 steps + [StepResult("runbook_gate", "Core", "FAIL", detail="GitHub issue action not allowed")], outputs, ["runbook denied action"])
            return receipt

        issue_title = f"[ProofGate] {signal.subject[:90]}"
        issue_body = (
            f"Source: {signal.source_app}:{signal.source_id}\n"
            f"Fingerprint: {fp}\n"
            f"Decision: ACTION ({decision.confidence:.2f})\n\n"
            f"Evidence summary:\n{signal.body[:1200]}\n"
        )

        try:
            (issue_id, created_new), issue_step = self._retry(
                lambda: self.github.upsert_issue(fp, issue_title, issue_body),
                step="upsert_issue",
                app="GitHub",
            )
            issue_step.object_id = issue_id
            issue_step.detail = "created" if created_new else "reused existing idempotent target"
            steps.append(issue_step)
            outputs["github_issue_id"] = issue_id

            issue = self.github.read_issue(issue_id)
            issue_ok = issue.get("idempotency_key") == fp and issue.get("title") == issue_title
            steps.append(StepResult("readback_issue", "GitHub", "PASS" if issue_ok else "FAIL", issue_id, readback_verified=issue_ok))
            if not issue_ok:
                raise AdapterError("GitHub readback mismatch")
        except AdapterError as exc:
            errors.append(str(exc))
            finished_at = utc_now()
            receipt = RunReceipt(run_id, signal.source_id, fp, decision.decision.value, decision.confidence,
                                 "PARTIAL_FAILURE_GITHUB", started_at, finished_at, steps + [StepResult("github_action", "GitHub", "FAIL", detail=str(exc))], outputs, errors)
            return receipt

        provisional = {
            "run_id": run_id,
            "source_id": signal.source_id,
            "fingerprint": fp,
            "decision": decision.decision.value,
            "github_issue_id": outputs["github_issue_id"],
            "status": "ACTION_WRITTEN_PENDING_RECEIPT_READBACK",
        }
        receipt_json = json.dumps(provisional, ensure_ascii=False, sort_keys=True, indent=2)

        try:
            drive_id, drive_step = self._retry(
                lambda: self.drive.write_receipt(run_id, receipt_json),
                step="write_receipt",
                app="Google Drive",
            )
            drive_step.object_id = drive_id
            steps.append(drive_step)
            outputs["drive_receipt_id"] = drive_id
            receipt_readback = self.drive.read_receipt(drive_id)
            receipt_ok = receipt_readback == receipt_json
            steps.append(StepResult("readback_receipt", "Google Drive", "PASS" if receipt_ok else "FAIL", drive_id, readback_verified=receipt_ok))
            if not receipt_ok:
                raise AdapterError("Drive receipt readback mismatch")
        except AdapterError as exc:
            errors.append(str(exc))
            finished_at = utc_now()
            receipt = RunReceipt(run_id, signal.source_id, fp, decision.decision.value, decision.confidence,
                                 "PARTIAL_SUCCESS_GITHUB_DRIVE_RECEIPT_FAILED", started_at, finished_at, steps + [StepResult("drive_receipt", "Google Drive", "FAIL", detail=str(exc))], outputs, errors)
            return receipt

        finished_at = utc_now()
        receipt = RunReceipt(
            run_id, signal.source_id, fp, decision.decision.value, decision.confidence,
            "SUCCESS_VERIFIED", started_at, finished_at, steps, outputs, errors
        )
        self.replay_ledger[fp] = receipt
        return receipt
