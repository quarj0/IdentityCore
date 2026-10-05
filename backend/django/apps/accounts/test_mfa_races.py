from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from apps.accounts import tests as fixtures
from apps.accounts.mfa import (
    enable_mfa,
    generate_secret,
    issue_mfa_token,
    totp,
    verify_login_challenge,
)
from apps.accounts.models import MFARecoveryCode


@skipUnless(connection.vendor == "postgresql", "PostgreSQL MFA transaction locks")
class MFATransactionRaceTests(TransactionTestCase):
    setUp = fixtures.MFAEndpointTests.setUp

    def test_two_live_proofs_cannot_use_the_same_totp_step(self):
        secret = generate_secret()
        enable_mfa(self.user, secret)
        proofs = [issue_mfa_token(self.user, purpose="challenge") for _ in range(2)]
        code = totp(secret)
        barrier = Barrier(2)

        def verify(proof):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return verify_login_challenge(self.user, proof, code)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(verify, proofs))
        self.assertCountEqual(results, ["totp", None])
        self.user.refresh_from_db()
        self.assertEqual(len(self.user.mfa_config_json["consumed_challenges"]), 1)

    def test_one_proof_cannot_consume_two_distinct_recovery_codes(self):
        codes = enable_mfa(self.user, generate_secret())
        proof = issue_mfa_token(self.user, purpose="challenge")
        barrier = Barrier(2)

        def verify(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return index, verify_login_challenge(self.user, proof, codes[index])
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(verify, (0, 1)))
        self.assertCountEqual(
            [method for _, method in results], ["recovery_code", None]
        )
        self.assertEqual(
            MFARecoveryCode.objects.filter(used_at__isnull=False).count(), 1
        )
        unused = next(index for index, method in results if method is None)
        fresh = issue_mfa_token(self.user, purpose="challenge")
        self.assertEqual(
            verify_login_challenge(self.user, fresh, codes[unused]), "recovery_code"
        )
