import unittest

from proofgate.adapters import FakeDriveAdapter, FakeGitHubAdapter, FakeSourceAdapter
from proofgate.engine import ProofGateEngine
from proofgate.models import Signal


def make_signal(source_id="m1", subject="Action required: deadline", body="Please submit the final item by Friday deadline."):
    return Signal("Gmail", source_id, subject, body, "ops@example.org", "2026-09-13T00:00:00Z")


def make_engine(signal, *, github_fail=0, drive_fail=0, max_attempts=2):
    return ProofGateEngine(
        FakeSourceAdapter({signal.source_id: signal}),
        FakeDriveAdapter({"runbook_id": "rb1", "allowed_actions": ["create_or_update_issue"]}, fail_writes=drive_fail),
        FakeGitHubAdapter(fail_writes=github_fail),
        max_attempts=max_attempts,
    )


class ProofGateEngineTests(unittest.TestCase):
    def test_happy_path_has_three_apps_and_verified_readback(self):
        signal = make_signal()
        engine = make_engine(signal)
        r = engine.run(signal.source_id)
        self.assertEqual(r.status, "SUCCESS_VERIFIED")
        self.assertEqual(r.decision, "ACTION")
        self.assertIn("github_issue_id", r.output_object_ids)
        self.assertIn("drive_receipt_id", r.output_object_ids)
        self.assertTrue(any(s.app == "Gmail" and s.status == "PASS" for s in r.steps))
        self.assertTrue(any(s.step == "readback_issue" and s.readback_verified for s in r.steps))
        self.assertTrue(any(s.step == "readback_receipt" and s.readback_verified for s in r.steps))

    def test_duplicate_replay_creates_no_new_action(self):
        signal = make_signal()
        engine = make_engine(signal)
        first = engine.run(signal.source_id)
        issue_count = len(engine.github.issues)
        receipt_count = len(engine.drive.receipts)
        second = engine.run(signal.source_id)
        self.assertEqual(first.status, "SUCCESS_VERIFIED")
        self.assertEqual(second.status, "DUPLICATE_REPLAY_NO_NEW_ACTION")
        self.assertEqual(second.replay_of_run_id, first.run_id)
        self.assertEqual(len(engine.github.issues), issue_count)
        self.assertEqual(len(engine.drive.receipts), receipt_count)

    def test_uncertain_input_stops_without_external_write(self):
        signal = make_signal(subject="Possible follow-up", body="We might need something later, but we are not sure. If needed we will say so.")
        engine = make_engine(signal)
        r = engine.run(signal.source_id)
        self.assertEqual(r.decision, "REVIEW")
        self.assertEqual(r.status, "SAFE_STOP")
        self.assertEqual(len(engine.github.issues), 0)
        self.assertEqual(len(engine.drive.receipts), 0)

    def test_partial_failure_is_not_reported_as_success(self):
        signal = make_signal()
        engine = make_engine(signal, drive_fail=2, max_attempts=2)
        r = engine.run(signal.source_id)
        self.assertEqual(r.status, "PARTIAL_SUCCESS_GITHUB_DRIVE_RECEIPT_FAILED")
        self.assertIn("github_issue_id", r.output_object_ids)
        self.assertNotIn("drive_receipt_id", r.output_object_ids)
        self.assertTrue(r.errors)

    def test_bounded_retry_recovers_single_transient_failure(self):
        signal = make_signal()
        engine = make_engine(signal, github_fail=1, max_attempts=2)
        r = engine.run(signal.source_id)
        self.assertEqual(r.status, "SUCCESS_VERIFIED")
        step = next(s for s in r.steps if s.step == "upsert_issue")
        self.assertEqual(step.attempts, 2)

    def test_recovery_after_partial_failure_reuses_issue_then_finishes_receipt(self):
        signal = make_signal()
        engine = make_engine(signal, drive_fail=2, max_attempts=2)
        first = engine.run(signal.source_id)
        self.assertEqual(first.status, "PARTIAL_SUCCESS_GITHUB_DRIVE_RECEIPT_FAILED")
        issue_id = first.output_object_ids["github_issue_id"]
        second = engine.run(signal.source_id)
        self.assertEqual(second.status, "SUCCESS_VERIFIED")
        self.assertEqual(second.output_object_ids["github_issue_id"], issue_id)
        self.assertEqual(len(engine.github.issues), 1)
        upsert = next(s for s in second.steps if s.step == "upsert_issue")
        self.assertEqual(upsert.detail, "reused existing idempotent target")


if __name__ == "__main__":
    unittest.main()
