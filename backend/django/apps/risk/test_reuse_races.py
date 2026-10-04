from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from apps.risk import reuse, tests as risk_tests
from apps.risk.models import ReuseFingerprint
from apps.risk import test_reuse as reuse_tests
from apps.verifications.models import Verification


@skipUnless(
    connection.vendor == "postgresql", "Fingerprint races require PostgreSQL locks"
)
class ReuseFingerprintRaceTests(TransactionTestCase):
    setUp = risk_tests.RiskDecisionTests.setUp
    _case = reuse_tests.ReuseSignalTests._case

    def test_simultaneous_matching_cases_cannot_both_miss_the_threshold(self):
        first, second = self._case(), self._case()
        barrier = Barrier(2)
        lock = reuse._lock_digests

        def synchronize(digests):
            barrier.wait(timeout=10)
            lock(digests)

        def run(pk):
            close_old_connections()
            try:
                return reuse.collect_reuse(Verification.objects.get(pk=pk))
            finally:
                close_old_connections()

        with patch("apps.risk.reuse._lock_digests", side_effect=synchronize):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(run, case.pk) for case in [first, second]]
                results = [future.result(timeout=20) for future in futures]
        self.assertEqual(sorted(len(result["signals"]) for result in results), [0, 4])
        self.assertEqual(ReuseFingerprint.objects.count(), 8)
