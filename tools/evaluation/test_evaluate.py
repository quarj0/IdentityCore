import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "evaluation", Path(__file__).with_name("evaluate.py")
)
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class LockedEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.manifest = {
            "evaluation_version": "1",
            "dataset_version": "synthetic-fixture-1",
            "tasks": {},
        }
        for task in evaluation.TASKS:
            model = self.root / (task + ".model")
            model.write_bytes(b"synthetic model artifact, no biometric data")
            truth = (
                [{"id": "a", "text": "SYNTHETIC TEXT"}]
                if task == "ocr"
                else [{"id": "a", "label": True}, {"id": "b", "label": False}]
            )
            dataset = self.root / (task + ".dataset.json")
            dataset.write_text(json.dumps(truth))
            outputs = (
                [{"id": "a", "text": "SYNTHETIC TEXT"}]
                if task == "ocr"
                else [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.1}]
            )
            predictions = self.root / (task + ".predictions.json")
            predictions.write_text(
                json.dumps(
                    {
                        "model_sha256": evaluation.digest(model),
                        "model_version": "fixture-1",
                        "dataset_sha256": evaluation.digest(dataset),
                        "rows": outputs,
                    }
                )
            )

            def lock(path):
                return {"path": path.name, "sha256": evaluation.digest(path)}

            gates = (
                {
                    "precision": 1,
                    "recall": 1,
                    "character_error_rate": 0,
                    "word_error_rate": 0,
                }
                if task == "ocr"
                else {
                    "precision": 1,
                    "recall": 1,
                    "false_accept_rate": 0,
                    "false_reject_rate": 0,
                    "error_rate": 0,
                }
            )
            self.manifest["tasks"][task] = {
                "model_version": "fixture-1",
                "model": lock(model),
                "dataset": lock(dataset),
                "predictions": lock(predictions),
                "threshold": None if task == "ocr" else 0.5,
                "gates": gates,
            }
        self.path = self.root / "manifest.json"
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.manifest))

    def test_reproducible_report_contains_metrics_without_subject_text(self):
        report = evaluation.evaluate(self.path)
        self.assertEqual(report, evaluation.evaluate(self.path))
        self.assertTrue(report["passed"])
        self.assertNotIn("SYNTHETIC TEXT", json.dumps(report))
        self.assertEqual(report["tasks"]["ocr"]["metrics"]["word_error_rate"], 0)
        self.assertEqual(
            report["tasks"]["face_match"]["metrics"]["false_accept_rate"], 0
        )

    def test_model_dataset_and_prediction_tampering_is_rejected(self):
        for suffix in ["model", "dataset.json", "predictions.json"]:
            path = self.root / ("liveness." + suffix)
            original = path.read_bytes()
            path.write_bytes(original + b" ")
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate(self.path)
            path.write_bytes(original)

    def test_changed_threshold_produces_gate_failure(self):
        self.manifest["tasks"]["face_match"]["threshold"] = 0.05
        self.save()
        report = evaluation.evaluate(self.path)
        self.assertFalse(report["passed"])
        self.assertEqual(
            report["tasks"]["face_match"]["metrics"]["false_accept_rate"], 1
        )

    def test_missing_or_duplicate_prediction_subjects_are_rejected(self):
        path = self.root / "face_match.predictions.json"
        payload = json.loads(path.read_text())
        for values in [[payload["rows"][0]], [payload["rows"][0]] * 2]:
            payload["rows"] = values
            path.write_text(json.dumps(payload))
            self.manifest["tasks"]["face_match"]["predictions"]["sha256"] = (
                evaluation.digest(path)
            )
            self.save()
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate(self.path)

    def test_nonfinite_and_unbounded_thresholds_fail(self):
        for threshold in [True, float("nan"), float("inf"), -0.1, 1.1, 10**500]:
            self.manifest["tasks"]["liveness"]["threshold"] = threshold
            self.save()
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate(self.path)

    def test_wrong_prediction_model_lineage_is_rejected(self):
        path = self.root / "ocr.predictions.json"
        payload = json.loads(path.read_text())
        payload["model_version"] = "wrong"
        path.write_text(json.dumps(payload))
        self.manifest["tasks"]["ocr"]["predictions"]["sha256"] = evaluation.digest(path)
        self.save()
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.evaluate(self.path)

    def test_private_file_paths_cannot_escape_manifest_directory(self):
        self.manifest["tasks"]["ocr"]["model"]["path"] = "../outside.model"
        self.save()
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.evaluate(self.path)

    def test_failed_metric_cannot_hide_a_later_nonfinite_gate(self):
        self.manifest["tasks"]["face_match"]["threshold"] = 0.99
        self.manifest["tasks"]["face_match"]["gates"]["recall"] = float("nan")
        self.save()
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.evaluate(self.path)

    def test_aggregate_ocr_work_is_rejected_before_distance_computation(self):
        from unittest.mock import patch

        truth = {str(i): "x" * 2048 for i in range(5)}
        predictions = {str(i): "y" * 2048 for i in range(5)}
        with patch.object(evaluation, "distance") as distance:
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.ocr_metrics(truth, predictions)
            distance.assert_not_called()

    def test_large_identical_ocr_data_uses_exact_match_fast_path(self):
        truth = {str(i): "x" * 2048 for i in range(100)}
        self.assertEqual(
            evaluation.ocr_metrics(truth, truth)["character_error_rate"], 0
        )


if __name__ == "__main__":
    unittest.main()
