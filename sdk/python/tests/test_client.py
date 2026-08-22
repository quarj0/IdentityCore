import json
import socket
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from identitycore import (
    IdentityCoreAPIError,
    IdentityCoreClient,
    verify_webhook_signature,
)


class FakeTransport:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

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
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def envelope(data):
    return json.dumps(
        {"success": True, "data": data, "request_id": "req_test"}
    ).encode()


def failure(message):
    return json.dumps(
        {
            "success": False,
            "error": {"code": "validation_error", "message": message, "details": {}},
            "request_id": "req_test",
        }
    ).encode()


class IdentityCoreClientTests(unittest.TestCase):
    def make_client(self, responses, **kwargs):
        self.transport = FakeTransport(responses)
        return IdentityCoreClient(
            api_origin="https://api.example.test",
            client_id="cli_test",
            client_secret="secret",
            transport=self.transport,
            sleep=lambda _: None,
            **kwargs,
        )

    def test_auth_request_and_user_agent_headers(self):
        client = self.make_client([(200, envelope([]))])
        client.policies.list()
        headers = self.transport.calls[0]["headers"]
        self.assertEqual(headers["X-Client-Id"], "cli_test")
        self.assertEqual(headers["Authorization"], "Bearer secret")
        self.assertTrue(headers["X-Request-Id"].startswith("req_"))
        self.assertEqual(headers["User-Agent"], "identitycore-python/0.2.0")

    def test_access_token_omits_saved_client_identifier(self):
        transport = FakeTransport([(200, envelope([])), (200, b"binary evidence")])
        client = IdentityCoreClient(
            api_origin="https://api.example.test",
            client_id="cli_saved",
            client_secret="saved-secret",
            access_token="user-token",
            transport=transport,
            sleep=lambda _: None,
        )

        client.policies.list()
        client.download("/verifications/ver_1/evidence-report/download")

        for call in transport.calls:
            self.assertEqual(call["headers"]["Authorization"], "Bearer user-token")
            self.assertNotIn("X-Client-Id", call["headers"])

    def test_create_includes_project_and_idempotency(self):
        client = self.make_client([(201, envelope({"id": "ver_123"}))])
        client.verifications.create(
            purpose="Onboarding",
            policy_id="pol_1",
            project_id="prj_1",
            verification_subject={"full_name": "Ama"},
            idempotency_key="customer-1",
        )
        call = self.transport.calls[0]
        self.assertEqual(call["headers"]["Idempotency-Key"], "customer-1")
        self.assertEqual(json.loads(call["body"])["project_id"], "prj_1")

    def test_get_retries_transient_response(self):
        client = self.make_client([(503, failure("Unavailable")), (200, envelope([]))])
        self.assertEqual(client.policies.list(), [])
        self.assertEqual(len(self.transport.calls), 2)

    def test_binary_download_retries_network_and_transient_failures(self):
        client = self.make_client(
            [
                socket.timeout("temporary"),
                (503, failure("Unavailable")),
                (200, b"evidence"),
            ]
        )

        self.assertEqual(client.download("/evidence"), b"evidence")
        self.assertEqual(len(self.transport.calls), 3)

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

    def test_retrieves_versioned_verification_result(self):
        client = self.make_client([(200, envelope({"schema_version": "1"}))])

        self.assertEqual(client.verifications.result("ver_1")["schema_version"], "1")
        self.assertEqual(
            self.transport.calls[0]["url"],
            "https://api.example.test/api/v1/verifications/ver_1/result",
        )

    def test_iterates_all_pages(self):
        client = self.make_client(
            [
                (
                    200,
                    envelope(
                        {
                            "results": [{"id": "1"}],
                            "pagination": {"next_cursor": "next"},
                        }
                    ),
                ),
                (
                    200,
                    envelope(
                        {"results": [{"id": "2"}], "pagination": {"next_cursor": None}}
                    ),
                ),
            ]
        )
        self.assertEqual([x["id"] for x in client.verifications.iter()], ["1", "2"])
        self.assertIn("cursor=next", self.transport.calls[1]["url"])

    def test_webhook_signature_and_tolerance(self):
        fixture = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "fixtures/webhook-signature-v1.json"
            ).read_text()
        )
        seen: set[str] = set()

        def claim_event_id(event_id: str) -> bool:
            if event_id in seen:
                return False
            seen.add(event_id)
            return True

        self.assertTrue(
            verify_webhook_signature(
                fixture["raw_body"].encode(),
                signature=fixture["rotation_signature_header"],
                timestamp=fixture["timestamp"],
                event_id=fixture["event_id"],
                signing_keys=[fixture["previous_secret"]],
                now=fixture["now_within_tolerance"],
                claim_event_id=claim_event_id,
            )
        )
        self.assertIn(fixture["event_id"], seen)
        self.assertFalse(
            verify_webhook_signature(
                fixture["raw_body"],
                signature=fixture["previous_signature"],
                timestamp=fixture["timestamp"],
                event_id=fixture["event_id"],
                signing_keys=[fixture["current_secret"], fixture["previous_secret"]],
                now=fixture["now_within_tolerance"],
                claim_event_id=claim_event_id,
            )
        )
        self.assertFalse(
            verify_webhook_signature(
                fixture["raw_body"],
                signature=fixture["current_signature"],
                timestamp=fixture["timestamp"],
                event_id=fixture["event_id"],
                signing_key=fixture["current_secret"],
                now=fixture["now_outside_tolerance"],
            )
        )
        valid_options = {
            "timestamp": fixture["timestamp"],
            "event_id": fixture["event_id"],
            "signing_key": fixture["current_secret"],
            "now": fixture["now_within_tolerance"],
        }
        self.assertTrue(
            verify_webhook_signature(
                fixture["raw_body"],
                signature=fixture["rotation_signature_header"],
                **valid_options,
            )
        )
        self.assertTrue(
            verify_webhook_signature(
                fixture["raw_body"],
                signature=fixture["legacy_signature"],
                timestamp=fixture["timestamp"],
                signing_key=fixture["legacy_signing_key"],
                now=fixture["now_within_tolerance"],
            )
        )
        self.assertTrue(
            verify_webhook_signature(
                fixture["raw_body"],
                signature=fixture["current_signature"],
                **valid_options,
            )
        )
        self.assertFalse(
            verify_webhook_signature(
                fixture["raw_body"],
                signature=fixture["current_signature"].replace("v1=", "v2="),
                **valid_options,
            )
        )
        self.assertFalse(
            verify_webhook_signature(
                fixture["raw_body"],
                signature=fixture["current_signature"],
                **{**valid_options, "event_id": "evt_other"},
            )
        )
        self.assertFalse(
            verify_webhook_signature(
                fixture["raw_body"] + " ",
                signature=fixture["current_signature"],
                **valid_options,
            )
        )
        self.assertFalse(
            verify_webhook_signature(
                fixture["non_object_raw_body"],
                signature=fixture["non_object_signature"],
                **valid_options,
            )
        )
        self.assertFalse(
            verify_webhook_signature(
                fixture["invalid_schema_raw_body"],
                signature=fixture["invalid_schema_signature"],
                **valid_options,
            )
        )


if __name__ == "__main__":
    unittest.main()
