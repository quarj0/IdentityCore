"""HTTP AI and webhook fixtures with controlled latency and real object reads."""

import hashlib
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread, Lock
import time
from shared import observability as telemetry


def ai_result(path):
    metadata = {
        "model_name": "synthetic-fixture",
        "model_version": "1",
        "status": "completed",
    }
    if path == "/v1/document/quality":
        return {**metadata, "quality_score": 0.95, "issues": []}
    if path == "/v1/document/classify":
        return {
            **metadata,
            "classification_status": "recognized",
            "predicted_document_type": "national_id",
            "predicted_country_code": "GH",
            "expected_document_type": "national_id",
            "matched_expected_document_type": True,
            "confidence_score": 0.95,
            "evidence_score": 0.95,
            "classification_margin": 0.5,
            "workflow_action": "continue",
            "requires_manual_review": False,
            "manual_review": {"required": False, "priority": "low", "reason_codes": []},
            "issues": [],
            "ocr": {"average_confidence": 0.95, "line_count": 2},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "score_components": {},
            "classifier": {"name": "synthetic", "version": "1"},
            "ocr_model": {"name": "synthetic", "version": "1"},
        }
    if path == "/v1/document/ocr":
        return {
            **metadata,
            "confidence_score": 0.95,
            "extracted_fields": {"full_name": "Synthetic Applicant"},
            "raw_text_lines": [],
        }
    if path == "/v1/liveness/check":
        return {
            **metadata,
            "passed": True,
            "score": 0.97,
            "confidence_level": "high",
            "metrics": {"face_count": 1, "avg_detection_confidence": 0.98},
        }
    if path == "/v1/face/compare":
        return {
            **metadata,
            "matched": False,
            "match_score": 0.76,
            "threshold_used": 0.85,
            "confidence_level": "medium",
        }
    raise ValueError("Unsupported synthetic AI operation")


class Fixtures:
    def __init__(self, storage, ai_token, webhook_secrets, latency=0.1):
        self.storage, self.ai_token = storage, ai_token
        self.webhook_secrets, self.latency = webhook_secrets, latency
        self.events, self.errors, self.lock = [], 0, Lock()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # Never log request bodies, credentials or object references.

            def do_POST(self):
                content = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                try:
                    payload = json.loads(content)
                    if self.path.startswith("/webhooks/"):
                        secret = owner.webhook_secrets[self.path]
                        signing_key = (
                            hashlib.sha256(secret.encode()).hexdigest().encode()
                        )
                        expected = hmac.new(
                            signing_key,
                            self.headers["X-IdentityCore-Timestamp"].encode()
                            + b"."
                            + content,
                            hashlib.sha256,
                        ).hexdigest()
                        if not hmac.compare_digest(
                            "sha256=" + expected,
                            self.headers.get("X-IdentityCore-Signature", ""),
                        ):
                            raise ValueError("Synthetic webhook signature invalid")
                        expected_v1 = (
                            "v1="
                            + hmac.new(
                                signing_key,
                                self.headers["X-IdentityCore-Timestamp"].encode()
                                + b"."
                                + payload["id"].encode()
                                + b"."
                                + content,
                                hashlib.sha256,
                            ).hexdigest()
                        )
                        if expected_v1 not in self.headers.get(
                            "X-IdentityCore-Signature-V1", ""
                        ).split(","):
                            raise ValueError("Synthetic versioned signature invalid")
                        with owner.lock:
                            owner.events.append((payload["id"], payload["type"]))
                        result = {"accepted": True}
                    else:
                        if not hmac.compare_digest(
                            self.headers.get("X-Internal-Token", ""), owner.ai_token
                        ):
                            raise ValueError("Synthetic AI token invalid")
                        token = telemetry.ENVIRONMENT.set(
                            telemetry.environment(
                                self.headers.get("X-IdentityCore-Environment")
                            )
                        )
                        try:
                            with telemetry.operation(
                                "ai", "request", context=telemetry.extract(self.headers)
                            ):
                                for key_field, bucket_field in [
                                    ("document_storage_key", "document_storage_bucket"),
                                    ("selfie_storage_key", "selfie_storage_bucket"),
                                ]:
                                    if payload.get(key_field):
                                        with telemetry.operation("storage", "read"):
                                            response = owner.storage.get_object(
                                                Bucket=payload[bucket_field],
                                                Key=payload[key_field],
                                            )
                                            while response["Body"].read(1024 * 1024):
                                                pass
                                            response["Body"].close()
                                time.sleep(owner.latency)
                                result = ai_result(self.path)
                        finally:
                            telemetry.ENVIRONMENT.reset(token)
                    body = json.dumps(result).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception:
                    with owner.lock:
                        owner.errors += 1
                    self.send_response(500)
                    self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 18081), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
