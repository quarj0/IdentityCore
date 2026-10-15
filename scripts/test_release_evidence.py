import hashlib
import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = Path(__file__).with_name("check_release_evidence.py")
spec = importlib.util.spec_from_file_location("release_evidence", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SHA = "a" * 40


class ReleaseEvidenceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "synthetic.txt").write_text("synthetic only", encoding="utf-8")
        digest = hashlib.sha256((self.root / "synthetic.txt").read_bytes()).hexdigest()
        self.now = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
        self.manifest = {
            "schema_version": 1, "environment": "production", "mode": "pilot",
            "head_sha": SHA,
            "checks": {name: {
                "result": "pass", "owner": "operator", "reviewer": "independent reviewer",
                "completed_at": self.now.isoformat(),
                "artifacts": [{"path": "synthetic.txt", "sha256": digest}],
            } for name in module.COMMON},
        }

    def check(self, mode="pilot"):
        return module.check_evidence(
            self.manifest, self.root, head_sha=SHA, mode=mode, now=self.now
        )

    def test_complete_structure(self):
        # Synthetic structural test does not certify that an approval occurred.
        self.assertTrue(self.check()["ready"])

    def test_missing_checks_rejected(self):
        del self.manifest["checks"]["managed_model_evaluation"]
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_not_applicable_is_never_pass(self):
        self.manifest["checks"]["byop_live_provider_journey"]["result"] = "not_applicable"
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_commit_binding(self):
        self.manifest["head_sha"] = "b" * 40
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_distinct_reviewer(self):
        self.manifest["checks"]["privacy_and_legal_assessment"]["reviewer"] = "operator"
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_stale_approval(self):
        self.manifest["checks"]["go_live_approval"]["completed_at"] = (
            self.now - timedelta(days=8)).isoformat()
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_digest_mismatch(self):
        self.manifest["checks"]["managed_model_evaluation"]["artifacts"][0]["sha256"] = "0" * 64
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_path_escape(self):
        self.manifest["checks"]["deployed_security"]["artifacts"][0]["path"] = "../outside.txt"
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_symlink_escape(self):
        (self.root / "outside").symlink_to(self.root.parent, target_is_directory=True)
        self.manifest["checks"]["deployed_security"]["artifacts"][0]["path"] = "outside/file"
        with self.assertRaises(module.EvidenceError):
            self.check()

    def test_commercial_needs_payment_and_terms(self):
        self.manifest["mode"] = "commercial"
        with self.assertRaises(module.EvidenceError):
            self.check(mode="commercial")
        for k in module.COMMERCIAL:
            self.manifest["checks"][k] = dict(
                self.manifest["checks"]["privacy_and_legal_assessment"])
        self.assertTrue(self.check(mode="commercial")["ready"])


if __name__ == "__main__":
    unittest.main()
