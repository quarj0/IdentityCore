#!/usr/bin/env python3
"""Evaluate locked private predictions without emitting subjects or OCR text."""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

TASKS = {"liveness", "face_match", "document_authenticity", "ocr"}


class EvaluationError(ValueError):
    pass


def require(condition):
    if not condition:
        raise EvaluationError("Invalid evaluation contract or lock mismatch.")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def read_json(path, expected_sha=None):
    require(path.stat().st_size <= 32 * 1024 * 1024)
    try:
        with path.open("rb") as source:
            content = source.read(32 * 1024 * 1024 + 1)
        require(len(content) <= 32 * 1024 * 1024)
        if expected_sha is not None:
            require(hashlib.sha256(content).hexdigest() == expected_sha)
        return json.loads(content.decode("utf-8"), object_pairs_hook=unique_object)
    except (ValueError, UnicodeError):
        raise EvaluationError("Invalid evaluation JSON.") from None


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def locked_file(root, value):
    require(isinstance(value, dict) and set(value) == {"path", "sha256"})
    require(isinstance(value["path"], str) and isinstance(value["sha256"], str))
    require(re.fullmatch(r"[a-f0-9]{64}", value["sha256"]) is not None)
    path = (root / value["path"]).resolve()
    require(path.is_relative_to(root) and path.is_file())
    require(digest(path) == value["sha256"])
    return path


def finite(value):
    require(type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 1)
    return value


def rows(value, field):
    require(isinstance(value, list) and 1 <= len(value) <= 10000)
    result = {}
    for row in value:
        require(isinstance(row, dict) and set(row) == {"id", field})
        key = row["id"]
        require(
            isinstance(key, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", key) is not None
            and key not in result
        )
        result[key] = row[field]
    return result


def distance(left, right):
    if left == right:
        return 0
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(
                min(previous[j] + 1, current[-1] + 1, previous[j - 1] + (a != b))
            )
        previous = current
    return previous[-1]


def binary_metrics(truth, predictions, threshold):
    require(all(type(label) is bool for label in truth.values()))
    positive, negative = sum(truth.values()), len(truth) - sum(truth.values())
    require(positive > 0 and negative > 0)
    tp = fp = fn = tn = 0
    for key, label in truth.items():
        accepted = finite(predictions[key]) >= threshold
        tp += bool(accepted and label)
        fp += bool(accepted and not label)
        fn += bool(not accepted and label)
        tn += bool(not accepted and not label)
    return {
        "precision": tp / (tp + fp) if tp + fp else 0,
        "recall": tp / positive,
        "false_accept_rate": fp / negative,
        "false_reject_rate": fn / positive,
        "error_rate": (fp + fn) / len(truth),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
    }


def ocr_metrics(truth, predictions):
    comparisons = []
    work = 0
    for key, reference in truth.items():
        prediction = predictions[key]
        require(
            isinstance(reference, str)
            and isinstance(prediction, str)
            and len(reference) <= 2048
            and len(prediction) <= 2048
        )
        left, right = reference.split(), prediction.split()
        require(len(left) <= 256 and len(right) <= 256)
        work += (len(reference) * len(prediction) if reference != prediction else 0) + (
            len(left) * len(right) if left != right else 0
        )
        require(work <= 20_000_000)
        comparisons.append((reference, prediction, left, right))
    characters = words = character_errors = word_errors = overlap = expected = (
        actual
    ) = 0
    for reference, prediction, left, right in comparisons:
        characters += len(reference)
        words += len(left)
        character_errors += distance(reference, prediction)
        word_errors += distance(left, right)
        overlap += sum((Counter(left) & Counter(right)).values())
        expected += len(left)
        actual += len(right)
    require(characters > 0 and words > 0)
    return {
        "precision": overlap / actual if actual else 0,
        "recall": overlap / expected,
        "character_error_rate": character_errors / characters,
        "word_error_rate": word_errors / words,
    }


def evaluate(manifest_path):
    root = manifest_path.resolve().parent
    manifest = read_json(manifest_path)
    require(
        isinstance(manifest, dict)
        and set(manifest) == {"evaluation_version", "dataset_version", "tasks"}
        and manifest["evaluation_version"] == "1"
    )
    require(
        isinstance(manifest["dataset_version"], str)
        and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", manifest["dataset_version"])
        is not None
    )
    require(isinstance(manifest["tasks"], dict) and set(manifest["tasks"]) == TASKS)
    report = {
        "evaluation_version": "1",
        "manifest_sha256": digest(manifest_path),
        "dataset_version": manifest["dataset_version"],
        "tasks": {},
        "passed": True,
    }
    for task in sorted(TASKS):
        config = manifest["tasks"][task]
        require(
            isinstance(config, dict)
            and set(config)
            == {
                "model_version",
                "model",
                "dataset",
                "predictions",
                "threshold",
                "gates",
            }
        )
        version = config["model_version"]
        require(
            isinstance(version, str)
            and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", version) is not None
        )
        model = locked_file(root, config["model"])
        dataset = locked_file(root, config["dataset"])
        predictions = read_json(
            locked_file(root, config["predictions"]),
            expected_sha=config["predictions"]["sha256"],
        )
        require(
            isinstance(predictions, dict)
            and set(predictions)
            == {"model_sha256", "model_version", "dataset_sha256", "rows"}
        )
        require(
            predictions["model_sha256"] == digest(model)
            and predictions["model_version"] == version
            and predictions["dataset_sha256"] == digest(dataset)
        )
        truth = rows(
            read_json(dataset, expected_sha=config["dataset"]["sha256"]),
            "text" if task == "ocr" else "label",
        )
        outputs = rows(predictions["rows"], "text" if task == "ocr" else "score")
        require(set(truth) == set(outputs))
        threshold = config["threshold"]
        require(threshold is None if task == "ocr" else type(threshold) in {int, float})
        metrics = (
            ocr_metrics(truth, outputs)
            if task == "ocr"
            else binary_metrics(truth, outputs, finite(threshold))
        )
        gates = config["gates"]
        required_gates = (
            {"precision", "recall", "character_error_rate", "word_error_rate"}
            if task == "ocr"
            else {
                "precision",
                "recall",
                "false_accept_rate",
                "false_reject_rate",
                "error_rate",
            }
        )
        require(isinstance(gates, dict) and set(gates) == required_gates)
        gates = {name: finite(bound) for name, bound in gates.items()}
        passed = all(
            (
                metrics[name] >= bound
                if name in {"precision", "recall"}
                else metrics[name] <= bound
            )
            for name, bound in gates.items()
        )
        report["tasks"][task] = {
            "model_version": version,
            "model_sha256": digest(model),
            "dataset_sha256": digest(dataset),
            "predictions_sha256": config["predictions"]["sha256"],
            "samples": len(truth),
            "threshold": threshold,
            "metrics": metrics,
            "gates": gates,
            "passed": passed,
        }
        report["passed"] &= passed
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(args.manifest)
        args.report.write_text(
            json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
    except (EvaluationError, OSError, TypeError, KeyError, RecursionError):
        parser.exit(2, "Evaluation failed: invalid private inputs or lock mismatch.\n")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
