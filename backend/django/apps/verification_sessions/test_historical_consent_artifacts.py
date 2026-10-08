import hashlib
import json
import re

from django.conf import settings
from django.test import SimpleTestCase

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.consent.models import ConsentTemplate
from apps.verification_sessions import tests as fixtures
from apps.verification_sessions.serializers import _consent_artifact


class HistoricalConsentArtifactTests(APITestCase):
    setUp = fixtures.VerificationSessionPortalTests.setUp
    session_headers = fixtures.VerificationSessionPortalTests.session_headers

    def template(
        self,
        name="Identity",
        content="Identity document and biometric notice",
        version=1,
    ):
        return ConsentTemplate.objects.create(
            tenant=self.tenant,
            name=name,
            content=content,
            version=version,
            language="en",
            status="active",
            evidence_scope_json=["document", "biometrics"],
        )

    def accept(self, body):
        return self.client.post(
            reverse(
                "verification-session-consent",
                kwargs={"session_id": self.session.public_id},
            ),
            body,
            format="json",
            **self.session_headers(),
        )

    def test_dynamic_notice_requires_every_fingerprint_field(self):
        template = self.template()
        for body in [
            {"accepted": True},
            {"accepted": True, "template_id": template.public_id},
        ]:
            with self.subTest(body=body):
                response = self.accept(body)
                self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.verification.consent_records.exists())

    def test_fully_fingerprinted_dynamic_notice_can_be_accepted(self):
        template = self.template()
        response = self.accept(
            {
                "accepted": True,
                "template_id": template.public_id,
                "version": template.version,
                "locale": "en",
                "content_hash": hashlib.sha256(template.content.encode()).hexdigest(),
            }
        )
        self.assertEqual(response.status_code, 200, response.data)
        record = self.verification.consent_records.get()
        self.assertEqual(record.consent_template_id, template.pk)
        self.assertEqual(
            record.proof_json["content_hash"],
            hashlib.sha256(template.content.encode()).hexdigest(),
        )

    def test_immutable_snapshot_preserves_legacy_acceptance(self):
        self.verification.policy_snapshot_json["consent"] = {
            "template_id": "generated",
            "content": "Frozen document and biometric notice",
            "language": "en",
            "version": 1,
            "evidence_scope": ["document", "biometrics"],
        }
        self.verification.save(update_fields=["policy_snapshot_json", "updated_at"])
        response = self.accept({"accepted": True})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            self.verification.consent_records.get().proof_json["content_hash"],
            hashlib.sha256(b"Frozen document and biometric notice").hexdigest(),
        )

    def test_generated_english_notice_is_not_labelled_arabic(self):
        artifact = _consent_artifact(self.verification, "ar")
        self.assertTrue(artifact["content"].startswith("I consent"))
        self.assertEqual(artifact["locale"], "en")

    def test_unbound_named_templates_fail_without_selecting_an_unrelated_notice(self):
        self.template(name="Identity")
        self.template(name="Unrelated marketing", content="Marketing", version=9)
        response = self.client.get(
            reverse(
                "verification-session-detail",
                kwargs={"session_id": self.session.public_id},
            ),
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("consent_template_id", response.data["error"]["details"])

    def test_explicit_template_identity_cannot_be_displaced_by_another_name(self):
        intended = self.template(name="Identity")
        self.template(name="Unrelated marketing", content="Marketing", version=9)
        self.verification.metadata_json["consent_template_id"] = intended.public_id
        self.verification.save(update_fields=["metadata_json", "updated_at"])
        response = self.client.get(
            reverse(
                "verification-session-detail",
                kwargs={"session_id": self.session.public_id},
            ),
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data["data"]["consent"]["template_id"], intended.public_id
        )

    def test_frozen_english_notice_keeps_its_language_for_arabic_requests(self):
        self.verification.policy_snapshot_json["consent"] = {
            "content": "Frozen English notice",
            "language": "en",
            "version": 1,
        }
        artifact = _consent_artifact(self.verification, "ar")
        self.assertEqual(artifact["locale"], "en")

    def test_explicit_template_must_be_active_and_owned_by_the_tenant(self):
        from apps.organizations.models import Organization
        from apps.tenants.models import Tenant

        organization = Organization.objects.create(name="Other", slug="other")
        tenant = Tenant.objects.create(
            organization=organization, name="Other", slug="other"
        )
        foreign = ConsentTemplate.objects.create(
            tenant=tenant, name="Identity", content="Foreign notice", status="active"
        )
        inactive = self.template()
        inactive.status = "archived"
        inactive.save(update_fields=["status", "updated_at"])
        for template_id in [foreign.public_id, inactive.public_id, "ctm_missing"]:
            with self.subTest(template_id=template_id):
                self.verification.metadata_json["consent_template_id"] = template_id
                self.verification.save(update_fields=["metadata_json", "updated_at"])
                response = self.client.get(
                    reverse(
                        "verification-session-detail",
                        kwargs={"session_id": self.session.public_id},
                    ),
                    **self.session_headers(),
                )
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn("consent_template_id", response.data["error"]["details"])
        self.assertFalse(self.verification.consent_records.exists())

    def test_translations_in_one_notice_family_are_not_ambiguous(self):
        self.template()
        ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Identity",
            content="Notice en français",
            version=1,
            language="fr",
            status="active",
            evidence_scope_json=["document", "biometrics"],
        )
        artifact = _consent_artifact(self.verification, "fr")
        self.assertEqual(artifact["locale"], "fr")
        self.assertEqual(artifact["content"], "Notice en français")

    def test_notice_rotation_rejects_the_previous_fingerprint(self):
        previous = self.template()
        fingerprint = _consent_artifact(self.verification, "en")
        self.template(version=2, content="Updated document and biometric notice")
        response = self.accept(
            {
                "accepted": True,
                **{
                    key: fingerprint[key]
                    for key in ("template_id", "version", "locale", "content_hash")
                },
            }
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.verification.consent_records.exists())
        self.assertEqual(previous.version, 1)

    def test_region_specific_arabic_locale_uses_rtl_direction(self):
        self.verification.policy_snapshot_json.update(
            {
                "default_locale": "ar-EG",
                "supported_locales": ["ar-EG"],
                "consent": {
                    "language": "ar-EG",
                    "content": "إشعار الموافقة",
                    "version": 1,
                },
            }
        )
        self.verification.save(update_fields=["policy_snapshot_json", "updated_at"])
        response = self.client.get(
            reverse(
                "verification-session-detail",
                kwargs={"session_id": self.session.public_id},
            ),
            HTTP_ACCEPT_LANGUAGE="ar-EG",
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["locale"], "ar-eg")
        self.assertEqual(response.data["data"]["direction"], "rtl")

    def test_template_link_remains_bound_when_another_version_activates(self):
        from unittest.mock import patch

        intended = self.template()
        fingerprint = _consent_artifact(self.verification, "en")

        def rotate_after_resolution(verification, locale):
            artifact = _consent_artifact(verification, locale)
            self.template(version=2, content="Later notice")
            return artifact

        with patch(
            "apps.verification_sessions.serializers._consent_artifact",
            side_effect=rotate_after_resolution,
        ):
            response = self.accept(
                {
                    "accepted": True,
                    **{
                        key: fingerprint[key]
                        for key in ("template_id", "version", "locale", "content_hash")
                    },
                }
            )
        self.assertEqual(response.status_code, 200, response.data)
        record = self.verification.consent_records.get()
        self.assertEqual(record.consent_template_id, intended.pk)
        self.assertEqual(record.proof_json["content_hash"], fingerprint["content_hash"])

    def test_acceptance_uses_the_fingerprint_locale_without_repeating_get_headers(self):
        self.template()
        french = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Identity",
            language="fr",
            content="Avis français",
            version=1,
            status="active",
            evidence_scope_json=["document", "biometrics"],
        )
        self.verification.policy_snapshot_json.update(
            {"default_locale": "en", "supported_locales": ["en", "fr"]}
        )
        self.verification.save(update_fields=["policy_snapshot_json", "updated_at"])
        response = self.client.get(
            reverse(
                "verification-session-detail",
                kwargs={"session_id": self.session.public_id},
            ),
            HTTP_ACCEPT_LANGUAGE="fr",
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        artifact = response.data["data"]["consent"]
        accepted = self.accept(
            {
                "accepted": True,
                **{
                    key: artifact[key]
                    for key in ("template_id", "version", "locale", "content_hash")
                },
            }
        )
        self.assertEqual(accepted.status_code, 200, accepted.data)
        record = self.verification.consent_records.get()
        self.assertEqual(record.consent_locale, "fr")
        self.assertEqual(record.consent_template_id, french.pk)

    def test_submitted_locale_cannot_bypass_policy_supported_languages(self):
        self.template()
        ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Identity",
            language="fr",
            content="Avis français",
            version=1,
            status="active",
            evidence_scope_json=["document", "biometrics"],
        )
        self.verification.policy_snapshot_json.update(
            {"default_locale": "en", "supported_locales": ["en"]}
        )
        self.verification.save(update_fields=["policy_snapshot_json", "updated_at"])
        artifact = _consent_artifact(self.verification, "fr")
        response = self.accept(
            {
                "accepted": True,
                **{
                    key: artifact[key]
                    for key in ("template_id", "version", "locale", "content_hash")
                },
            }
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(self.verification.consent_records.exists())

    def test_explicit_identity_preserves_translations_at_the_selected_version(self):
        intended = self.template()
        arabic = ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Identity",
            language="ar-EG",
            content="الموافقة على التحقق",
            version=1,
            status="active",
            evidence_scope_json=["document", "biometrics"],
        )
        ConsentTemplate.objects.create(
            tenant=self.tenant,
            name="Identity",
            language="ar-EG",
            content="Later notice",
            version=2,
            status="active",
        )
        self.template(name="Unrelated", version=99)
        self.verification.metadata_json["consent_template_id"] = intended.public_id
        self.verification.policy_snapshot_json.update(
            {"default_locale": "en", "supported_locales": ["en", "ar-EG"]}
        )
        self.verification.save(
            update_fields=["metadata_json", "policy_snapshot_json", "updated_at"]
        )
        response = self.client.get(
            reverse(
                "verification-session-detail",
                kwargs={"session_id": self.session.public_id},
            ),
            HTTP_ACCEPT_LANGUAGE="ar-EG",
            **self.session_headers(),
        )
        self.assertEqual(response.status_code, 200, response.data)
        notice = response.data["data"]["consent"]
        self.assertEqual(notice["template_id"], arabic.public_id)
        self.assertEqual(notice["version"], 1)
        accepted = self.accept(
            {
                "accepted": True,
                **{
                    key: notice[key]
                    for key in ("template_id", "version", "locale", "content_hash")
                },
            }
        )
        self.assertEqual(accepted.status_code, 200, accepted.data)
        self.assertEqual(
            self.verification.consent_records.get().consent_template_id, arabic.pk
        )

    def test_regional_frozen_translation_matches_case_normalized_negotiation(self):
        self.verification.policy_snapshot_json["consent"] = {
            "language": "en",
            "content": "English notice",
            "version": 1,
            "translations": {
                "en": {"language": "en", "content": "English notice", "version": 1},
                "ar-EG": {"language": "ar-EG", "content": "الموافقة", "version": 1},
            },
        }
        artifact = _consent_artifact(self.verification, "ar-eg")
        self.assertEqual(artifact["locale"], "ar-EG")
        self.assertEqual(artifact["content"], "الموافقة")

    def test_dynamic_replay_still_requires_all_four_fingerprint_fields(self):
        self.template()
        notice = _consent_artifact(self.verification, "en")
        body = {
            "accepted": True,
            **{
                key: notice[key]
                for key in ("template_id", "version", "locale", "content_hash")
            },
        }
        self.assertEqual(self.accept(body).status_code, 200)
        for key in ("template_id", "version", "locale", "content_hash"):
            partial = {field: value for field, value in body.items() if field != key}
            with self.subTest(missing=key):
                self.assertEqual(self.accept(partial).status_code, 400)
        self.assertEqual(self.accept({"accepted": True}).status_code, 400)
        self.assertEqual(self.accept(body).status_code, 200)
        self.assertEqual(self.verification.consent_records.count(), 1)

    def test_identical_replacement_notice_does_not_reuse_a_different_template_proof(
        self,
    ):
        first = self.template()
        notice = _consent_artifact(self.verification, "en")
        body = {
            "accepted": True,
            **{
                key: notice[key]
                for key in ("template_id", "version", "locale", "content_hash")
            },
        }
        self.assertEqual(self.accept(body).status_code, 200)
        first.status = "archived"
        first.save(update_fields=["status", "updated_at"])
        replacement = self.template(name="Replacement")
        body["template_id"] = replacement.public_id
        response = self.accept(body)
        self.assertEqual(response.status_code, 400, response.data)
        record = self.verification.consent_records.get()
        self.assertEqual(record.consent_template_id, first.pk)
        self.assertEqual(record.proof_json["template_id"], first.public_id)


class ConsentDocumentationContractTests(SimpleTestCase):
    def test_session_and_acceptance_examples_share_the_exact_notice_fingerprint(self):
        specification = (
            settings.BASE_DIR.parent.parent / "docs/architecture/api-spec.md"
        ).read_text()
        detail_section = specification.split("## GET /sessions/{session_id}\n", 1)[
            1
        ].split("\n---", 1)[0]
        acceptance_section = specification.split(
            "## POST /sessions/{session_id}/consent\n", 1
        )[1].split("\n---", 1)[0]
        detail = json.loads(
            re.search(r"```json\n(.*?)\n```", detail_section, re.S).group(1)
        )
        acceptance = json.loads(
            re.search(r"```json\n(.*?)\n```", acceptance_section, re.S).group(1)
        )
        notice = detail["data"]["consent"]
        self.assertTrue(acceptance["accepted"])
        for key in ("template_id", "version", "locale", "content_hash"):
            self.assertEqual(acceptance[key], notice[key])
        self.assertEqual(
            notice["content_hash"],
            hashlib.sha256(notice["content"].encode()).hexdigest(),
        )
