import hashlib
import hmac
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from identitycore import IdentityCoreAPIError, IdentityCoreClient, verify_webhook_signature


class FakeTransport:
    def __init__(self, responses): self.responses, self.calls = list(responses), []
    def __call__(self, method, url, headers, body, timeout):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body, "timeout": timeout})
        result = self.responses.pop(0)
        if isinstance(result, Exception): raise result
        return result


def envelope(data): return json.dumps({"success": True, "data": data, "request_id": "req_test"}).encode()
def failure(message): return json.dumps({"success": False, "error": {"code": "validation_error", "message": message, "details": {}}, "request_id": "req_test"}).encode()


class IdentityCoreClientTests(unittest.TestCase):
    def make_client(self, responses, **kwargs):
        self.transport = FakeTransport(responses)
        return IdentityCoreClient(api_origin="https://api.example.test", client_id="cli_test", client_secret="secret", transport=self.transport, sleep=lambda _: None, **kwargs)

    def test_auth_request_and_user_agent_headers(self):
        client = self.make_client([(200, envelope([]))])
        client.policies.list()
        headers = self.transport.calls[0]["headers"]
        self.assertEqual(headers["X-Client-Id"], "cli_test")
        self.assertEqual(headers["Authorization"], "Bearer secret")
        self.assertTrue(headers["X-Request-Id"].startswith("req_"))
        self.assertEqual(headers["User-Agent"], "identitycore-python/0.2.0")

    def test_create_includes_project_and_idempotency(self):
        client = self.make_client([(201, envelope({"id": "ver_123"}))])
        client.verifications.create(purpose="Onboarding", policy_id="pol_1", project_id="prj_1", verification_subject={"full_name": "Ama"}, idempotency_key="customer-1")
        call = self.transport.calls[0]
        self.assertEqual(call["headers"]["Idempotency-Key"], "customer-1")
        self.assertEqual(json.loads(call["body"])["project_id"], "prj_1")

    def test_get_retries_transient_response(self):
        client = self.make_client([(503, failure("Unavailable")), (200, envelope([]))])
        self.assertEqual(client.policies.list(), [])
        self.assertEqual(len(self.transport.calls), 2)

    def test_post_without_idempotency_does_not_retry(self):
        client = self.make_client([(503, failure("Unavailable")), (201, envelope({}))])
        with self.assertRaises(IdentityCoreAPIError):
            client.request("POST", "/unsafe-action", {})
        self.assertEqual(len(self.transport.calls), 1)

    def test_encodes_identifiers_used_in_api_paths(self):
        client = self.make_client([(200, envelope({}))])
        client.verifications.cancel("ver_1/../../policies?include=all")
        self.assertEqual(
            self.transport.calls[0]["url"],
            "https://api.example.test/api/v1/verifications/ver_1%2F..%2F..%2Fpolicies%3Finclude%3Dall/cancel",
        )

    def test_iterates_all_pages(self):
        client = self.make_client([
            (200, envelope({"results": [{"id": "1"}], "pagination": {"total_pages": 2}})),
            (200, envelope({"results": [{"id": "2"}], "pagination": {"total_pages": 2}})),
        ])
        self.assertEqual([x["id"] for x in client.verifications.iter()], ["1", "2"])

    def test_webhook_signature_and_tolerance(self):
        body, timestamp, key = b'{"id":"evt_1"}', "1000", "whsec_test"
        signature = "sha256=" + hmac.new(key.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_webhook_signature(body, signature=signature, timestamp=timestamp, signing_key=key, now=1001))
        self.assertFalse(verify_webhook_signature(body, signature=signature, timestamp=timestamp, signing_key=key, now=2000))


if __name__ == "__main__": unittest.main()
