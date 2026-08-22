import hashlib
import hmac
import json
import os
import time
import unittest
import uuid

from identitycore import (
    IdentityCoreAPIError,
    IdentityCoreClient,
    verify_webhook_signature,
)


@unittest.skipUnless(
    os.getenv("IDENTITYCORE_COMPAT_URL"), "live compatibility backend not configured"
)
class LiveCompatibilityTests(unittest.TestCase):
    def test_create_get_list_error_and_webhook(self):
        client = IdentityCoreClient(
            api_origin=os.environ["IDENTITYCORE_COMPAT_URL"],
            client_id=os.environ["IDENTITYCORE_COMPAT_CLIENT_ID"],
            client_secret=os.environ["IDENTITYCORE_COMPAT_CLIENT_SECRET"],
        )
        reference = f"python-{uuid.uuid4().hex}"
        created = client.verifications.create(
            purpose="SDK compatibility",
            policy_id=os.environ["IDENTITYCORE_COMPAT_POLICY_ID"],
            verification_subject={"full_name": "Python Compatibility"},
            external_reference=reference,
        )
        self.assertEqual(
            client.verifications.retrieve(created["id"])["id"], created["id"]
        )
        self.assertIn(
            created["id"],
            [
                item["id"]
                for item in client.verifications.iter(external_reference=reference)
            ],
        )
        with self.assertRaises(IdentityCoreAPIError) as error:
            client.verifications.retrieve("ver_does_not_exist")
        self.assertEqual(error.exception.status, 404)

        event_id = "evt_live_compatibility"
        payload = json.dumps(
            {"id": event_id, "schema_version": "1", "type": "verification.completed"},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        timestamp, secret = str(int(time.time())), "webhook-secret"
        signing_key = hashlib.sha256(secret.encode()).hexdigest().encode()
        signature = (
            "v1="
            + hmac.new(
                signing_key,
                timestamp.encode() + b"." + event_id.encode() + b"." + payload,
                hashlib.sha256,
            ).hexdigest()
        )
        self.assertTrue(
            verify_webhook_signature(
                payload,
                signature=signature,
                timestamp=timestamp,
                event_id=event_id,
                signing_key=secret,
            )
        )
