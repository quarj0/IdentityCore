from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest import skipUnless

from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from apps.identity_documents import tests as document_fixtures
from apps.identity_documents.models import IdentityDocument
from apps.verification_subjects.services import request_subject_deletion
from apps.verifications.models import ProcessingJob, Verification
from apps.verifications.processing_jobs import (
    acquire_processing_job,
    lock_processing_job_for_finalization,
    ProcessingJobOwnershipLost,
)


@skipUnless(connection.vendor == "postgresql", "Privacy races require PostgreSQL locks")
class SubjectDeletionRaceTests(TransactionTestCase):
    setUp = document_fixtures.IdentityDocumentTaskTests.setUp

    def test_erasure_blocks_late_provider_result_from_restoring_personal_data(self):
        owner = acquire_processing_job(
            job_type="identity_document", resource=self.identity_document
        )
        ready, erased = Event(), Event()

        def late_result():
            close_old_connections()
            try:
                ready.set()
                if not erased.wait(10):
                    raise AssertionError("Deletion did not finish")
                with transaction.atomic():
                    lock_processing_job_for_finalization(owner)
                    document = IdentityDocument.objects.get(pk=self.identity_document.pk)
                    document.extracted_data_json = {"full_name": "Restored private data"}
                    document.save(update_fields=["extracted_data_json"])
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(late_result)
            self.assertTrue(ready.wait(10))
            try:
                self.assertEqual(
                    request_subject_deletion(subject=self.subject)["status"],
                    "completed",
                )
            finally:
                erased.set()
            with self.assertRaises(ProcessingJobOwnershipLost):
                result.result(timeout=15)
        self.identity_document.refresh_from_db()
        self.assertEqual(self.identity_document.extracted_data_json, {})
        self.assertEqual(
            ProcessingJob.objects.get(pk=owner.pk).error_code, "subject_deleted"
        )

    def test_erasure_waits_for_started_finalization_then_clears_its_result(self):
        owner = acquire_processing_job(
            job_type="identity_document", resource=self.identity_document
        )
        finalizing, attempted, release = Event(), Event(), Event()

        def finalize():
            close_old_connections()
            try:
                with transaction.atomic():
                    lock_processing_job_for_finalization(owner)
                    document = IdentityDocument.objects.get(
                        pk=self.identity_document.pk
                    )
                    document.extracted_data_json = {"full_name": "Private result"}
                    document.save(update_fields=["extracted_data_json"])
                    finalizing.set()
                    if not release.wait(10):
                        raise AssertionError("Finalizer release not signalled")
            finally:
                close_old_connections()

        def erase():
            close_old_connections()
            try:
                attempted.set()
                return request_subject_deletion(subject=self.subject)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            finalized = pool.submit(finalize)
            self.assertTrue(finalizing.wait(10))
            deletion = pool.submit(erase)
            try:
                self.assertTrue(attempted.wait(10))
                self.assertFalse(deletion.done())
            finally:
                release.set()
            finalized.result(timeout=15)
            self.assertEqual(deletion.result(timeout=15)["status"], "completed")
        self.identity_document.refresh_from_db()
        self.assertEqual(self.identity_document.extracted_data_json, {})
        self.assertEqual(
            Verification.objects.get(pk=self.verification.pk).status, "cancelled"
        )
