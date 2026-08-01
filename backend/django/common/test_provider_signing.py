import json
from pathlib import Path

from unittest import TestCase

from common.provider_signing import (
    ProviderSignatureError,
    canonical_json,
    canonical_message,
    sign_message,
    verify_message,
)


class ProviderSigningTests(TestCase):
    def setUp(self):
        self.body = canonical_json({"result": "ok", "score": 0.98})
        self.signed = sign_message(
            method="POST",
            path="/v1/check",
            body=self.body,
            key_id="next",
            secret="rotated-secret",
            timestamp=1_700_000_000,
            nonce="request-nonce",
        )

    def verify(self, **overrides):
        arguments = {
            "method": "POST",
            "path": "/v1/check",
            "body": self.body,
            "headers": self.signed.headers(),
            "keys": {"current": "old-secret", "next": "rotated-secret"},
            "now": 1_700_000_001,
            "expected_nonce": "request-nonce",
            "claim_nonce": lambda _key, _ttl: True,
        }
        arguments.update(overrides)
        return verify_message(**arguments)

    def test_accepts_an_active_rotated_key(self):
        self.assertEqual(self.verify().key_id, "next")

    def test_rejects_stale_response(self):
        with self.assertRaisesRegex(ProviderSignatureError, "stale"):
            self.verify(now=1_700_000_301)

    def test_rejects_response_bound_to_another_request(self):
        with self.assertRaisesRegex(ProviderSignatureError, "not bound"):
            self.verify(expected_nonce="another-nonce")

    def test_rejects_replay(self):
        with self.assertRaisesRegex(ProviderSignatureError, "already been used"):
            self.verify(claim_nonce=lambda _key, _ttl: False)

    def test_rejects_tampering(self):
        with self.assertRaisesRegex(ProviderSignatureError, "invalid"):
            self.verify(body=b'{"result":"failed"}')

    def test_published_fixture_matches(self):
        fixture_path = (
            Path(__file__).resolve().parents[3]
            / "docs/fixtures/provider-signing-v1.json"
        )
        with fixture_path.open(encoding="utf-8") as fixture:
            item = json.load(fixture)
        body = canonical_json(item["body"])
        canonical = canonical_message(
            method=item["method"],
            path=item["path"],
            timestamp=item["timestamp"],
            nonce=item["nonce"],
            body=body,
        )
        self.assertEqual(body.decode(), item["canonical_body"])
        self.assertEqual(canonical.decode(), item["canonical_message"])
        self.assertEqual(
            sign_message(
                method=item["method"],
                path=item["path"],
                body=body,
                key_id=item["key_id"],
                secret=item["secret"],
                timestamp=item["timestamp"],
                nonce=item["nonce"],
            ).signature,
            item["signature"],
        )
