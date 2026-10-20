"""PostgreSQL serialization between new sessions and profile erasure."""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verification_subjects.services import request_subject_deletion
from apps.verifications.models import Verification, VerificationSession
from apps.verifications.serializers import VerificationCreateSerializer


@skipUnless(connection.vendor == "postgresql", "Creation/erasure races need PostgreSQL")
class SubjectCreationRaceTests(TransactionTestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Privacy race", slug="privacy-race", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Privacy race",
            slug="privacy-race",
            status="active",
        )
        self.reference = "existing-customer"
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            external_reference=self.reference,
            full_name="Original profile",
        )

    def create_case(self):
        serializer = VerificationCreateSerializer(
            data={
                "purpose": "Onboarding",
                "external_reference": self.reference,
                "verification_subject": {"full_name": "Fresh profile"},
            },
            context={
                "request": SimpleNamespace(tenant=self.tenant, user=AnonymousUser())
            },
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            return serializer.save()

    def worker(self, callback, ready=None, pid=None):
        close_old_connections()
        try:
            connection.ensure_connection()
            if pid is not None:
                pid.append(connection.connection.info.backend_pid)
            if ready is not None:
                ready.set()
            return callback()
        finally:
            close_old_connections()

    def assert_waiting_for_lock(self, future, pid):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not future.done():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", [pid]
                )
                row = cursor.fetchone()
            if row and row[0] == "Lock":
                return
            time.sleep(0.02)
        self.fail(
            "Competing transaction did not wait for the privacy serialization lock"
        )

    def test_creation_first_is_included_in_erasure_snapshot(self):
        selected, release, attempted = Event(), Event(), Event()
        deleting_pid = []
        original_create = Verification.objects.create

        def pause_before_insert(**values):
            selected.set()
            if not release.wait(10):
                raise AssertionError("Creation release not signalled")
            return original_create(**values)

        with patch.object(
            Verification.objects, "create", side_effect=pause_before_insert
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                creation = pool.submit(self.worker, self.create_case)
                self.assertTrue(selected.wait(10))
                deletion = pool.submit(
                    self.worker,
                    lambda: request_subject_deletion(subject=self.subject),
                    attempted,
                    deleting_pid,
                )
                try:
                    self.assertTrue(attempted.wait(10))
                    self.assert_waiting_for_lock(deletion, deleting_pid[0])
                finally:
                    release.set()
                case = creation.result(timeout=15)
                self.assertEqual(deletion.result(timeout=15)["status"], "completed")
        case.refresh_from_db()
        self.subject.refresh_from_db()
        self.assertEqual(case.verification_subject_id, self.subject.pk)
        self.assertEqual(case.status, "cancelled")
        self.assertIsNotNone(self.subject.deleted_at)
        self.assertEqual(
            VerificationSession.objects.get(verification=case).status, "revoked"
        )

    def test_erasure_first_does_not_attach_session_to_deleted_profile(self):
        erasing, release, attempted = Event(), Event(), Event()
        creating_pid = []
        original_save = VerificationSubject.save

        def pause_before_erasure_save(subject, *args, **kwargs):
            if subject.pk == self.subject.pk and subject.deleted_at is not None:
                erasing.set()
                if not release.wait(10):
                    raise AssertionError("Erasure release not signalled")
            return original_save(subject, *args, **kwargs)

        with patch.object(VerificationSubject, "save", pause_before_erasure_save):
            with ThreadPoolExecutor(max_workers=2) as pool:
                deletion = pool.submit(
                    self.worker, lambda: request_subject_deletion(subject=self.subject)
                )
                self.assertTrue(erasing.wait(10))
                creation = pool.submit(
                    self.worker, self.create_case, attempted, creating_pid
                )
                try:
                    self.assertTrue(attempted.wait(10))
                    self.assert_waiting_for_lock(creation, creating_pid[0])
                finally:
                    release.set()
                self.assertEqual(deletion.result(timeout=15)["status"], "completed")
                case = creation.result(timeout=15)
        self.subject.refresh_from_db()
        self.assertIsNotNone(self.subject.deleted_at)
        self.assertNotEqual(case.verification_subject_id, self.subject.pk)
        self.assertIsNone(case.verification_subject.deleted_at)
        self.assertEqual(case.verification_subject.full_name, "Fresh profile")
        self.assertEqual(case.status, "pending_consent")
        self.assertFalse(self.subject.verifications.exists())
        self.assertEqual(
            VerificationSession.objects.get(verification=case).status, "created"
        )
