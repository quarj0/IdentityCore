from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone

from apps.consent.models import ConsentRecord, ConsentTemplate
from apps.consent.test_helpers import accept_test_consent
from apps.verification_sessions import tests as fixtures


class LegacyConsentLocaleMigrationTests(TransactionTestCase):
    def setUp(self):
        fixtures.VerificationSessionPortalTests.setUp(self)
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([("consent", "0003_consentrecord_proof_json_and_more")])
        self.old_apps = self.executor.loader.project_state(
            [("consent", "0003_consentrecord_proof_json_and_more")]
        ).apps
        self.addCleanup(self.restore_latest)

    def restore_latest(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def legacy_record(self, suffix, template=None, **fields):
        return self.old_apps.get_model("consent", "ConsentRecord").objects.create(
            public_id=f"con_legacy_{suffix}",
            tenant_id=self.tenant.pk,
            verification_id=self.verification.pk,
            verification_subject_id=self.subject.pk,
            consent_template_id=template.pk if template else None,
            consent_text_snapshot="Historical notice",
            accepted_at=timezone.now(),
            **fields,
        )

    def test_backfill_derives_linked_languages_without_fabricating_proofs(self):
        arabic = ConsentTemplate.objects.create(
            tenant=self.tenant, name="Arabic", language="ar-EG", content="إشعار"
        )
        french = ConsentTemplate.objects.create(
            tenant=self.tenant, name="French", language="fr", content="Notice"
        )
        first = self.legacy_record("arabic", arabic)
        second = self.legacy_record("french", french, deleted_at=timezone.now())
        generated = self.legacy_record("generated")
        self.restore_latest()
        records = ConsentRecord._base_manager
        self.assertEqual(records.get(pk=first.pk).consent_locale, "ar-EG")
        self.assertEqual(records.get(pk=second.pk).consent_locale, "fr")
        self.assertEqual(records.get(pk=generated.pk).consent_locale, "en")
        for record in records.filter(pk__in=[first.pk, second.pk, generated.pk]):
            self.assertIsNone(record.proof_json)
            self.assertEqual(record.consent_content_hash, "")
            self.assertEqual(record.consent_text_snapshot, "Historical notice")

    def test_backfill_preserves_fingerprinted_and_proven_notice_metadata(self):
        arabic = ConsentTemplate.objects.create(
            tenant=self.tenant, name="Arabic", language="ar", content="إشعار"
        )
        fingerprinted = self.legacy_record(
            "fingerprinted", arabic, consent_content_hash="a" * 64
        )
        selected = self.legacy_record("selected", arabic, consent_locale="fr")
        proof = accept_test_consent(self.verification)
        original_proof = proof.proof_json
        self.assertIsNotNone(original_proof)
        self.restore_latest()
        fingerprinted.refresh_from_db()
        selected.refresh_from_db()
        proof.refresh_from_db()
        self.assertEqual(fingerprinted.consent_locale, "en")
        self.assertEqual(fingerprinted.consent_content_hash, "a" * 64)
        self.assertEqual(selected.consent_locale, "fr")
        self.assertEqual(proof.proof_json, original_proof)
        self.assertEqual(proof.consent_locale, "en")
