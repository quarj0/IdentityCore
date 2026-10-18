from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.audit.models import AuditEvent
from apps.consent.models import ConsentRecord, ConsentTemplate
from apps.verification_sessions import tests as portal_fixtures
from common.test_subject_metadata import SECRET, signed_headers


@override_settings(VERIFICATION_METADATA_SECRET=SECRET)
class SubjectMetadataIntegrationTests(APITestCase):
    setUp = portal_fixtures.VerificationSessionPortalTests.setUp

    def test_session_consent_and_audit_retain_authenticated_subject_context(self):
        detail = reverse(
            "verification-session-detail", kwargs={"session_id": self.session.public_id}
        )
        template = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Synthetic notice",
            version=1,
            language="en",
            content="Synthetic notice",
            status="active",
            created_by=self.user,
        )
        authorization = f"Bearer {self.raw_session_token}"
        response = self.client.get(
            detail, **signed_headers(detail, authorization=authorization)
        )
        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(self.session.ip_address, "192.0.2.40")
        self.assertEqual(self.session.user_agent, "ApplicantBrowser/1.0")
        consent = reverse(
            "verification-session-consent",
            kwargs={"session_id": self.session.public_id},
        )
        import hashlib

        response = self.client.post(
            consent,
            {
                "accepted": True,
                "template_id": template.public_id,
                "version": 1,
                "locale": "en",
                "content_hash": hashlib.sha256(b"Synthetic notice").hexdigest(),
            },
            format="json",
            **signed_headers(consent, authorization=authorization, method="POST"),
        )
        self.assertEqual(response.status_code, 200, response.data)
        record = ConsentRecord.objects.get(verification=self.verification)
        event = AuditEvent.objects.get(action="consent.accepted", tenant=self.tenant)
        for item in (record, event):
            self.assertEqual(item.ip_address, "192.0.2.40")
            self.assertEqual(item.user_agent, "ApplicantBrowser/1.0")
        self.assertEqual(
            record.proof_json["request_provenance"]["source"], "verification_portal"
        )
        self.assertEqual(
            event.metadata_json["request_provenance"]["client_ip"], "ingress_asserted"
        )

    def test_bad_signature_cannot_touch_session_or_create_consent(self):
        path = reverse(
            "verification-session-detail", kwargs={"session_id": self.session.public_id}
        )
        headers = signed_headers(path, authorization=f"Bearer {self.raw_session_token}")
        headers["HTTP_X_IC_SUBJECT_SIGNATURE"] = "0" * 64
        self.assertEqual(self.client.get(path, **headers).status_code, 400)
        self.session.refresh_from_db()
        self.assertIsNone(self.session.started_at)
        self.assertFalse(
            ConsentRecord.objects.filter(verification=self.verification).exists()
        )
