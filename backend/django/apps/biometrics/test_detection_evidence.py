from decimal import Decimal
from importlib import import_module

from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.biometrics.models import SelfieCapture
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification
from apps.verifications.evidence import (
    build_verification_evidence_pdf_bytes,
    serialize_verification_evidence_report,
    render_report_pdf,
)


class DetectionFixture:
    def create_case(self):
        organization = Organization.objects.create(
            name="Detection fixture", slug="detection"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Detection",
            slug="detection",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Synthetic subject"
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=organization,
            verification_subject=self.subject,
            purpose="Detection provenance",
            expires_at=timezone.now(),
        )

    def capture_fields(self):
        return dict(
            tenant_id=self.tenant.pk,
            verification_id=self.verification.pk,
            verification_subject_id=self.subject.pk,
            storage_key="uploads/selfies/synthetic",
            capture_type="image",
            captured_at=timezone.now(),
        )


class DetectionReportTests(DetectionFixture, TestCase):
    def setUp(self):
        self.create_case()

    def test_new_json_and_pdf_include_detection_provenance_and_zero_values(self):
        capture = SelfieCapture.objects.create(
            **self.capture_fields(),
            face_count=0,
            face_detection_confidence=Decimal("0.0000"),
            face_detection_model_name="synthetic-detector",
            face_detection_model_version="test-v1",
        )
        payload = serialize_verification_evidence_report(self.verification)
        selfie = payload["selfie_captures"][0]
        self.assertEqual(selfie["id"], capture.public_id)
        self.assertEqual(selfie["face_count"], 0)
        self.assertEqual(selfie["face_detection_confidence"], 0.0)
        self.assertEqual(selfie["face_detection_model_name"], "synthetic-detector")
        self.assertEqual(selfie["face_detection_model_version"], "test-v1")
        pdf = build_verification_evidence_pdf_bytes(payload)
        for text in (
            b"Face Count: 0",
            b"Detection Confidence: 0.0",
            b"Detection Model: synthetic-detector",
            b"Detection Model Version: test-v1",
        ):
            self.assertIn(text, pdf)

    def test_unavailable_detection_remains_null_in_json_and_unavailable_in_pdf(self):
        SelfieCapture.objects.create(**self.capture_fields())
        payload = serialize_verification_evidence_report(self.verification)
        self.assertIsNone(payload["selfie_captures"][0]["face_count"])
        self.assertIsNone(payload["selfie_captures"][0]["face_detection_confidence"])
        pdf = build_verification_evidence_pdf_bytes(payload)
        self.assertIn(b"Face Count: N/A", pdf)
        self.assertIn(b"Detection Confidence: N/A", pdf)

    def test_long_report_preserves_late_sections_and_wrapped_values(self):
        pdf = render_report_pdf(
            title="Long report",
            subtitle="Synthetic",
            sections=[
                ("Many rows", [f"Row {i}" for i in range(200)]),
                ("Final evidence", ["start-" + "x" * 140 + "-end-marker"]),
            ],
        )
        self.assertGreater(pdf.count(b"/Type /Page "), 1)
        self.assertIn(b"Row 199", pdf)
        self.assertIn(b"Final evidence", pdf)
        self.assertIn(b"-end-marker", pdf)


class LegacyDetectionMigrationTests(DetectionFixture, TransactionTestCase):
    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_populated_legacy_schema_clears_only_unattributed_default_one(self):
        self.create_case()
        executor = MigrationExecutor(connection)
        old_target = [("biometrics", "0004_livenesschallenge_and_check_challenge")]
        executor.migrate(old_target)
        old_apps = executor.loader.project_state(old_target).apps
        old_selfie = old_apps.get_model("biometrics", "SelfieCapture")
        legacy = old_selfie.objects.create(
            public_id="sel_legacy_default", **self.capture_fields()
        )
        attributed = old_selfie.objects.create(
            public_id="sel_legacy_attributed", **self.capture_fields()
        )
        zero = old_selfie.objects.create(
            public_id="sel_legacy_zero", face_count=0, **self.capture_fields()
        )
        self.assertEqual(legacy.face_count, 1)

        executor = MigrationExecutor(connection)
        middle_target = [("biometrics", "0005_selfiecapture_face_detection_evidence")]
        executor.migrate(middle_target)
        middle_apps = executor.loader.project_state(middle_target).apps
        middle_selfie = middle_apps.get_model("biometrics", "SelfieCapture")
        middle_selfie.objects.filter(pk=attributed.pk).update(
            face_detection_confidence=Decimal("0.9800"),
            face_detection_model_name="recorded-detector",
            face_detection_model_version="v1",
        )
        later = middle_selfie.objects.create(
            public_id="sel_later_capture", face_count=1, **self.capture_fields()
        )
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

        repaired = SelfieCapture.objects.get(pk=legacy.pk)
        self.assertIsNone(repaired.face_count)
        self.assertEqual(
            repaired.face_detection_correction_json["previous_face_count"], 1
        )
        correction = repaired.face_detection_correction_json
        payload = serialize_verification_evidence_report(self.verification)
        exported = next(
            item
            for item in payload["selfie_captures"]
            if item["id"] == legacy.public_id
        )
        self.assertIsNone(exported["face_count"])
        self.assertEqual(exported["face_detection_correction"], correction)
        self.assertEqual(SelfieCapture.objects.get(pk=attributed.pk).face_count, 1)
        self.assertEqual(SelfieCapture.objects.get(pk=zero.pk).face_count, 0)
        self.assertEqual(SelfieCapture.objects.get(pk=later.pk).face_count, 1)
        repair = import_module(
            "apps.biometrics.migrations.0006_clear_legacy_placeholder_face_counts"
        )
        with connection.schema_editor() as editor:
            repair.clear_legacy_placeholder_counts(apps, editor)
        repaired.refresh_from_db()
        self.assertIsNone(repaired.face_count)
        self.assertEqual(repaired.face_detection_correction_json, correction)
        self.assertEqual(SelfieCapture.objects.get(pk=attributed.pk).face_count, 1)
