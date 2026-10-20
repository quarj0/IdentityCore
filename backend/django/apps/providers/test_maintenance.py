from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.evidence.lifecycle import create_legal_hold, release_legal_hold
from apps.providers import test_operations as fixtures
from apps.providers.maintenance import reconcile_remote_action, retire_provider_records
from apps.providers.operations import accept_response
from apps.verification_subjects.services import request_subject_deletion


class ProviderMaintenanceTests(TestCase):
    create = fixtures.ProviderOperationTests.create
    invoke = fixtures.ProviderOperationTests.invoke
    pending = fixtures.ProviderOperationTests.pending
    completed = fixtures.ProviderOperationTests.completed
    _test_atomic_only = fixtures.ProviderOperationTests._test_atomic_only

    def setUp(self):
        fixtures.ProviderOperationTests.setUp(self)

    def acknowledge(self, *, expected_action="delete"):
        def response(**values):
            self.assertTrue(
                self._test_atomic_only(), "Remote control transport holds SQL locks"
            )
            self.assertEqual(values["payload"]["operation"], expected_action)
            self.assertNotIn("inputs", values["payload"])
            self.assertNotIn("Synthetic provider name", str(values["payload"]))
            return {
                "binding": values["payload"]["binding"],
                "status": "deleted" if expected_action == "delete" else "cancelled",
            }

        return patch(
            "apps.providers.maintenance.SecureHTTPProviderAdapter.post_json",
            side_effect=response,
        )

    def test_subject_erasure_scrubs_completed_provider_copy_and_tracks_remote_ack(self):
        record = self.pending()
        accept_response(record.public_id, self.completed(record))
        request_subject_deletion(subject=self.subject, actor=self.approver)
        record.refresh_from_db()
        self.assertEqual(record.result_json, {})
        self.assertEqual(record.result_sha256, "")
        self.assertEqual(record.remote_action, "delete")
        self.assertEqual(record.remote_action_status, "pending")
        with self.acknowledge():
            self.assertEqual(reconcile_remote_action(record.public_id), "acknowledged")
        record.refresh_from_db()
        self.assertEqual(record.lease_json, {})

    def test_hold_stops_processing_without_requesting_remote_destruction_until_released(
        self,
    ):
        record = self.pending()
        hold = create_legal_hold(
            tenant_id=self.tenant.pk,
            actor=self.approver,
            project_id=self.project.public_id,
            subject_id=self.subject.public_id,
            reason={"reference": "synthetic hold"},
        )
        self.assertEqual(
            request_subject_deletion(subject=self.subject, actor=self.approver)[
                "status"
            ],
            "deferred",
        )
        record.refresh_from_db()
        self.assertEqual(record.remote_action, "cancel")
        with self.acknowledge(expected_action="cancel"):
            self.assertEqual(reconcile_remote_action(record.public_id), "acknowledged")
        record.refresh_from_db()
        self.assertTrue(record.lease_json)
        with patch(
            "apps.providers.maintenance.timezone.now",
            return_value=record.delete_after + timedelta(days=2),
        ):
            self.assertEqual(
                retire_provider_records(tenant_id=self.tenant.pk)["operations"], 0
            )
        release_legal_hold(
            tenant_id=self.tenant.pk, actor=self.approver, hold_id=hold.public_id
        )
        self.assertEqual(
            request_subject_deletion(subject=self.subject, actor=self.approver)[
                "status"
            ],
            "completed",
        )
        record.refresh_from_db()
        self.assertEqual(record.remote_action, "delete")
        # A previous cancel attempt cannot delay the new privacy deletion request.
        with patch(
            "apps.providers.maintenance.timezone.now",
            return_value=timezone.now() + timedelta(minutes=6),
        ), self.acknowledge():
            self.assertEqual(reconcile_remote_action(record.public_id), "acknowledged")

    def test_remote_failure_is_durable_and_does_not_restore_locally_erased_data(self):
        record = self.pending()
        request_subject_deletion(subject=self.subject, actor=self.approver)
        with patch(
            "apps.providers.maintenance.SecureHTTPProviderAdapter.post_json",
            side_effect=RuntimeError("sensitive provider details"),
        ):
            self.assertEqual(reconcile_remote_action(record.public_id), "pending")
        record.refresh_from_db()
        self.assertEqual(record.result_json, {})
        self.assertEqual(record.remote_action_status, "pending")
        self.assertIsNotNone(record.remote_attempted_at)
        with patch(
            "apps.providers.maintenance.timezone.now",
            return_value=timezone.now() + timedelta(minutes=6),
        ), self.acknowledge():
            self.assertEqual(reconcile_remote_action(record.public_id), "acknowledged")

    def test_expired_remote_cleanup_clears_capability_without_fabricating_acknowledgement(
        self,
    ):
        record = self.pending()
        request_subject_deletion(subject=self.subject, actor=self.approver)
        record.refresh_from_db()
        with patch(
            "apps.providers.maintenance.timezone.now",
            return_value=record.remote_requested_at + timedelta(days=31),
        ):
            self.assertEqual(reconcile_remote_action(record.public_id), "expired")
        record.refresh_from_db()
        self.assertEqual(record.lease_json, {})
        self.assertEqual(record.remote_action_status, "expired")

    def test_retention_scrubs_provider_result_and_expired_certification_report(self):
        record = self.pending()
        accept_response(record.public_id, self.completed(record))
        with patch(
            "apps.providers.maintenance.timezone.now",
            return_value=record.delete_after + timedelta(days=3),
        ):
            result = retire_provider_records(tenant_id=self.tenant.pk, limit=1)
        self.assertEqual(result["operations"], 1)
        self.assertEqual(result["certifications"], 1)
        record.refresh_from_db()
        self.assertEqual(record.result_json, {})
        receipt = self.config.certifications.get()
        self.assertEqual(receipt.report_json, {})
        self.assertIsNotNone(receipt.deleted_at)
