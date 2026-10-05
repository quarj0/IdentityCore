from datetime import timedelta
from unittest.mock import Mock, patch
from io import StringIO
from django.core.management import call_command, CommandError
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import connection, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from apps.audit.models import AuditEvent
from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.consent.models import ConsentRecord, ConsentTemplate
from apps.consent.services import active_consent, withdraw
from apps.consent.test_helpers import accept_test_consent
from apps.verifications import tests as fixtures
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobType,
    VerificationSession,
)
from apps.providers.services import create_provider_check, invoke_provider_check


class PortalConsentBoundaryTests(APITestCase):
    from apps.verification_sessions import tests as portal_fixtures

    setUp = portal_fixtures.VerificationSessionPortalTests.setUp
    session_headers = portal_fixtures.VerificationSessionPortalTests.session_headers

    def test_liveness_and_challenges_require_active_biometric_scope(self):
        template = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Document only",
            content="Document only",
            evidence_scope_json=["document"],
        )
        ConsentRecord.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            consent_template=template,
            consent_text_snapshot=template.content,
            accepted_at=timezone.now(),
        )
        for name in (
            "verification-session-liveness",
            "verification-session-liveness-challenge",
        ):
            response = self.client.post(
                reverse(name, kwargs={"session_id": self.session.public_id}),
                {},
                format="json",
                **self.session_headers(),
            )
            self.assertEqual(response.status_code, 400)
        self.assertFalse(self.verification.liveness_checks.exists())
        self.assertFalse(self.verification.provider_checks.exists())

    def test_withdrawal_after_authentication_prevents_artifact_creation(self):
        from apps.verification_sessions.views import require_verification_session_action

        record = accept_test_consent(self.verification)

        def withdraw_after_authentication(request, action):
            require_verification_session_action(request, action)
            withdraw(record)

        with patch(
            "apps.verification_sessions.views.require_verification_session_action",
            side_effect=withdraw_after_authentication,
        ):
            response = self.client.post(
                reverse(
                    "verification-session-liveness",
                    kwargs={"session_id": self.session.public_id},
                ),
                {},
                format="json",
                **self.session_headers(),
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.verification.liveness_checks.exists())
        self.assertFalse(self.verification.provider_checks.exists())


class ConsentPurposeTests(TestCase):
    setUp = fixtures.ManualReviewOwnershipTests.setUp
    _create_case = fixtures.ManualReviewOwnershipTests._create_case

    def test_acceptance_uses_scope_and_template_from_the_displayed_locale(self):
        from types import SimpleNamespace
        from apps.verification_sessions.serializers import (
            VerificationSessionConsentSerializer,
        )
        from apps.verifications.models import VerificationStatus

        self.tenant_case.status = VerificationStatus.PENDING_CONSENT
        self.tenant_case.policy_snapshot_json = {
            "supported_locales": ["en", "fr"],
            "default_locale": "fr",
        }
        self.tenant_case.save(update_fields=["status", "policy_snapshot_json"])
        french = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="French",
            version=1,
            language="fr",
            content="Document only",
            status="active",
            evidence_scope_json=["document"],
        )
        ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="English",
            version=9,
            language="en",
            content="Document and biometrics",
            status="active",
            evidence_scope_json=["document", "biometrics"],
        )
        session = VerificationSession.objects.create(
            tenant=self.tenant,
            verification=self.tenant_case,
            session_token_hash="synthetic",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        request = SimpleNamespace(
            verification_session=session,
            headers={"Accept-Language": "fr"},
            query_params={},
            META={},
        )
        serializer = VerificationSessionConsentSerializer(
            data={"accepted": True}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        self.assertEqual(record.consent_template_id, french.pk)
        self.assertEqual(record.proof_json["evidence_scope"], ["document"])
        self.assertIsNone(active_consent(self.tenant_case, "biometrics"))

    def test_only_platform_onboarding_can_process_while_tenant_is_pending(self):
        accept_test_consent(self.platform_case)
        accept_test_consent(self.tenant_case)
        for tenant_status in ("pending", "pending_review", "suspended", "closed"):
            self.tenant.status = tenant_status
            self.tenant.save(update_fields=["status"])
            self.assertIsNone(active_consent(self.tenant_case))
            if tenant_status in {"pending", "pending_review"}:
                self.assertIsNotNone(active_consent(self.platform_case))
            else:
                self.assertIsNone(active_consent(self.platform_case))
        self.tenant.status = "pending_review"
        self.tenant.save(update_fields=["status"])
        self.tenant_case.metadata_json = {"workflow": "administrator_onboarding"}
        self.tenant_case.save(update_fields=["metadata_json"])
        self.assertIsNone(active_consent(self.tenant_case))

    def _make_legacy(self, record, *, content_hash=None):
        # Simulate persisted rows from the old schema without opening a mutation
        # bypass in the production manager.
        quote = connection.ops.quote_name
        sql = f"UPDATE {quote(ConsentRecord._meta.db_table)} SET proof_json = NULL"
        params = []
        if content_hash is not None:
            sql += ", consent_content_hash = %s"
            params.append(content_hash)
        sql += " WHERE id = %s"
        params.append(record.pk)
        with connection.cursor() as cursor:
            cursor.execute(sql, params)

    def test_bulk_mutation_and_deletion_cannot_erase_or_reactivate_proof(self):
        record = withdraw(accept_test_consent(self.tenant_case))
        for operation in (
            lambda: ConsentRecord.objects.bulk_create(
                [record],
                update_conflicts=True,
                update_fields=["withdrawn_at"],
                unique_fields=["pk"],
            ),
            lambda: ConsentRecord.objects.filter(pk=record.pk).update(
                withdrawn_at=None
            ),
            lambda: ConsentRecord.objects.filter(pk=record.pk).update(
                consent_text_snapshot="Changed notice"
            ),
            lambda: ConsentRecord.objects.filter(pk=record.pk).delete(),
            record.delete,
        ):
            with self.assertRaises(ValidationError), transaction.atomic():
                operation()
        record.withdrawn_at = None
        with self.assertRaises(ValidationError), transaction.atomic():
            ConsentRecord.objects.bulk_update([record], ["withdrawn_at"])
        record.refresh_from_db()
        self.assertIsNotNone(record.withdrawn_at)
        self.assertIsNone(active_consent(self.tenant_case))

    def test_proof_freezes_context_and_cannot_be_rewritten(self):
        template = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Synthetic",
            content="Synthetic notice",
            version=3,
            language="es",
            status="active",
            evidence_scope_json=["document"],
        )
        record = ConsentRecord.objects.create(
            tenant=self.tenant,
            verification=self.tenant_case,
            verification_subject=self.tenant_case.verification_subject,
            consent_template=template,
            consent_text_snapshot=template.content,
            consent_locale="es",
            accepted_at=timezone.now(),
        )
        self.assertEqual(record.proof_json["purpose"], self.tenant_case.purpose)
        self.assertEqual(record.proof_json["notice_version"], 3)
        self.assertEqual(record.proof_json["locale"], "es")
        self.assertEqual(record.proof_json["evidence_scope"], ["document"])
        self.assertIsNotNone(active_consent(self.tenant_case, "document"))
        self.assertIsNone(active_consent(self.tenant_case, "biometrics"))
        record.consent_text_snapshot = "Changed notice"
        with self.assertRaises(ValidationError):
            record.save()
        record.refresh_from_db()
        record.withdrawn_at = timezone.now()
        with self.assertRaises(ValidationError):
            record.save()
        self.tenant_case.purpose = "Different purpose"
        self.tenant_case.save(update_fields=["purpose"])
        self.assertIsNone(active_consent(self.tenant_case, "document"))

    def test_withdrawal_is_idempotent_cancels_work_and_keeps_original_proof(self):
        record = accept_test_consent(self.tenant_case)
        before = record.proof_json
        session = VerificationSession.objects.create(
            tenant=self.tenant,
            verification=self.tenant_case,
            session_token_hash="synthetic-consent",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=self.tenant_case,
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource_public_id="doc_synthetic",
            status="queued",
            lease_expires_at=timezone.now(),
        )
        record = withdraw(record, actor=self.tenant_reviewer)
        first = record.withdrawn_at
        record = withdraw(record, actor=self.tenant_reviewer)
        self.assertEqual(record.withdrawn_at, first)
        self.assertEqual(record.proof_json, before)
        self.assertIsNone(active_consent(self.tenant_case))
        session.refresh_from_db()
        job.refresh_from_db()
        self.tenant_case.refresh_from_db()
        self.assertEqual(session.status, "revoked")
        self.assertEqual(job.status, "exhausted")
        self.assertEqual(job.error_code, "consent_withdrawn")
        self.assertEqual(self.tenant_case.status, "cancelled")
        self.assertEqual(
            AuditEvent.objects.filter(action="consent.withdrawn").count(), 1
        )

    def test_provider_transfer_is_blocked_and_inflight_result_is_not_persisted(self):
        record = accept_test_consent(self.tenant_case)
        check = create_provider_check(
            verification=self.tenant_case, check_type="document_ocr", status="pending"
        )

        def response():
            withdraw(record)
            return {"status": "completed", "fields": {}, "confidence_score": 0.99}

        with self.assertRaises(ValidationError):
            invoke_provider_check(
                provider_check=check, operation=response, operation_kwargs={}
            )
        check.refresh_from_db()
        self.assertNotEqual(check.status, "completed")
        self.assertFalse(check.normalized_result_json)
        operation = Mock()
        with self.assertRaises(ValidationError):
            invoke_provider_check(
                provider_check=check, operation=operation, operation_kwargs={}
            )
        operation.assert_not_called()

    def test_privacy_administration_requires_dedicated_permission(self):
        record = accept_test_consent(self.tenant_case)
        client = APIClient()
        client.force_authenticate(self.tenant_reviewer)
        url = reverse("consent-withdraw", kwargs={"record_id": record.public_id})
        self.assertEqual(client.post(url, {}, format="json").status_code, 403)
        permission = Permission.objects.create(
            code="manage_consent", name="Manage consent"
        )
        role = Role.objects.create(tenant=self.tenant, name="Privacy", scope="tenant")
        RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(
            role=role, user=self.tenant_reviewer, tenant=self.tenant
        )
        self.assertEqual(client.post(url, {}, format="json").status_code, 200)
        self.assertEqual(client.post(url, {}, format="json").status_code, 200)
        client.force_authenticate(self.platform_reviewer)
        self.assertEqual(client.post(url, {}, format="json").status_code, 403)

    def test_old_withdrawn_record_still_withdraws_a_new_active_proof(self):
        old = accept_test_consent(self.tenant_case)
        old.withdrawn_at = timezone.now()
        old._withdrawal_authorized = True
        old.save(update_fields=["withdrawn_at", "updated_at"])
        active = accept_test_consent(self.tenant_case)
        self.assertIsNotNone(active_consent(self.tenant_case))
        session = VerificationSession.objects.create(
            tenant=self.tenant,
            verification=self.tenant_case,
            session_token_hash="legacy-new-consent",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=self.tenant_case,
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource_public_id="doc_legacy_new_consent",
            status="queued",
            lease_expires_at=timezone.now(),
        )
        withdraw(old)
        active.refresh_from_db()
        session.refresh_from_db()
        job.refresh_from_db()
        self.assertIsNotNone(active.withdrawn_at)
        self.assertEqual(session.status, "revoked")
        self.assertEqual(job.status, "exhausted")
        self.assertIsNone(active_consent(self.tenant_case))

    def test_withdrawal_does_not_require_decrypting_the_acceptance_proof(self):
        record = accept_test_consent(self.tenant_case)
        original = record.proof_json
        with patch(
            "common.fields.decrypt_tenant_json", side_effect=ValueError("unavailable")
        ):
            self.assertIsNone(active_consent(self.tenant_case))
            withdrawn = withdraw(ConsentRecord.objects.get(pk=record.pk))
            self.assertIsNotNone(withdrawn.withdrawn_at)
        record.refresh_from_db()
        self.assertEqual(record.proof_json, original)

    def test_legacy_binding_requires_explicit_reviewed_version_and_scope(self):
        record = accept_test_consent(self.tenant_case)
        self._make_legacy(record)
        self.assertIsNone(active_consent(self.tenant_case))
        output = StringIO()
        call_command(
            "bind_legacy_consent",
            tenant=self.tenant.public_id,
            notice_version=4,
            evidence_scope=["document"],
            batch_size=1,
            stdout=output,
        )
        record.refresh_from_db()
        self.assertEqual(record.proof_json["binding_source"], "legacy-reviewed")
        self.assertEqual(record.proof_json["notice_version"], 4)
        self.assertEqual(record.proof_json["evidence_scope"], ["document"])
        self.assertIsNotNone(active_consent(self.tenant_case, "document"))
        self.assertIsNone(active_consent(self.tenant_case, "biometrics"))
        self.assertEqual(
            AuditEvent.objects.filter(action="consent.legacy_proof_bound").count(), 1
        )

    def test_legacy_binding_rejects_notice_hash_mismatch(self):
        record = accept_test_consent(self.tenant_case)
        self._make_legacy(record, content_hash="0" * 64)
        with self.assertRaises(CommandError):
            call_command(
                "bind_legacy_consent",
                tenant=self.tenant.public_id,
                notice_version=1,
                evidence_scope=["document"],
                stdout=StringIO(),
            )
        record.refresh_from_db()
        self.assertIsNone(record.proof_json)
        self.assertFalse(
            AuditEvent.objects.filter(action="consent.legacy_proof_bound").exists()
        )
