import json
import unittest
from pathlib import Path


class LiveEvidenceContractTests(unittest.TestCase):
    def test_r008_verified_envelope_preserves_chronology_and_replay(self):
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "evidence" / "live_r008_verified.json").read_text(encoding="utf-8"))

        self.assertEqual(data["source"]["app"], "Gmail")
        self.assertTrue(data["source"]["fresh_readback"])
        self.assertTrue(data["runbook"]["readback_verified"])
        self.assertTrue(data["github_action"]["readback_verified"])
        self.assertEqual(data["proof_receipt"]["written_status"], "ACTION_WRITTEN_PENDING_RECEIPT_READBACK")
        self.assertTrue(data["proof_receipt"]["readback_verified"])
        self.assertEqual(data["terminal_status"], "SUCCESS_VERIFIED")
        self.assertTrue(data["replay"]["same_fingerprint"])
        self.assertEqual(data["replay"]["matching_github_issue_count"], 1)
        self.assertFalse(data["replay"]["new_issue_created"])
        self.assertEqual(data["replay"]["status"], "DUPLICATE_REPLAY_NO_NEW_ACTION")


if __name__ == "__main__":
    unittest.main()
