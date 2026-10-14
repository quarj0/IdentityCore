from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.consent.models import ConsentRecord, ConsentTemplate
from apps.consent.serializers import serialize_consent_record
from apps.consent.test_helpers import accept_test_consent
from apps.verification_sessions import tests as fixtures


class LegacyConsentLocaleReportingTests(APITestCase):
    def setUp(self):
        fixtures.VerificationSessionPortalTests.setUp(self)
        permission = Permission.objects.create(
            code="manage_consent", name="Manage consent"
        )
        role = Role.objects.create(tenant=self.tenant, name="Privacy", scope="tenant")
        RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(role=role, user=self.user, tenant=self.tenant)
        self.client.force_authenticate(self.user)

    def legacy_record(self, suffix, template=None, **fields):
        old_apps = (
            MigrationExecutor(connection)
            .loader.project_state(
                [("consent", "0003_consentrecord_proof_json_and_more")]
            )
            .apps
        )
        historical = old_apps.get_model("consent", "ConsentRecord").objects.create(
            public_id=f"con_legacy_{suffix}",
            tenant_id=self.tenant.pk,
            verification_id=self.verification.pk,
            verification_subject_id=self.subject.pk,
            consent_template_id=template.pk if template else None,
            consent_text_snapshot="Original notice",
            accepted_at=timezone.now(),
            **fields,
        )
        return ConsentRecord._base_manager.get(pk=historical.pk)

    def serialized(self, record):
        response = self.client.get(reverse("consent-record-list"))
        self.assertEqual(response.status_code, 200, response.data)
        return next(
            row
            for row in response.data["data"]["results"]
            if row["id"] == record.public_id
        )

    def test_legacy_default_is_not_reported_as_observed_english(self):
        template = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Arabic notice",
            language="ar",
            content="Original notice",
        )
        record = self.legacy_record("default", template)
        payload = self.serialized(record)
        self.assertIsNone(payload["consent_locale"])
        self.assertEqual(payload["consent_locale_status"], "unavailable_legacy")
        template.language = "fr"
        template.content = "Replacement notice"
        template.save(update_fields=["language", "content", "updated_at"])
        self.assertIsNone(self.serialized(record)["consent_locale"])
        record.refresh_from_db()
        self.assertEqual(record.consent_locale, "en")
        self.assertEqual(record.consent_text_snapshot, "Original notice")
        self.assertEqual(record.consent_content_hash, "")
        self.assertIsNone(record.proof_json)

    def test_explicit_and_fingerprinted_locales_are_preserved(self):
        for suffix, locale, content_hash in [
            ("explicit", "fr", ""),
            ("fingerprinted", "en", "a" * 64),
        ]:
            with self.subTest(suffix=suffix):
                record = self.legacy_record(
                    suffix, consent_locale=locale, consent_content_hash=content_hash
                )
                payload = self.serialized(record)
                self.assertEqual(payload["consent_locale"], locale)
                self.assertEqual(payload["consent_locale_status"], "recorded")

    def test_current_signed_acceptance_retains_locale_and_proof(self):
        record = accept_test_consent(self.verification)
        proof = record.proof_json
        payload = self.serialized(record)
        self.assertEqual(payload["consent_locale"], "en")
        self.assertEqual(payload["consent_locale_status"], "recorded")
        record.refresh_from_db()
        self.assertEqual(record.proof_json, proof)

    def test_retained_deleted_legacy_record_does_not_infer_a_locale(self):
        record = self.legacy_record("retained", deleted_at=timezone.now())
        self.assertIsNone(serialize_consent_record(record)["consent_locale"])
        self.assertEqual(
            serialize_consent_record(record)["consent_locale_status"],
            "unavailable_legacy",
        )
