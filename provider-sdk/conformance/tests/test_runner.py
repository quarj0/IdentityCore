import importlib.util
import json
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


CONFORMANCE_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "identitycore_provider_conformance", CONFORMANCE_DIR / "run.py"
)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


class ConformingProviderHandler(BaseHTTPRequestHandler):
    key_id = "test-key"
    secret = "test-secret"
    claimed_nonces = set()

    def log_message(self, _format, *_args):
        return

    def _signed_response(self, status, payload, nonce):
        body = runner.canonical_json(payload)
        timestamp = int(time.time())
        headers = runner.signing_headers(
            path=self.path,
            body=body,
            key_id=self.key_id,
            secret=self.secret,
            timestamp=timestamp,
            nonce=nonce,
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers.items():
            if name not in {"Accept", "Content-Type"}:
                self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        nonce = self.headers["X-IC-Nonce"]
        timestamp = int(self.headers["X-IC-Timestamp"])
        expected_signature = runner.signature(
            method="POST",
            path=self.path,
            timestamp=timestamp,
            nonce=nonce,
            body=body,
            secret=self.secret,
        )
        if self.headers["X-IC-Signature"] != expected_signature:
            self._signed_response(
                401,
                {"error": {"code": "authentication_failed", "retryable": False}},
                nonce,
            )
            return

        case_id = self.headers["X-IC-Conformance-Case"]
        if case_id == "timeout":
            time.sleep(0.5)
            self._signed_response(
                200,
                {
                    "contract_version": "1",
                    "invocation_id": "pinv_conformance_timeout",
                    "status": "completed",
                    "outcome": "recognized",
                },
                nonce,
            )
            return
        if case_id == "replay" and nonce in self.claimed_nonces:
            self._signed_response(
                409,
                {"error": {"code": "replay_rejected", "retryable": False}},
                nonce,
            )
            return
        self.claimed_nonces.add(nonce)
        if case_id == "malformed":
            self._signed_response(
                400,
                {"error": {"code": "invalid_request", "retryable": False}},
                nonce,
            )
            return

        payload = json.loads(body)
        if case_id == "version_negotiation":
            self._signed_response(
                422,
                {
                    "error": {
                        "code": "unsupported_contract_version",
                        "retryable": False,
                    },
                    "supported_contract_versions": ["1"],
                },
                nonce,
            )
            return
        self._signed_response(
            200,
            {
                "contract_version": "1",
                "invocation_id": payload["invocation_id"],
                "status": "completed",
                "outcome": "recognized",
            },
            nonce,
        )


class ProviderConformanceRunnerTests(unittest.TestCase):
    fixture_path = CONFORMANCE_DIR / "fixtures" / "provider-contract-v1.json"

    def setUp(self):
        ConformingProviderHandler.claimed_nonces = set()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ConformingProviderHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_published_suite_contains_exactly_the_required_cases(self):
        suite = runner.load_suite(self.fixture_path)

        self.assertEqual({case["id"] for case in suite["cases"]}, runner.REQUIRED_CASES)

    def test_local_provider_passes_all_contract_cases(self):
        passed = runner.run_suite(
            base_url=f"http://127.0.0.1:{self.server.server_port}",
            fixture_path=self.fixture_path,
            key_id=ConformingProviderHandler.key_id,
            secret=ConformingProviderHandler.secret,
            timeout=0.1,
        )

        self.assertEqual(
            passed,
            ["success", "malformed", "replay", "version_negotiation", "timeout"],
        )

    def test_response_signature_failure_is_reported_without_body_content(self):
        result = runner.HTTPResult(
            status=200,
            headers={
                "content-type": "application/json",
                "x-ic-key-id": "test-key",
                "x-ic-timestamp": str(int(time.time())),
                "x-ic-nonce": "test-nonce",
                "x-ic-signature-version": runner.SIGNATURE_VERSION,
                "x-ic-signature": "invalid",
            },
            body=b'{"private_document_number":"GHA-PRIVATE"}',
        )

        with self.assertRaisesRegex(
            runner.ConformanceError, "signature is invalid"
        ) as caught:
            runner._verify_response_signature(
                result=result,
                path="/identitycore/conformance",
                nonce="test-nonce",
                key_id="test-key",
                secret="test-secret",
                case_id="success",
            )
        self.assertNotIn("GHA-PRIVATE", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
