from unittest.mock import patch
from django.test import SimpleTestCase
from common import credential_proofs as proofs


class CredentialProofTests(SimpleTestCase):
    def setUp(self):
        proofs._PROOFS.clear()

    @patch.object(proofs, "check_password", return_value=True)
    def test_success_reuses_proof_but_rotation_rechecks(self, check):
        self.assertTrue(proofs.verify_bearer_secret("secret", "hash-one"))
        self.assertTrue(proofs.verify_bearer_secret("secret", "hash-one"))
        self.assertEqual(check.call_count, 1)
        self.assertTrue(proofs.verify_bearer_secret("secret", "hash-two"))
        self.assertEqual(check.call_count, 2)
        self.assertTrue(
            all(isinstance(key, bytes) and len(key) == 32 for key in proofs._PROOFS)
        )

    @patch.object(proofs, "check_password", return_value=False)
    def test_failures_never_cached(self, check):
        self.assertFalse(proofs.verify_bearer_secret("wrong", "hash"))
        self.assertFalse(proofs.verify_bearer_secret("wrong", "hash"))
        self.assertEqual(check.call_count, 2)
        self.assertFalse(proofs._PROOFS)

    @patch.object(proofs, "check_password", return_value=True)
    def test_expiry_and_capacity_force_reverification(self, check):
        with patch.object(proofs, "_MAX_PROOFS", 1):
            self.assertTrue(proofs.verify_bearer_secret("one", "hash"))
            self.assertTrue(proofs.verify_bearer_secret("two", "hash"))
            self.assertEqual(len(proofs._PROOFS), 1)
            self.assertTrue(proofs.verify_bearer_secret("one", "hash"))
            self.assertEqual(check.call_count, 3)
        with patch.object(proofs.time, "monotonic", return_value=10**15):
            self.assertTrue(proofs.verify_bearer_secret("one", "hash"))
        self.assertEqual(check.call_count, 4)

    def test_generated_tokens_use_constant_time_digest_verification(self):
        import secrets

        token = secrets.token_urlsafe(32)
        encoded = proofs.hash_generated_bearer(token)
        self.assertNotIn(token, encoded)
        self.assertTrue(proofs.verify_bearer_secret(token, encoded))
        self.assertFalse(proofs.verify_bearer_secret(token + "wrong", encoded))
        self.assertFalse(proofs.verify_bearer_secret(encoded, encoded))
        with self.assertRaises(ValueError):
            proofs.hash_generated_bearer("human-password")

    def test_concurrent_first_use_performs_one_expensive_check(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        import time

        start = Barrier(8)

        def slow_check(*args):
            time.sleep(0.03)
            return True

        def verify(_):
            start.wait(timeout=5)
            return proofs.verify_bearer_secret("secret", "encoded")

        with patch.object(proofs, "check_password", side_effect=slow_check) as check:
            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertTrue(all(pool.map(verify, range(8))))
            self.assertEqual(check.call_count, 1)
