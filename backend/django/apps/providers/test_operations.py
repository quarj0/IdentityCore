from copy import deepcopy
from datetime import timedelta
import json
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.access_control.models import Permission, Role, RolePermission
from apps.consent.test_helpers import accept_test_consent
from apps.projects.models import Project
from apps.providers import assurance, operations, test_configuration as fixtures
from apps.providers.adapters import ProviderContractError
from apps.providers.configuration import activate_configuration, test_configuration
from apps.providers.models import ProviderCheck, ProviderOperation
from apps.providers.services import invoke_provider_check
from apps.verification_subjects.models import VerificationSubject
from apps.verification_subjects.services import request_subject_deletion
from apps.verifications.models import Verification, ProcessingJob
from apps.verifications.processing_jobs import (
    ProviderOperationPending,
    ProcessingJobOwnershipLost,
)
from common.provider_signing import canonical_json, sign_message


class ProviderOperationTests(TestCase):
    create = fixtures.ConfigurationTests.create

    def setUp(self):
        fixtures.ConfigurationTests.setUp(self)
        role = Role.objects.get(tenant=self.tenant, name="Provider manager")
        for code in (
            "manage_provider_assurance",
            "approve_provider_assurance",
            "manage_subject_privacy",
        ):
            permission, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": code}
            )
            RolePermission.objects.create(role=role, permission=permission)
        for actor in (self.requester, self.approver):
            actor.status = "active"
            actor.save(update_fields=["status"])
        self.public.update(
            {
                "signing_mode": "hmac_v1",
                "operation_contract": operations.CONTRACT,
                "required_assurance": "conformance",
            }
        )
        config = self.create()

        def connection_reply(**values):
            payload = values["payload"]
            return {
                "contract_version": "1",
                "status": "completed",
                "challenge": payload["challenge"],
                "capabilities": payload["capabilities"],
                "operation_contract": payload["operation_contract"],
            }

        with patch(
            "apps.providers.configuration.SecureHTTPProviderAdapter.post_json",
            side_effect=connection_reply,
        ):
            self.config = activate_configuration(
                config=test_configuration(config=config, user=self.requester),
                user=self.requester,
            )
        report = {
            **assurance.report_scope(self.config, "document_ocr"),
            "cases": {
                case: "passed" for case in assurance.SYNC_CASES | assurance.ASYNC_CASES
            },
            "artifact_sha256": "0" * 64,
            "assurance_references": [],
        }
        receipt = assurance.propose_certification(
            tenant_id=self.tenant.pk,
            actor=self.requester,
            configuration_id=self.config.public_id,
            capability="document_ocr",
            report=report,
            assurance_level="conformance",
            valid_until=timezone.now() + timedelta(days=1),
            delete_after=timezone.now() + timedelta(days=2),
        )
        assurance.approve_certification(
            tenant_id=self.tenant.pk,
            actor=self.approver,
            certification_id=receipt.public_id,
        )
        self.project = Project.objects.create(
            tenant=self.tenant,
            name="Operations",
            slug="operations",
            created_by=self.requester,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Synthetic provider subject"
        )
        self.case = Verification.objects.create(
            tenant=self.tenant,
            organization=self.org,
            project=self.project,
            verification_subject=self.subject,
            purpose="synthetic-verification",
            status="awaiting_selfie",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        accept_test_consent(self.case)
        self.job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=self.case,
            job_type="identity_document",
            resource_public_id="idoc_synthetic",
            status="processing",
            attempt_count=1,
            lease_generation=1,
            lease_expires_at=timezone.now() + timedelta(minutes=5),
        )
        self.check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.case,
            provider=self.provider,
            check_type="document_ocr",
            status="pending",
            started_at=timezone.now(),
            request_metadata_json={"identity_document_id": "idoc_synthetic"},
        )
        self.inputs = {
            "verification_id": self.case.public_id,
            "document_storage_key": "synthetic/opaque-reference",
        }
        self.calls = []

    def invoke(self, response=None):
        def transport(**values):
            self.assertFalse(
                __import__("django").db.connection.in_atomic_block
                and not self._test_atomic_only()
            )
            self.calls.append(values["payload"])
            if response is not None:
                return response(values["payload"])
            return {
                "binding": values["payload"]["binding"],
                "status": "pending",
                "retry_after_seconds": 5,
            }

        from apps.providers.configuration import invoke_configured_provider

        with patch(
            "apps.providers.operations.SecureHTTPProviderAdapter.post_json",
            side_effect=transport,
        ):
            return invoke_provider_check(
                provider_check=self.check,
                processing_job=self.job,
                operation=lambda: invoke_configured_provider(
                    provider=self.provider,
                    environment="sandbox",
                    capability="document_ocr",
                    inputs=self.inputs,
                    timeout_seconds=10,
                ),
                operation_kwargs={},
            )

    def _test_atomic_only(self):
        from django.db import connection

        return all(
            getattr(block, "_from_testcase", False)
            for block in connection.atomic_blocks
        )

    def pending(self):
        with self.assertRaises(ProviderOperationPending):
            self.invoke()
        self.check.refresh_from_db()
        self.assertEqual(self.check.status, "processing")
        return ProviderOperation.objects.get(provider_check=self.check)

    def completed(self, record, **overrides):
        return {
            "binding": operations.envelope(record),
            "status": "completed",
            "result": {
                "contract_version": "1",
                "capability": "document_ocr",
                "status": "completed",
                "extracted_fields": {"name": "Synthetic provider name"},
            },
            **overrides,
        }

    def test_pending_survives_worker_reentry_and_poll_uses_same_bound_operation(self):
        record = self.pending()
        initial = self.calls[0]["binding"]
        self.assertEqual(self.calls[0]["operation"], "start")
        with patch(
            "apps.providers.operations.timezone.now",
            return_value=record.next_poll_at + timedelta(seconds=1),
        ):
            result = self.invoke(lambda payload: self.completed(record))
        self.assertEqual(self.calls[1]["operation"], "poll")
        self.assertEqual(self.calls[1]["binding"], initial)
        self.assertNotIn("inputs", self.calls[1])
        self.assertEqual(result["extracted_fields"]["name"], "Synthetic provider name")
        self.assertEqual(ProviderOperation.objects.count(), 1)
        self.check.refresh_from_db()
        self.assertEqual(self.check.status, "completed")

    def test_identical_completion_is_idempotent_but_changed_binding_or_result_is_rejected(
        self,
    ):
        record = self.pending()
        response = self.completed(record)
        operations.accept_response(record.public_id, response)
        operations.accept_response(record.public_id, response)
        for field, value in (
            ("environment", "production"),
            ("lease_token", "incorrect"),
            ("request_sha256", "f" * 64),
            ("capability", "liveness"),
            ("lease_generation", 2),
        ):
            tampered = deepcopy(response)
            tampered["binding"][field] = value
            with self.subTest(field=field), self.assertRaises(ProviderContractError):
                operations.accept_response(record.public_id, tampered)
        changed = deepcopy(response)
        changed["result"]["extracted_fields"]["name"] = "Conflicting value"
        with self.assertRaises(ProviderContractError):
            operations.accept_response(record.public_id, changed)

    def test_signed_callback_requires_fresh_exact_wire_authentication_and_returns_signed_receipt(
        self,
    ):
        record = self.pending()
        path = record.scope_json["callback_path"]
        body = canonical_json(self.completed(record))
        from apps.providers.configuration import _signing_context

        context = _signing_context(self.config)
        signed = sign_message(
            method="POST",
            path=path,
            body=body,
            key_id=context.key_id,
            secret=context.secret,
        )
        headers = {
            "HTTP_" + key.upper().replace("-", "_"): value
            for key, value in signed.headers().items()
        }
        client = APIClient()
        denied = client.post(path, body, content_type="application/json")
        self.assertEqual(denied.status_code, 403, denied.data)
        accepted = client.post(path, body, content_type="application/json", **headers)
        self.assertEqual(accepted.status_code, 200, accepted.content)
        self.assertEqual(json.loads(accepted.content)["data"]["status"], "completed")
        self.assertEqual(accepted["X-IC-Nonce"], signed.nonce)
        replay = client.post(path, body, content_type="application/json", **headers)
        self.assertEqual(replay.status_code, 403)

    def test_withdrawn_consent_callback_is_rejected_without_internal_error(self):
        from apps.consent.models import ConsentRecord

        record = self.pending()
        # Exercise loss of proof independently of the later worker-cancellation checks.
        proof = ConsentRecord.objects.get(verification=self.case)
        proof.withdrawn_at = timezone.now()
        proof._withdrawal_authorized = True
        proof.save(update_fields=["withdrawn_at", "updated_at"])
        path = f"/api/v1/providers/operations/{record.public_id}/callback"
        body = canonical_json(self.completed(record))
        from apps.providers.configuration import _signing_context

        context = _signing_context(self.config)
        signed = sign_message(
            method="POST",
            path=path,
            body=body,
            key_id=context.key_id,
            secret=context.secret,
        )
        headers = {
            "HTTP_" + key.upper().replace("-", "_"): value
            for key, value in signed.headers().items()
        }
        client = APIClient()
        client.raise_request_exception = False
        response = client.post(path, body, content_type="application/json", **headers)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"]["code"], "provider_callback_rejected")
        record.refresh_from_db()
        self.assertEqual(record.status, "pending")
        self.assertEqual(record.result_json, {})

    def test_late_and_deleted_subject_completions_cannot_restore_results(self):
        record = self.pending()
        response = self.completed(record)
        with patch(
            "apps.providers.operations.timezone.now", return_value=record.deadline
        ):
            with self.assertRaises(ProviderContractError):
                operations.accept_response(record.public_id, response)
        request_subject_deletion(subject=self.subject, actor=self.approver)
        with self.assertRaises(ProcessingJobOwnershipLost):
            operations.accept_response(record.public_id, response)
        self.check.refresh_from_db()
        self.assertEqual(self.check.normalized_result_json, {})

    def test_real_document_worker_defers_then_resumes_from_callback_without_resubmission(
        self,
    ):
        from apps.document_captures.models import DocumentCapture
        from apps.identity_documents.models import IdentityDocument
        from apps.identity_documents.tasks import process_identity_document_task
        from apps.providers.configuration import assign_configuration
        from apps.uploads.models import Upload
        from apps.uploads.test_helpers import seal_test_upload

        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.case,
            verification_subject=self.subject,
            document_type_id="passport",
            country_profile_id="GH",
            status="processing",
        )
        capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=document,
            side="front",
            storage_key="uploads/documents/synthetic-front",
            captured_at=timezone.now(),
        )
        session = self.case.sessions.create(
            tenant=self.tenant,
            session_token_hash="synthetic-session",
            expires_at=self.case.expires_at,
        )
        seal_test_upload(
            Upload.objects.create(
                tenant=self.tenant,
                verification=self.case,
                verification_session=session,
                purpose="document_capture",
                storage_key=capture.storage_key,
                storage_provider="local",
                mime_type="image/jpeg",
                file_size_bytes=1024,
                status="consumed",
                expires_at=self.case.expires_at,
                consumed_at=timezone.now(),
            )
        )
        self.job.resource_public_id = document.public_id
        self.job.status = "queued"
        self.job.attempt_count = 0
        self.job.lease_generation = 0
        self.job.save(
            update_fields=[
                "resource_public_id",
                "status",
                "attempt_count",
                "lease_generation",
            ]
        )
        self.check.request_metadata_json = {"identity_document_id": document.public_id}
        self.check.save(update_fields=["request_metadata_json"])
        assign_configuration(
            config=self.config,
            user=self.requester,
            capability="document_ocr",
            countries=["GH"],
            document_types=["passport"],
        )
        classification = {
            "status": "completed",
            "classification_status": "recognized",
            "predicted_document_type": "passport",
            "expected_document_type": "passport",
            "matched_expected_document_type": True,
            "predicted_country_code": "GH",
            "confidence_score": 0.95,
            "evidence_score": 0.95,
            "classification_margin": 0.95,
            "workflow_action": "continue",
            "requires_manual_review": False,
            "manual_review": {
                "required": False,
                "priority": "low",
                "reason_codes": [],
                "review_category": "document_classification",
            },
            "issues": [],
            "ocr": {"average_confidence": 0.95, "line_count": 1},
            "evidence": [],
            "candidates": [],
            "raw_text_lines": [],
            "model_name": "synthetic-classifier",
            "model_version": "1",
        }

        def pending_reply(**values):
            return {
                # Match the real HTTP JSON round trip, including Django text enums.
                "binding": json.loads(json.dumps(values["payload"]["binding"])),
                "status": "pending",
                "retry_after_seconds": 5,
            }

        with patch(
            "apps.identity_documents.tasks.run_document_quality",
            return_value={"status": "completed", "quality_score": 0.9, "issues": []},
        ), patch(
            "apps.identity_documents.tasks.run_document_classification",
            return_value=classification,
        ), patch(
            "apps.providers.operations.SecureHTTPProviderAdapter.post_json",
            side_effect=pending_reply,
        ) as transport:
            self.assertEqual(
                process_identity_document_task(document.public_id),
                "processing",
                list(
                    self.case.provider_checks.values(
                        "check_type", "status", "error_code"
                    )
                ),
            )
            self.job.refresh_from_db()
            self.assertEqual(self.job.status, "queued")
            self.assertEqual(self.job.attempt_count, 0)
            self.assertTrue(self.job.error_code.startswith("provider_pending:"))
            record = ProviderOperation.objects.get(processing_job=self.job)
            result = self.completed(record)
            result["result"].update({"confidence_score": 0.95, "issues": []})
            operations.accept_response(record.public_id, result)
            self.assertEqual(
                process_identity_document_task(document.public_id), "processed"
            )
            self.assertEqual(transport.call_count, 1)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "completed")
        self.assertEqual(self.job.attempt_count, 1)
        document.refresh_from_db()
        self.assertEqual(
            document.extracted_data_json["name"], "Synthetic provider name"
        )

    def test_operation_listing_exposes_cleanup_status_without_results_or_lease(self):
        record = self.pending()
        client = APIClient()
        client.force_authenticate(self.approver)
        result = client.get(
            "/api/v1/providers/operations",
            {
                "project_id": self.project.public_id,
                "verification_id": self.case.public_id,
            },
        )
        self.assertEqual(result.status_code, 200, result.data)
        item = result.data["data"]["results"][0]
        self.assertEqual(item["id"], record.public_id)
        self.assertIn("remote_action_status", item)
        self.assertNotIn("result", item)
        self.assertNotIn("lease_token", json.dumps(item))
        self.assertNotIn("synthetic/opaque-reference", json.dumps(item))
        other = Project.objects.create(
            tenant=self.tenant,
            name="Other project",
            slug="other-project",
            created_by=self.requester,
        )
        result = client.get(
            "/api/v1/providers/operations", {"project_id": other.public_id}
        )
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data["data"]["results"], [])
