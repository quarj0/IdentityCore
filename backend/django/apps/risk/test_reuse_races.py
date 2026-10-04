from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, local
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
            if len(digests) > 1:
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

    def test_erasure_waits_for_inflight_fingerprint_collection_then_removes_all_rows(
        self,
    ):
        from apps.verification_subjects.services import request_subject_deletion

        case = self._case()
        role = local()
        collecting, erasing, finish_collection = Event(), Event(), Event()
        lock = reuse._lock_digests

        def controlled_lock(digests):
            if role.name == "collect" and len(digests) > 1:
                collecting.set()
                if not finish_collection.wait(10):
                    raise RuntimeError("Collection synchronization timed out")
            if role.name == "erase" and len(digests) == 1:
                erasing.set()
            lock(digests)

        def collect():
            close_old_connections()
            role.name = "collect"
            try:
                return reuse.collect_reuse(Verification.objects.get(pk=case.pk))
            finally:
                close_old_connections()

        def erase():
            close_old_connections()
            role.name = "erase"
            try:
                subject = (
                    Verification.objects.select_related("verification_subject")
                    .get(pk=case.pk)
                    .verification_subject
                )
                return request_subject_deletion(subject=subject)
            finally:
                close_old_connections()

        with patch("apps.risk.reuse._lock_digests", side_effect=controlled_lock):
            with ThreadPoolExecutor(max_workers=2) as executor:
                collection = executor.submit(collect)
                self.assertTrue(collecting.wait(10))
                deletion = executor.submit(erase)
                try:
                    self.assertTrue(erasing.wait(10))
                    self.assertFalse(deletion.done())
                finally:
                    finish_collection.set()
                self.assertEqual(collection.result(timeout=20)["status"], "completed")
                self.assertEqual(deletion.result(timeout=20)["status"], "completed")
        self.assertFalse(ReuseFingerprint.objects.filter(verification=case).exists())

    def test_collection_with_cached_subject_waits_for_erasure_and_rechecks_database(
        self,
    ):
        from apps.verification_subjects.services import request_subject_deletion

        case = self._case()
        stale = Verification.objects.select_related("verification_subject").get(
            pk=case.pk
        )
        role = local()
        erase_locked, collection_waiting, finish_erasure = Event(), Event(), Event()
        lock = reuse._lock_digests

        def controlled_lock(digests):
            if role.name == "collect":
                collection_waiting.set()
            lock(digests)
            if role.name == "erase":
                erase_locked.set()
                if not finish_erasure.wait(10):
                    raise RuntimeError("Erasure synchronization timed out")

        def erase():
            close_old_connections()
            role.name = "erase"
            try:
                return request_subject_deletion(
                    subject=Verification.objects.select_related("verification_subject")
                    .get(pk=case.pk)
                    .verification_subject
                )
            finally:
                close_old_connections()

        def collect():
            close_old_connections()
            role.name = "collect"
            try:
                return reuse.collect_reuse(stale)
            finally:
                close_old_connections()

        with patch("apps.risk.reuse._lock_digests", side_effect=controlled_lock):
            with ThreadPoolExecutor(max_workers=2) as executor:
                deletion = executor.submit(erase)
                self.assertTrue(erase_locked.wait(10))
                collection = executor.submit(collect)
                try:
                    self.assertTrue(collection_waiting.wait(10))
                    self.assertFalse(collection.done())
                finally:
                    finish_erasure.set()
                self.assertEqual(deletion.result(timeout=20)["status"], "completed")
                self.assertEqual(collection.result(timeout=20)["status"], "erased")
        self.assertFalse(ReuseFingerprint.objects.filter(verification=case).exists())
