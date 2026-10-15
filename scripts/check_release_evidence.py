#!/usr/bin/env python3
"""Fail-closed release evidence integrity checks, NOT production certification."""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

COMMON = {
    "historical_review_remediation": 30,
    "managed_model_evaluation": 90,
    "byop_live_provider_journey": 30,
    "deployed_security": 7,
    "deployed_readiness": 7,
    "backup_restore": 30,
    "real_inference_load_test": 30,
    "oncall_alert_delivery": 30,
    "independent_security_assessment": 180,
    "privacy_and_legal_assessment": 180,
    "go_live_approval": 7,
}
COMMERCIAL = {"billing_and_payment_reconciliation": 30, "commercial_terms": 180}
INDEPENDENT = {
    "managed_model_evaluation",
    "independent_security_assessment",
    "privacy_and_legal_assessment",
    "go_live_approval",
    "billing_and_payment_reconciliation",
    "commercial_terms",
}
MAX_BYTES = 25 * 1024 * 1024


class EvidenceError(ValueError):
    pass


def utc(value):
    if not isinstance(value, str):
        raise EvidenceError("Invalid timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError("Invalid timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise EvidenceError("Timestamp is not UTC")
    return dt


def digest(path):
    h, count = hashlib.sha256(), 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            count += len(block)
            if count > MAX_BYTES:
                raise EvidenceError("Evidence file too large")
            h.update(block)
    if not count:
        raise EvidenceError("Empty evidence file")
    return h.hexdigest()


def check_evidence(manifest, evidence_root, *, head_sha, mode, now=None):
    now = now or datetime.now(timezone.utc)
    if mode not in ("pilot", "commercial"):
        raise EvidenceError("Unknown release mode")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise EvidenceError("Unsupported manifest version")
    if manifest.get("environment") != "production":
        raise EvidenceError("Not production evidence")
    if not isinstance(head_sha, str) or not re.fullmatch("[a-f0-9]{40}", head_sha):
        raise EvidenceError("Invalid candidate SHA")
    if manifest.get("head_sha") != head_sha or manifest.get("mode") != mode:
        raise EvidenceError("Manifest scope or candidate mismatch")
    required = {**COMMON, **(COMMERCIAL if mode == "commercial" else {})}
    checks = manifest.get("checks")
    if not isinstance(checks, dict) or set(checks) != set(required):
        raise EvidenceError("Missing or unexpected release checks")
    root = Path(evidence_root).resolve(strict=True)
    if not root.is_dir():
        raise EvidenceError("Evidence root is not a directory")
    for name, max_age in required.items():
        entry = checks[name]
        if not isinstance(entry, dict) or entry.get("result") != "pass":
            raise EvidenceError(f"{name}: not passed")
        owner, reviewer = entry.get("owner"), entry.get("reviewer")
        if not isinstance(owner, str) or not owner.strip() or len(owner) > 120:
            raise EvidenceError(f"{name}: missing owner")
        if name in INDEPENDENT and (
            not isinstance(reviewer, str)
            or not reviewer.strip()
            or reviewer.strip().casefold() == owner.strip().casefold()
        ):
            raise EvidenceError(f"{name}: distinct reviewer required")
        time = utc(entry.get("completed_at"))
        if time > now + timedelta(minutes=5) or now - time > timedelta(days=max_age):
            raise EvidenceError(f"{name}: stale or future-dated")
        artifacts = entry.get("artifacts")
        if not isinstance(artifacts, list) or not 1 <= len(artifacts) <= 12:
            raise EvidenceError(f"{name}: missing artifacts")
        for a in artifacts:
            if not isinstance(a, dict):
                raise EvidenceError(f"{name}: malformed artifact")
            rel, expected = a.get("path"), a.get("sha256")
            if not isinstance(rel, str) or not rel or "\x00" in rel:
                raise EvidenceError(f"{name}: invalid path")
            if not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected):
                raise EvidenceError(f"{name}: invalid digest")
            part = Path(rel)
            if part.is_absolute() or ".." in part.parts or len(part.parts) > 8:
                raise EvidenceError(f"{name}: unsafe artifact path")
            candidate = (root / part).resolve()
            if not candidate.is_relative_to(root) or not candidate.is_file():
                raise EvidenceError(f"{name}: evidence missing or outside root")
            if digest(candidate) != expected:
                raise EvidenceError(f"{name}: digest mismatch")
    return {"ready": True, "mode": mode, "checks_verified": sorted(required)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--mode", required=True, choices=["pilot", "commercial"])
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = check_evidence(data, args.evidence_root, head_sha=args.head_sha, mode=args.mode)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ready": False, "reason": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
