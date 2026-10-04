from io import BytesIO
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.identity_documents.authenticity import (
    collect_authenticity,
    normalize_authenticity,
    source_size_for_capture,
    unavailable_authenticity,
)
from apps.identity_documents import tests as document_tests
from apps.providers.adapters import ProviderContractError, provider_adapter_registry
from apps.providers.models import Provider, ProviderAssignment


def evidence(**changes):
    return {
        **unavailable_authenticity(source_size=[1000, 600]),
        "status": "completed",
        "verdict": "authentic",
        "confidence": 0.98,
        "model_name": "synthetic-only",
        "model_version": "fixture-1",
        **changes,
    }


class AuthenticityTests(TestCase):
    setUp = document_tests.IdentityDocumentTaskTests.setUp

    def enable(self):
        self.verification.policy_snapshot_json = {
            "document_authenticity_required": True,
            "document_authenticity_min_confidence": 0.9,
        }
        self.verification.save()

    def test_scaled_crop_maps_to_original_coordinates(self):
        result = normalize_authenticity(
            evidence(
                analysis_size=[400, 200],
                analysis_to_source=[2, 0, 100, 0, 2, 100],
                regions=[
                    {
                        "box": [50, 20, 100, 40],
                        "reason": "copy_move",
                        "confidence": 0.91,
                    }
                ],
            ),
            source_size=[1000, 600],
        )
        self.assertEqual(result["regions"][0]["box"], [0.2, 140 / 600, 0.2, 80 / 600])
        self.assertEqual(result["coordinate_space"], "source_normalized")

    def test_rotation_maps_all_corners(self):
        result = normalize_authenticity(
            evidence(
                analysis_size=[600, 1000],
                analysis_to_source=[0, -1, 1000, 1, 0, 0],
                regions=[
                    {
                        "box": [100, 200, 40, 50],
                        "reason": "portrait_edit",
                        "confidence": 0.8,
                    }
                ],
            ),
            source_size=[1000, 600],
        )
        self.assertEqual(result["regions"][0]["box"], [0.75, 100 / 600, 0.05, 40 / 600])

    def test_invalid_contracts_fail_before_persistence(self):
        malformed = [
            evidence(status=[]),
            evidence(verdict={}),
            evidence(confidence=float("nan")),
            evidence(confidence=True),
            evidence(source_size=[999, 600]),
            evidence(analysis_to_source=[0] * 6),
            evidence(raw_output={"bad": float("inf")}),
            evidence(
                regions=[
                    {"box": [0, 0, 2000, 1], "reason": "copy_move", "confidence": 0.9}
                ]
            ),
            evidence(regions=[{"box": [0, 0, 1, 1], "reason": [], "confidence": 0.9}]),
            evidence(
                regions=[
                    {
                        "box": [0, 0, 1, 1],
                        "reason": "script injection",
                        "confidence": 0.9,
                    }
                ]
            ),
        ]
        for result in malformed:
            with self.subTest(result=result), self.assertRaises(ProviderContractError):
                normalize_authenticity(result, source_size=[1000, 600])
        self.assertFalse(
            self.verification.provider_checks.filter(
                check_type="document_authenticity"
            ).exists()
        )

    def test_managed_model_uncertainty_requires_review(self):
        self.enable()
        with patch(
            "apps.identity_documents.authenticity.source_size_for_capture",
            return_value=((1000, 600), "test"),
        ):
            result = collect_authenticity(
                verification=self.verification,
                document=self.identity_document,
                captures=[self.capture],
                processing_job=None,
            )
        self.assertTrue(result["requires_manual_review"])
        self.assertEqual(result["captures"][0]["result"]["verdict"], "inconclusive")
        from apps.verifications.models import VerificationDecision

        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )

    def test_external_authenticity_is_versioned_and_regions_require_review(self):
        self.enable()
        provider = Provider.objects.create(
            tenant=self.tenant,
            name="Authenticity",
            code="synthetic-authenticity",
            provider_type="document",
        )
        ProviderAssignment.objects.create(
            tenant=self.tenant,
            provider=provider,
            assignment_key="document_authenticity",
        )
        adapter = Mock()
        adapter.document_authenticity.return_value = evidence(
            regions=[
                {"box": [100, 60, 100, 60], "reason": "copy_move", "confidence": 0.9}
            ],
            raw_output={"synthetic_private": "kept encrypted"},
        )
        with patch.dict(
            provider_adapter_registry._factories, {provider.code: lambda: adapter}
        ), patch(
            "apps.identity_documents.authenticity.source_size_for_capture",
            return_value=((1000, 600), "test"),
        ):
            result = collect_authenticity(
                verification=self.verification,
                document=self.identity_document,
                captures=[self.capture],
                processing_job=None,
            )
        self.assertTrue(result["requires_manual_review"])
        check = self.verification.provider_checks.get(
            check_type="document_authenticity"
        )
        self.assertEqual(check.provider, provider)
        self.assertEqual(check.normalized_result_json["model_version"], "fixture-1")
        self.assertEqual(result["captures"][0]["provider_check_id"], check.public_id)
        self.assertEqual(
            check.normalized_result_json["regions"][0]["box"], [0.1, 0.1, 0.1, 0.1]
        )

    def test_unavailable_capture_and_disabled_policy_are_safe(self):
        with patch(
            "apps.identity_documents.authenticity.source_size_for_capture"
        ) as read:
            self.assertIsNone(
                collect_authenticity(
                    verification=self.verification,
                    document=self.identity_document,
                    captures=[self.capture],
                    processing_job=None,
                )
            )
            read.assert_not_called()
        self.enable()
        self.upload.status = "deleted"
        self.upload.save()
        with patch("apps.identity_documents.authenticity.get_object_bytes") as read:
            result = collect_authenticity(
                verification=self.verification,
                document=self.identity_document,
                captures=[self.capture],
                processing_job=None,
            )
            read.assert_not_called()
        self.assertTrue(result["requires_manual_review"])

    def test_exif_orientation_defines_source_geometry(self):
        image = Image.new("RGB", (80, 40), "white")
        exif = Image.Exif()
        exif[274] = 6
        output = BytesIO()
        image.save(output, format="JPEG", exif=exif)
        with patch(
            "apps.identity_documents.authenticity.get_object_bytes",
            return_value=(output.getvalue(), "image/jpeg"),
        ):
            size, _ = source_size_for_capture(self.capture)
        self.assertEqual(size, (40, 80))

    def reviewer(self):
        user = get_user_model().objects.create_user(
            email="reviewer@example.test", password="unused", tenant=self.tenant
        )
        role = Role.objects.create(tenant=self.tenant, scope="tenant", name="Reviewer")
        permission, _ = Permission.objects.get_or_create(
            code="manual_review", defaults={"name": "Review"}
        )
        RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(user=user, role=role, tenant=self.tenant)
        client = APIClient()
        client.force_authenticate(user)
        return client

    def test_review_endpoint_filters_raw_output_and_deleted_evidence(self):
        client = self.reviewer()
        self.identity_document.extracted_data_json = {
            "document_authenticity": {
                "captures": [
                    {
                        "capture_id": self.capture.public_id,
                        "result": normalize_authenticity(
                            evidence(raw_output={"private": "secret"}),
                            source_size=[1000, 600],
                        ),
                    }
                ],
                "requires_manual_review": False,
            }
        }
        self.identity_document.save()
        path = f"/api/v1/verifications/manual-reviews/{self.verification.public_id}/authenticity"
        response = client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("private", str(response.data))
        self.assertEqual(len(response.data["data"]["captures"]), 1)
        self.capture.soft_delete()
        self.assertEqual(client.get(path).data["data"]["captures"], [])
        self.verification.soft_delete()
        self.assertEqual(client.get(path).status_code, 404)

    def test_review_requires_ownership(self):
        from apps.tenants.models import Tenant
        from apps.organizations.models import Organization

        foreign_org = Organization.objects.create(name="Foreign", slug="foreign-review")
        foreign = Tenant.objects.create(
            organization=foreign_org, name="Foreign", slug="foreign-review"
        )
        user = get_user_model().objects.create_user(
            email="viewer@example.test", password="unused", tenant=foreign
        )
        client = APIClient()
        client.force_authenticate(user)
        response = client.get(
            f"/api/v1/verifications/manual-reviews/{self.verification.public_id}/authenticity"
        )
        self.assertEqual(response.status_code, 404)
