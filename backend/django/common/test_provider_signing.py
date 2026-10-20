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

    def test_malformed_ascii_fields_fail_without_claiming_a_nonce(self):
        from unittest.mock import Mock

        for header, value in (
            ("X-IC-Nonce", "nonce-é"),
            ("X-IC-Nonce", "nonce\nother"),
            ("X-IC-Nonce", "x" * 257),
            ("X-IC-Signature", "é" * 64),
            ("X-IC-Signature", "f" * 63),
            ("X-IC-Key-Id", "key\nother"),
            ("X-IC-Timestamp", "١٧٠٠٠٠٠٠٠٠"),
        ):
            with self.subTest(header=header, value=value):
                headers = {**self.signed.headers(), header: value}
                claim = Mock(return_value=True)
                with self.assertRaises(ProviderSignatureError):
                    self.verify(headers=headers, claim_nonce=claim)
                claim.assert_not_called()

    def test_non_ascii_expected_nonce_is_a_controlled_error(self):
        with self.assertRaises(ProviderSignatureError):
            self.verify(expected_nonce="nonce-é")

    def test_rotating_key_id_does_not_allow_reusing_a_claimed_nonce(self):
        claimed = set()

        def claim(key, _ttl):
            if key in claimed:
                return False
            claimed.add(key)
            return True

        self.verify(claim_nonce=claim, replay_namespace="provider-one")
        rotated = sign_message(
            method="POST",
            path="/v1/check",
            body=self.body,
            key_id="current",
            secret="old-secret",
            timestamp=1_700_000_000,
            nonce="request-nonce",
        )
        with self.assertRaisesRegex(ProviderSignatureError, "already been used"):
            self.verify(
                headers=rotated.headers(),
                claim_nonce=claim,
                replay_namespace="provider-one",
            )

    def test_independent_provider_namespaces_can_claim_the_same_nonce(self):
        claimed = set()

        def claim(key, _ttl):
            if key in claimed:
                return False
            claimed.add(key)
            return True

        self.verify(claim_nonce=claim, replay_namespace="provider-one")
        self.verify(claim_nonce=claim, replay_namespace="provider-two")
        self.assertEqual(len(claimed), 2)

    def test_wire_fixtures_accept_numeric_and_unicode_runtime_variations(self):
        from common.provider_signing import derive_provider_signing_secret

        fixture = json.loads(
            (
                Path(__file__).resolve().parents[3]
                / "docs/fixtures/provider-signing-wire-v1.json"
            ).read_text()
        )
        secret = derive_provider_signing_secret(fixture["api_credential"])
        self.assertEqual(secret, fixture["derived_signing_secret"])
        for item in fixture["cases"]:
            with self.subTest(case=item["name"]):
                body = item["raw_body"].encode("utf-8")
                json.loads(body)
                signed = sign_message(
                    method=item["method"],
                    path=item["path"],
                    body=body,
                    key_id=item["key_id"],
                    secret=secret,
                    timestamp=item["timestamp"],
                    nonce=item["nonce"],
                )
                self.assertEqual(signed.signature, item["signature"])
                verified = verify_message(
                    method=item["method"],
                    path=item["path"],
                    body=body,
                    headers=signed.headers(),
                    keys={item["key_id"]: secret},
                    now=item["timestamp"] + 1,
                    expected_nonce=item["nonce"],
                    claim_nonce=lambda _key, _ttl: True,
                )
                self.assertEqual(verified.signature, item["signature"])
