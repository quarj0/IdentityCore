from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import override_settings
from rest_framework.test import APIClient, APITransactionTestCase

from apps.verification_sessions import test_handoff
from apps.verifications.models import VerificationMobileHandoff, VerificationSession


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
@override_settings(VERIFICATION_PORTAL_BASE_URL="https://verify.example.test/verify")
class MobileHandoffRaceTests(APITransactionTestCase):
    setUp = test_handoff.HandoffLifecycleTests.setUp
    session_headers = test_handoff.HandoffLifecycleTests.session_headers
    create = test_handoff.HandoffLifecycleTests.create

    def parallel(self, function):
        barrier = Barrier(2)

        def run(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return function(index)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, range(2)))

    def test_simultaneous_claim_has_one_mobile_session(self):
        claim = self.create()
        results = self.parallel(
            lambda _: APIClient()
            .post(
                "/api/v1/sessions/mobile-handoff/redeem",
                {"handoff": claim, "session_id": self.session.public_id},
                format="json",
            )
            .status_code
        )
        self.assertEqual(sorted(results), [200, 400])
        self.assertEqual(VerificationSession.objects.count(), 2)

    def test_simultaneous_creation_leaves_one_live_claim(self):
        results = self.parallel(
            lambda _: APIClient()
            .post(
                f"/api/v1/sessions/{self.session.public_id}/mobile-handoff",
                {},
                format="json",
                **self.session_headers(),
            )
            .status_code
        )
        self.assertEqual(results, [200, 200])
        from django.utils import timezone

        self.assertEqual(
            VerificationMobileHandoff.objects.filter(
                redeemed_at__isnull=True, expires_at__gt=timezone.now()
            ).count(),
            1,
        )

    def test_simultaneous_challenge_issuance_cannot_exceed_case_budget(self):
        from datetime import timedelta
        from django.utils import timezone
        from apps.biometrics.models import LivenessChallenge
        from apps.consent.test_helpers import accept_test_consent
        from shared.liveness_challenge import MAX_CHALLENGES, new_actions

        accept_test_consent(self.verification)
        self.verification.policy_snapshot_json = {"required_liveness_level": "active"}
        self.verification.save()
        for _ in range(MAX_CHALLENGES - 1):
            LivenessChallenge.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                verification_session=self.session,
                actions=new_actions(),
                expires_at=timezone.now() + timedelta(minutes=3),
            )
        statuses = self.parallel(
            lambda _: APIClient()
            .post(
                f"/api/v1/sessions/{self.session.public_id}/liveness/challenge",
                {},
                format="json",
                **self.session_headers(),
            )
            .status_code
        )
        self.assertEqual(sorted(statuses), [200, 400])
        self.assertEqual(
            LivenessChallenge.objects.filter(verification=self.verification).count(),
            MAX_CHALLENGES,
        )

    def test_simultaneous_liveness_posts_consume_one_challenge(self):
        from datetime import timedelta
        from unittest.mock import patch
        from django.utils import timezone
        from apps.biometrics.models import (
            LivenessChallenge,
            LivenessCheck,
            SelfieCapture,
        )
        from apps.consent.test_helpers import accept_test_consent
        from apps.document_captures.models import DocumentCapture
        from apps.identity_documents.models import IdentityDocument
        from apps.verifications.models import ProcessingJob

        accept_test_consent(self.verification)
        self.verification.status = "awaiting_selfie"
        self.verification.save(update_fields=["status", "updated_at"])
        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processed",
        )
        DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=document,
            side="front",
            storage_key="synthetic/front",
            mime_type="image/jpeg",
            status="uploaded",
            captured_at=timezone.now(),
        )
        captures = [
            SelfieCapture.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                verification_subject=self.subject,
                storage_key=f"synthetic/video-{index}",
                capture_type="video",
                mime_type="video/webm",
                status="uploaded",
                captured_at=timezone.now(),
            )
            for index in range(2)
        ]
        challenge = LivenessChallenge.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_session=self.session,
            actions=[
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
                "turn_left",
                "look_up",
                "turn_right",
                "look_down",
            ],
            expires_at=timezone.now() + timedelta(minutes=2),
        )
        with patch(
            "apps.biometrics.tasks.process_verification_biometrics_task.delay"
        ) as publish:
            statuses = self.parallel(
                lambda index: APIClient()
                .post(
                    f"/api/v1/sessions/{self.session.public_id}/liveness",
                    {
                        "liveness_type": "active",
                        "selfie_capture_id": captures[index].public_id,
                        "challenge_id": challenge.public_id,
                    },
                    format="json",
                    **self.session_headers(),
                )
                .status_code
            )
        self.assertEqual(sorted(statuses), [200, 400])
        self.assertEqual(LivenessCheck.objects.filter(challenge=challenge).count(), 1)
        self.assertEqual(
            ProcessingJob.objects.filter(verification=self.verification).count(), 1
        )
        challenge.refresh_from_db()
        self.assertIsNotNone(challenge.completed_at)
        publish.assert_called_once()
