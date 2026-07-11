import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from identitycore import IdentityCoreAPIError, IdentityCoreClient


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
                "timeout": timeout,
            }
        )
        return self.responses.pop(0)


def envelope(data, request_id="req_test"):
    return json.dumps({"success": True, "data": data, "request_id": request_id}).encode()


def failure(message, code="validation_error", details=None, request_id="req_test"):
    return json.dumps(
        {
            "success": False,
            "error": {"code": code, "message": message, "details": details or {}},
            "request_id": request_id,
        }
    ).encode()


class IdentityCoreClientTests(unittest.TestCase):
    def make_client(self, responses):
        self.transport = FakeTransport(responses)
        return IdentityCoreClient(
            api_origin="https://api.example.test",
            client_id="cli_test",
            client_secret="secret",
            transport=self.transport,
        )

    def test_sends_api_client_auth_headers(self):
        client = self.make_client([(200, envelope([{"id": "pol_123"}]))])

        policies = client.policies.list()

        self.assertEqual(policies, [{"id": "pol_123"}])
        call = self.transport.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["url"], "https://api.example.test/api/v1/policies/")
        self.assertEqual(call["headers"]["X-Client-Id"], "cli_test")
        self.assertEqual(call["headers"]["Authorization"], "Bearer secret")

    def test_create_verification_uses_expected_path_and_payload(self):
        client = self.make_client([(201, envelope({"id": "ver_123"}))])

        response = client.verifications.create(
            purpose="Customer onboarding",
            policy_id="pol_123",
            verification_subject={"full_name": "Kwame Mensah"},
            external_reference="customer_123",
        )

        self.assertEqual(response["id"], "ver_123")
        call = self.transport.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.example.test/api/v1/verifications/")
        self.assertEqual(
            json.loads(call["body"].decode()),
            {
                "purpose": "Customer onboarding",
                "policy_id": "pol_123",
                "verification_subject": {"full_name": "Kwame Mensah"},
                "external_reference": "customer_123",
                "redirect_url": "",
                "metadata": {},
            },
        )

    def test_error_envelope_raises_api_error(self):
        client = self.make_client(
            [(400, failure("Choose an active verification template.", details={"policy_id": ["Required."]}))]
        )

        with self.assertRaises(IdentityCoreAPIError) as raised:
            client.verifications.create(
                purpose="Customer onboarding",
                policy_id="",
                verification_subject={"full_name": "Kwame Mensah"},
            )

        self.assertEqual(raised.exception.status, 400)
        self.assertEqual(raised.exception.code, "validation_error")
        self.assertEqual(raised.exception.request_id, "req_test")
        self.assertIn("policy_id", raised.exception.details)

    def test_invalid_json_is_human_readable(self):
        client = self.make_client([(502, b"InvalidTag")])

        with self.assertRaises(IdentityCoreAPIError) as raised:
            client.policies.list()

        self.assertEqual(
            raised.exception.message,
            "The service is temporarily unavailable. Please try again shortly.",
        )
        self.assertEqual(raised.exception.code, "invalid_response")

    def test_verification_helpers_use_expected_paths(self):
        client = self.make_client(
            [
                (200, envelope({"results": []})),
                (200, envelope({"id": "ver_123"})),
                (200, envelope({"status": "cancelled"})),
                (200, envelope({"verification_url": "https://verify.example"})),
                (200, envelope({"download_url": "https://evidence.example"})),
            ]
        )

        client.verifications.list(status="verified", page=2, page_size=10)
        client.verifications.retrieve("ver_123")
        client.verifications.cancel("ver_123", reason="Duplicate")
        client.verifications.resend_link("ver_123")
        client.verifications.evidence_report("ver_123")

        self.assertEqual(
            [call["url"] for call in self.transport.calls],
            [
                "https://api.example.test/api/v1/verifications/?status=verified&page=2&page_size=10",
                "https://api.example.test/api/v1/verifications/ver_123",
                "https://api.example.test/api/v1/verifications/ver_123/cancel",
                "https://api.example.test/api/v1/verifications/ver_123/resend-link",
                "https://api.example.test/api/v1/verifications/ver_123/evidence-report",
            ],
        )


if __name__ == "__main__":
    unittest.main()
