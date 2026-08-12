import json
import socket
import threading
import time
from datetime import timedelta
from unittest.mock import Mock, call, patch
from urllib.error import HTTPError

from django.db import connection
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.providers.ai_service import (
    AI_SERVICE_UNAVAILABLE_MESSAGE,
    AIServiceUnavailable,
    run_document_quality,
)
from apps.providers.http_adapter import (
    _PinnedHTTPSConnection,
    _resolve_public_addresses,
    SecureHTTPAdapterError,
    SecureHTTPProviderAdapter,
)
from apps.providers.adapters import (
    BUILT_IN_AI_SERVICE,
    BuiltInAIServiceAdapter,
    ProviderContractError,
    ProviderAdapterRegistry,
    normalize_provider_result,
    provider_adapter_registry,
)
from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderAssignment,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderCircuitState,
    ProviderCircuitStatus,
    ProviderAttemptOutcome,
    ProviderRoute,
    ProviderRouteEnvironment,
    ProviderRouteFinalAction,
    ProviderRouteStatus,
    ProviderRouteStep,
    ProviderStatus,
    ProviderType,
)
from apps.providers.services import (
    create_provider_check,
    execute_provider_route,
    invoke_provider_check,
    publish_provider_route,
    ProviderRouteExhausted,
    preserve_provider_result_envelope,
    redact_provider_metadata,
    resolve_provider_chain,
)
from apps.providers.serializers import serialize_provider_check
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus


class ProviderModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Kwame Mensah",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Provider test",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now(),
        )

    def test_create_provider_check_with_matching_provider_type(self):
        provider = Provider.objects.create(
            name="Internal Liveness Engine",
            code="internal-liveness",
            provider_type=ProviderType.LIVENESS,
        )

        check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.COMPLETED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            normalized_result_json={"status": "inconclusive"},
        )

        self.assertTrue(check.public_id.startswith("pck_"))

    def test_provider_configuration_is_encrypted_at_rest(self):
        provider = Provider.objects.create(
            name="SMTP Provider",
            code="smtp-provider",
            provider_type=ProviderType.NOTIFICATION,
            configuration_json={"api_key": "super-secret", "region": "eu-west-1"},
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT configuration_json FROM providers_provider WHERE id = %s",
                [provider.id],
            )
            raw_value = cursor.fetchone()[0]

        if isinstance(raw_value, str):
            raw_value = json.loads(raw_value)
        self.assertEqual(provider.configuration_json["api_key"], "super-secret")
        self.assertEqual(raw_value["__enc__"], "ic-field-v1")
        self.assertNotIn("super-secret", json.dumps(raw_value))

    def test_provider_check_rejects_mismatched_provider_type(self):
        provider = Provider.objects.create(
            name="Notification Gateway",
            code="notify-gateway",
            provider_type=ProviderType.NOTIFICATION,
        )

        with self.assertRaises(ValidationError) as exc:
            ProviderCheck.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                provider=provider,
                check_type=ProviderCheckType.LIVENESS,
                status=ProviderCheckStatus.PENDING,
                started_at=timezone.now(),
            )

        self.assertIn("provider", exc.exception.message_dict)

    def test_completed_provider_check_requires_timestamp(self):
        provider = Provider.objects.create(
            name="Internal Face Match Engine",
            code="internal-face-match",
            provider_type=ProviderType.BIOMETRIC,
        )

        with self.assertRaises(ValidationError) as exc:
            ProviderCheck.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                provider=provider,
                check_type=ProviderCheckType.FACE_MATCH,
                status=ProviderCheckStatus.COMPLETED,
                started_at=timezone.now(),
            )

        self.assertIn("completed_at", exc.exception.message_dict)

    def test_failed_provider_check_allows_completion_timestamp(self):
        provider = Provider.objects.create(
            name="Internal Face Match Engine",
            code="internal-face-match-failed",
            provider_type=ProviderType.BIOMETRIC,
        )

        check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.FACE_MATCH,
            status=ProviderCheckStatus.FAILED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            error_code="provider_unavailable",
        )

        self.assertEqual(check.status, ProviderCheckStatus.FAILED)

    def test_tenant_assignment_routes_provider_checks_to_byo_provider(self):
        tenant_provider = Provider.objects.create(
            tenant=self.tenant,
            name="Tenant OCR Engine",
            code="tenant-ocr-engine",
            provider_type=ProviderType.DOCUMENT,
        )
        ProviderAssignment.objects.create(
            tenant=self.tenant,
            assignment_key=ProviderCheckType.DOCUMENT_OCR,
            provider=tenant_provider,
        )

        check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            normalized_result={"status": "completed"},
        )

        self.assertEqual(check.provider_id, tenant_provider.id)

    def test_orchestrator_records_normalized_success_duration_and_redacted_metadata(
        self,
    ):
        check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.PENDING,
        )

        result = invoke_provider_check(
            provider_check=check,
            operation=lambda **kwargs: {
                "status": "completed",
                "confidence_score": 0.91,
                "model_name": "test-model",
            },
            operation_kwargs={"api_key": "never-record-this"},
            request_metadata={"capture_id": "cap_123", "api_key": "secret"},
        )

        check.refresh_from_db()
        self.assertEqual(result["confidence_score"], 0.91)
        self.assertEqual(result["contract_version"], "1")
        self.assertEqual(result["capability"], ProviderCheckType.DOCUMENT_OCR)
        self.assertEqual(check.status, ProviderCheckStatus.COMPLETED)
        self.assertIsNotNone(check.duration_ms)
        self.assertEqual(check.request_metadata_json["api_key"], "[REDACTED]")
        self.assertEqual(check.response_metadata_json["model_name"], "test-model")
        self.assertNotIn("confidence_score", check.response_metadata_json)

    def test_orchestrator_normalizes_timeout_before_reraising(self):
        check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_QUALITY,
            status=ProviderCheckStatus.PENDING,
        )

        with self.assertRaises(AIServiceUnavailable):
            invoke_provider_check(
                provider_check=check,
                operation=Mock(
                    side_effect=AIServiceUnavailable(
                        error_code="provider_timeout",
                        provider_check_status="timeout",
                    )
                ),
                operation_kwargs={},
            )

        check.refresh_from_db()
        self.assertEqual(check.status, ProviderCheckStatus.TIMEOUT)
        self.assertEqual(
            check.normalized_result_json["error"]["code"], "provider_timeout"
        )
        self.assertTrue(check.normalized_result_json["error"]["retryable"])
        self.assertEqual(check.normalized_result_json["contract_version"], "1")
        self.assertEqual(
            check.normalized_result_json["capability"],
            ProviderCheckType.DOCUMENT_QUALITY,
        )
        self.assertIsNotNone(check.duration_ms)

    def test_workflow_result_preserves_normalized_provider_envelope(self):
        check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.PENDING,
        )
        invoke_provider_check(
            provider_check=check,
            operation=lambda: {
                "status": "completed",
                "confidence_score": 0.91,
            },
            operation_kwargs={},
        )
        check.refresh_from_db()

        persisted = preserve_provider_result_envelope(
            check,
            workflow_result={"status": "processed"},
        )

        self.assertEqual(persisted["contract_version"], "1")
        self.assertEqual(persisted["capability"], ProviderCheckType.DOCUMENT_OCR)
        self.assertEqual(persisted["status"], "completed")
        self.assertEqual(persisted["workflow_result"], {"status": "processed"})

    def test_redaction_is_recursive(self):
        self.assertEqual(
            redact_provider_metadata({"nested": [{"token": "secret"}]}),
            {"nested": [{"token": "[REDACTED]"}]},
        )


class ProviderRouteTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Route Organization", slug="route-organization"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Route Tenant",
            slug="route-tenant",
            status="active",
        )
        self.providers = [
            Provider.objects.create(
                tenant=self.tenant,
                name=f"Route Provider {index}",
                code=f"route-provider-{index}",
                provider_type=ProviderType.DOCUMENT,
                status=ProviderStatus.ACTIVE,
            )
            for index in range(1, 4)
        ]

    def create_route(
        self,
        *,
        route_key,
        providers,
        version=1,
        environment=ProviderRouteEnvironment.SANDBOX,
        capability=ProviderCheckType.DOCUMENT_OCR,
        priority=100,
        countries=None,
        document_types=None,
        workflows=None,
        **policy,
    ):
        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key=route_key,
            name=route_key.replace("-", " ").title(),
            version=version,
            environment=environment,
            capability=capability,
            priority=priority,
            country_codes_json=countries or [],
            document_type_ids_json=document_types or [],
            workflow_public_ids_json=workflows or [],
            **policy,
        )
        for position, provider in enumerate(providers, start=1):
            ProviderRouteStep.objects.create(
                route=route,
                provider=provider,
                position=position,
            )
        return publish_provider_route(route)

    def test_resolution_applies_all_conditions_and_deterministic_specificity(self):
        self.create_route(
            route_key="wildcard",
            providers=[self.providers[0]],
            priority=1,
        )
        self.create_route(
            route_key="ghana",
            providers=[self.providers[1]],
            countries=["gh"],
        )
        self.create_route(
            route_key="ghana-national-id",
            providers=[self.providers[1], self.providers[0]],
            countries=["GH"],
            document_types=["national_id"],
        )
        most_specific = self.create_route(
            route_key="ghana-national-id-onboarding",
            providers=[self.providers[2], self.providers[1]],
            priority=500,
            countries=["GH"],
            document_types=["national_id"],
            workflows=["wfl_onboarding"],
        )

        resolution = resolve_provider_chain(
            tenant=self.tenant,
            environment=ProviderRouteEnvironment.SANDBOX,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            country_code="gh",
            document_type="national_id",
            workflow_public_id="wfl_onboarding",
        )

        self.assertEqual(resolution.route, most_specific)
        self.assertEqual(resolution.providers, (self.providers[2], self.providers[1]))

        document_resolution = resolve_provider_chain(
            tenant=self.tenant,
            environment=ProviderRouteEnvironment.SANDBOX,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            country_code="GH",
            document_type="national_id",
            workflow_public_id="wfl_other",
        )
        self.assertEqual(document_resolution.route.route_key, "ghana-national-id")

        country_resolution = resolve_provider_chain(
            tenant=self.tenant,
            environment=ProviderRouteEnvironment.SANDBOX,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            country_code="GH",
            document_type="passport",
        )
        self.assertEqual(country_resolution.route.route_key, "ghana")

        wildcard_resolution = resolve_provider_chain(
            tenant=self.tenant,
            environment=ProviderRouteEnvironment.SANDBOX,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            country_code="NG",
        )
        self.assertEqual(wildcard_resolution.route.route_key, "wildcard")

    def test_ties_resolve_by_priority_then_route_key(self):
        self.create_route(
            route_key="zulu-route",
            providers=[self.providers[0]],
            priority=20,
            countries=["GH"],
        )
        selected = self.create_route(
            route_key="alpha-route",
            providers=[self.providers[1]],
            priority=10,
            countries=["GH"],
        )
        self.create_route(
            route_key="beta-route",
            providers=[self.providers[2]],
            priority=10,
            countries=["GH"],
        )

        resolution = resolve_provider_chain(
            tenant=self.tenant,
            environment=ProviderRouteEnvironment.SANDBOX,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            country_code="GH",
        )

        self.assertEqual(resolution.route, selected)

    def test_routes_are_tenant_and_environment_scoped(self):
        production = self.create_route(
            route_key="production-only",
            providers=[self.providers[0]],
            environment=ProviderRouteEnvironment.PRODUCTION,
        )
        other_organization = Organization.objects.create(
            name="Other Route Organization", slug="other-route-organization"
        )
        other_tenant = Tenant.objects.create(
            organization=other_organization,
            name="Other Route Tenant",
            slug="other-route-tenant",
            status="active",
        )

        production_resolution = resolve_provider_chain(
            tenant=self.tenant,
            environment=ProviderRouteEnvironment.PRODUCTION,
            check_type=ProviderCheckType.DOCUMENT_OCR,
        )
        sandbox_resolution = resolve_provider_chain(
            tenant=self.tenant,
            environment=ProviderRouteEnvironment.SANDBOX,
            check_type=ProviderCheckType.DOCUMENT_OCR,
        )
        foreign_resolution = resolve_provider_chain(
            tenant=other_tenant,
            environment=ProviderRouteEnvironment.PRODUCTION,
            check_type=ProviderCheckType.DOCUMENT_OCR,
        )

        self.assertEqual(production_resolution.route, production)
        self.assertIsNone(sandbox_resolution.route)
        self.assertIsNone(foreign_resolution.route)
        self.assertNotIn(self.providers[0], foreign_resolution.providers)

    def test_publishing_new_version_retires_and_freezes_previous_version(self):
        first = self.create_route(
            route_key="versioned-route",
            providers=[self.providers[0]],
        )
        second = self.create_route(
            route_key="versioned-route",
            providers=[self.providers[1]],
            version=2,
        )

        first.refresh_from_db()
        self.assertEqual(first.status, ProviderRouteStatus.RETIRED)
        self.assertEqual(second.status, ProviderRouteStatus.ACTIVE)
        first.priority = 1
        with self.assertRaisesRegex(ValidationError, "immutable"):
            first.save()

        second.status = ProviderRouteStatus.DRAFT
        with self.assertRaisesRegex(ValidationError, "immutable"):
            second.save()

    def test_publication_revalidates_and_rejects_deleted_configuration(self):
        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="invalid-draft",
            name="Invalid draft",
            environment=ProviderRouteEnvironment.SANDBOX,
            capability=ProviderCheckType.DOCUMENT_OCR,
        )
        ProviderRouteStep.objects.create(
            route=route,
            provider=self.providers[0],
            position=1,
        )
        route.capability = ProviderCheckType.LIVENESS
        route.save()

        with self.assertRaises(ValidationError):
            publish_provider_route(route)

        route.capability = ProviderCheckType.DOCUMENT_OCR
        route.save()
        route.soft_delete()
        with self.assertRaisesRegex(ValidationError, "Deleted provider routes"):
            publish_provider_route(route)

    def test_draft_cannot_bypass_publication_and_published_steps_cannot_move(self):
        route = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="guarded-route",
            name="Guarded route",
            environment=ProviderRouteEnvironment.SANDBOX,
            capability=ProviderCheckType.DOCUMENT_OCR,
        )
        step = ProviderRouteStep.objects.create(
            route=route,
            provider=self.providers[0],
            position=1,
        )
        route.status = ProviderRouteStatus.ACTIVE
        with self.assertRaisesRegex(ValidationError, "publication service"):
            route.save()

        published = publish_provider_route(ProviderRoute.objects.get(pk=route.pk))
        replacement = ProviderRoute.objects.create(
            tenant=self.tenant,
            route_key="replacement-route",
            name="Replacement route",
            environment=ProviderRouteEnvironment.SANDBOX,
            capability=ProviderCheckType.DOCUMENT_OCR,
        )
        step.route = replacement
        with self.assertRaisesRegex(ValidationError, "immutable"):
            step.save()
        self.assertEqual(published.status, ProviderRouteStatus.ACTIVE)

    def test_provider_check_records_selected_route_version(self):
        selected = self.create_route(
            route_key="verification-route",
            providers=[self.providers[1], self.providers[0]],
            countries=["GH"],
            document_types=["national_id"],
            workflows=["wfl_onboarding"],
        )
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Route Subject",
        )
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Route check",
            workflow_snapshot_json={"workflow_id": "wfl_onboarding"},
            expires_at=timezone.now(),
        )
        verification.identity_documents.create(
            tenant=self.tenant,
            verification_subject=subject,
            document_type_id="national_id",
            country_profile_id="GH",
        )

        check = create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.PENDING,
        )

        self.assertEqual(check.provider, self.providers[1])
        self.assertEqual(
            check.request_metadata_json["provider_route_id"], selected.public_id
        )
        self.assertEqual(check.request_metadata_json["provider_route_version"], 1)
        self.assertEqual(check.request_metadata_json["provider_route_step"], 1)

    def test_provider_check_records_actual_enabled_step_and_keeps_route_metadata(self):
        selected = self.create_route(
            route_key="disabled-first-step",
            providers=[self.providers[0], self.providers[1]],
        )
        self.providers[0].status = ProviderStatus.DISABLED
        self.providers[0].save(update_fields=["status", "updated_at"])
        verification = self.create_processing_verification()

        check = create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.PENDING,
        )
        invoke_provider_check(
            provider_check=check,
            operation=lambda: {"status": "completed"},
            operation_kwargs={},
            request_metadata={"identity_document_id": "doc_example"},
        )

        self.assertEqual(check.provider, self.providers[1])
        self.assertEqual(
            check.request_metadata_json["provider_route_id"], selected.public_id
        )
        self.assertEqual(check.request_metadata_json["provider_route_step"], 2)
        self.assertEqual(
            check.request_metadata_json["identity_document_id"], "doc_example"
        )

    def create_processing_verification(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Route Execution Subject",
        )
        return Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Route execution",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_execution_retries_then_falls_back_with_explainable_history(self):
        route = self.create_route(
            route_key="resilient-route",
            providers=[self.providers[0], self.providers[1]],
            timeout_seconds=7,
            max_attempts_per_provider=2,
            circuit_failure_threshold=2,
        )
        verification = self.create_processing_verification()
        calls = []

        def operation(provider, timeout_seconds):
            calls.append((provider.public_id, timeout_seconds))
            if provider == self.providers[0]:
                raise AIServiceUnavailable(
                    "secret upstream detail",
                    error_code="provider_timeout",
                    provider_check_status=ProviderCheckStatus.TIMEOUT,
                )
            return {"status": "completed", "confidence_score": 0.93}

        execution = execute_provider_route(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=operation,
        )

        self.assertEqual(
            calls,
            [
                (self.providers[0].public_id, 7),
                (self.providers[0].public_id, 7),
                (self.providers[1].public_id, 7),
            ],
        )
        self.assertEqual(execution.provider_check.provider, self.providers[1])
        self.assertEqual(
            [attempt.outcome for attempt in execution.attempts],
            [
                ProviderAttemptOutcome.TIMEOUT,
                ProviderAttemptOutcome.TIMEOUT,
                ProviderAttemptOutcome.SUCCEEDED,
            ],
        )
        self.assertEqual(
            [attempt.fallback_reason for attempt in execution.attempts],
            ["retryable_error", "provider_fallback", ""],
        )
        self.assertTrue(execution.attempts[0].retryable)
        self.assertNotIn(
            "secret upstream detail",
            execution.attempts[0].provider_check.error_message,
        )
        circuit = ProviderCircuitState.objects.get(
            route_step__route=route,
            route_step__provider=self.providers[0],
        )
        self.assertEqual(circuit.status, ProviderCircuitStatus.OPEN)
        serialized = serialize_provider_check(execution.attempts[0].provider_check)
        self.assertEqual(
            serialized["execution_attempt"]["execution_id"],
            execution.attempts[0].execution_id,
        )

    def test_open_circuit_skips_then_allows_one_recovery_probe(self):
        route = self.create_route(
            route_key="circuit-route",
            providers=[self.providers[0], self.providers[1]],
            max_attempts_per_provider=1,
            circuit_failure_threshold=1,
            circuit_recovery_seconds=30,
        )
        verification = self.create_processing_verification()

        def fail_primary(provider, timeout_seconds):
            if provider == self.providers[0]:
                raise AIServiceUnavailable(error_code="provider_unavailable")
            return {"status": "completed"}

        execute_provider_route(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=fail_primary,
        )
        skipped = execute_provider_route(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=lambda provider, timeout: {"status": "completed"},
        )
        self.assertEqual(skipped.attempts[0].outcome, ProviderAttemptOutcome.SKIPPED)
        self.assertEqual(skipped.attempts[0].fallback_reason, "circuit_open")
        self.assertEqual(skipped.provider_check.provider, self.providers[1])

        circuit = ProviderCircuitState.objects.get(
            route_step__route=route,
            route_step__provider=self.providers[0],
        )
        circuit.retry_after = timezone.now() - timedelta(seconds=1)
        circuit.save(update_fields=["retry_after", "updated_at"])
        recovered_calls = []
        recovered = execute_provider_route(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=lambda provider, timeout: (
                recovered_calls.append(provider.public_id) or {"status": "completed"}
            ),
        )
        circuit.refresh_from_db()
        self.assertEqual(recovered.provider_check.provider, self.providers[0])
        self.assertEqual(recovered_calls, [self.providers[0].public_id])
        self.assertEqual(circuit.status, ProviderCircuitStatus.CLOSED)
        self.assertEqual(circuit.consecutive_failures, 0)

    def test_failed_half_open_probe_does_not_retry_and_stale_claim_recovers(self):
        route = self.create_route(
            route_key="half-open-route",
            providers=[self.providers[0], self.providers[1]],
            max_attempts_per_provider=3,
            circuit_failure_threshold=1,
            circuit_recovery_seconds=30,
        )
        step = route.steps.get(provider=self.providers[0])
        ProviderCircuitState.objects.create(
            route_step=step,
            status=ProviderCircuitStatus.HALF_OPEN,
            consecutive_failures=1,
            retry_after=timezone.now() - timedelta(seconds=1),
        )
        verification = self.create_processing_verification()
        calls = []

        execution = execute_provider_route(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=lambda provider, timeout: (
                calls.append(provider.public_id)
                or (
                    (_ for _ in ()).throw(
                        AIServiceUnavailable(error_code="provider_timeout")
                    )
                    if provider == self.providers[0]
                    else {"status": "completed"}
                )
            ),
        )

        self.assertEqual(
            calls, [self.providers[0].public_id, self.providers[1].public_id]
        )
        self.assertEqual(execution.provider_check.provider, self.providers[1])

    def test_nonretryable_response_resets_closed_circuit_failure_streak(self):
        route = self.create_route(
            route_key="reset-streak-route",
            providers=[self.providers[0]],
            max_attempts_per_provider=1,
            circuit_failure_threshold=3,
            final_action=ProviderRouteFinalAction.FAIL,
        )
        step = route.steps.get(provider=self.providers[0])
        circuit = ProviderCircuitState.objects.create(
            route_step=step,
            status=ProviderCircuitStatus.CLOSED,
            consecutive_failures=1,
        )
        verification = self.create_processing_verification()

        with self.assertRaises(ProviderRouteExhausted):
            execute_provider_route(
                verification=verification,
                check_type=ProviderCheckType.DOCUMENT_OCR,
                operation=lambda provider, timeout: (_ for _ in ()).throw(
                    AIServiceUnavailable(
                        error_code="provider_invalid_response", retryable=False
                    )
                ),
            )

        circuit.refresh_from_db()
        self.assertEqual(circuit.status, ProviderCircuitStatus.CLOSED)
        self.assertEqual(circuit.consecutive_failures, 0)

    def test_route_exhaustion_applies_manual_review_without_exception_details(self):
        route = self.create_route(
            route_key="manual-route",
            providers=[self.providers[0], self.providers[1]],
            max_attempts_per_provider=1,
            final_action=ProviderRouteFinalAction.MANUAL_REVIEW,
        )
        verification = self.create_processing_verification()

        with self.assertRaises(ProviderRouteExhausted) as exc:
            execute_provider_route(
                verification=verification,
                check_type=ProviderCheckType.DOCUMENT_OCR,
                operation=lambda provider, timeout: (_ for _ in ()).throw(
                    AIServiceUnavailable(
                        "private provider response",
                        error_code="provider_unavailable",
                    )
                ),
            )

        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED)
        self.assertEqual(
            exc.exception.final_action, ProviderRouteFinalAction.MANUAL_REVIEW
        )
        decision = verification.decision_record
        self.assertEqual(decision.reason_code, "provider_route_exhausted")
        self.assertEqual(
            decision.evidence_summary_json["provider_route_id"], route.public_id
        )
        self.assertNotIn(
            "private provider response", json.dumps(decision.evidence_summary_json)
        )
        attempts = list(route.execution_attempts.order_by("sequence"))
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[-1].fallback_reason, "route_exhausted")

    def test_route_can_fail_verification_after_nonretryable_error(self):
        self.create_route(
            route_key="fail-route",
            providers=[self.providers[0]],
            max_attempts_per_provider=3,
            final_action=ProviderRouteFinalAction.FAIL,
        )
        verification = self.create_processing_verification()
        calls = []

        with self.assertRaises(ProviderRouteExhausted):
            execute_provider_route(
                verification=verification,
                check_type=ProviderCheckType.DOCUMENT_OCR,
                operation=lambda provider, timeout: (
                    calls.append(provider.public_id)
                    or (_ for _ in ()).throw(
                        AIServiceUnavailable(
                            error_code="provider_invalid_response",
                            retryable=False,
                        )
                    )
                ),
            )

        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.FAILED)
        self.assertEqual(calls, [self.providers[0].public_id])


class AIServiceClientTests(TestCase):
    @override_settings(
        AI_SERVICE_BASE_URL="http://ai-service:8001",
        AI_SERVICE_TIMEOUT_SECONDS=1,
        AI_SERVICE_SHARED_TOKEN="shared-token",
    )
    @patch("apps.providers.ai_service.request.urlopen")
    def test_http_error_returns_human_ready_unavailable_error(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            url="http://ai-service:8001/v1/document/quality",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=Mock(read=Mock(return_value=b'{"detail":"models missing"}')),
        )

        with self.assertRaises(AIServiceUnavailable) as exc:
            run_document_quality(
                verification_id="ver_123",
                document_storage_key="documents/front.jpg",
            )

        self.assertEqual(str(exc.exception), AI_SERVICE_UNAVAILABLE_MESSAGE)
        self.assertEqual(exc.exception.error_code, "provider_http_503")
        self.assertEqual(exc.exception.reason, "models missing")
        self.assertTrue(exc.exception.retryable)

    @override_settings(AI_SERVICE_BASE_URL="http://ai-service:8001")
    @patch("apps.providers.ai_service.request.urlopen")
    def test_client_error_is_explicitly_nonretryable(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            url="http://ai-service:8001/v1/document/quality",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=Mock(read=Mock(return_value=b'{"detail":"invalid input"}')),
        )

        with self.assertRaises(AIServiceUnavailable) as exc:
            run_document_quality(
                verification_id="ver_123",
                document_storage_key="documents/front.jpg",
            )

        self.assertEqual(exc.exception.error_code, "provider_http_400")
        self.assertFalse(exc.exception.retryable)

    @override_settings(AI_SERVICE_BASE_URL="http://ai-service:8001")
    @patch("apps.providers.ai_service.request.urlopen")
    def test_invalid_json_returns_human_ready_unavailable_error(self, mock_urlopen):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b"InvalidTag"
        mock_urlopen.return_value = response

        with self.assertRaises(AIServiceUnavailable) as exc:
            run_document_quality(
                verification_id="ver_123",
                document_storage_key="documents/front.jpg",
            )

        self.assertEqual(str(exc.exception), AI_SERVICE_UNAVAILABLE_MESSAGE)
        self.assertEqual(exc.exception.error_code, "provider_invalid_response")

    @override_settings(AI_SERVICE_BASE_URL="http://ai-service:8001")
    @patch("apps.providers.ai_service.request.urlopen")
    def test_timeout_returns_timeout_provider_status(self, mock_urlopen):
        mock_urlopen.side_effect = socket.timeout("timed out")

        with self.assertRaises(AIServiceUnavailable) as exc:
            run_document_quality(
                verification_id="ver_123",
                document_storage_key="documents/front.jpg",
            )

        self.assertEqual(str(exc.exception), AI_SERVICE_UNAVAILABLE_MESSAGE)
        self.assertEqual(exc.exception.error_code, "provider_timeout")
        self.assertEqual(exc.exception.provider_check_status, "timeout")


class ProviderAdapterRegistryTests(TestCase):
    def test_builtin_adapter_exposes_all_five_capabilities(self):
        adapter = provider_adapter_registry.resolve(BUILT_IN_AI_SERVICE)

        self.assertIsInstance(adapter, BuiltInAIServiceAdapter)
        self.assertTrue(callable(adapter.document_quality))
        self.assertTrue(callable(adapter.document_classification))
        self.assertTrue(callable(adapter.document_ocr))
        self.assertTrue(callable(adapter.liveness))
        self.assertTrue(callable(adapter.face_compare))

    def test_registry_resolves_custom_adapter_factory(self):
        adapter = object()
        registry = ProviderAdapterRegistry()
        registry.register("custom", lambda: adapter)

        self.assertIs(registry.resolve("custom"), adapter)

    def test_registry_rejects_unknown_adapter(self):
        with self.assertRaisesRegex(LookupError, "missing"):
            ProviderAdapterRegistry().resolve("missing")

    def test_builtin_contract_accepts_each_declared_capability(self):
        capabilities = (
            "document_quality",
            "document_classification",
            "document_ocr",
            "liveness",
            "face_compare",
        )
        adapter = provider_adapter_registry.resolve(BUILT_IN_AI_SERVICE)

        for capability in capabilities:
            with self.subTest(capability=capability):
                self.assertTrue(callable(getattr(adapter, capability)))
                result = normalize_provider_result(
                    capability,
                    {
                        "contract_version": "1",
                        "status": "completed",
                        "outcome": "conformance_fixture_passed",
                    },
                )
                self.assertEqual(result["contract_version"], "1")
                self.assertEqual(result["capability"], capability)

    def test_contract_rejects_malformed_and_unsupported_version_results(self):
        invalid_results = (
            [],
            {"contract_version": "1"},
            {"status": "unexpected"},
            {"contract_version": "999", "status": "completed"},
        )

        for result in invalid_results:
            with self.subTest(result=result), self.assertRaises(ProviderContractError):
                normalize_provider_result("document_ocr", result)

        with self.assertRaises(ProviderContractError) as caught:
            normalize_provider_result(
                "document_ocr",
                {"contract_version": "999", "status": "completed"},
            )
        self.assertEqual(
            caught.exception.error_code, "provider_contract_version_unsupported"
        )


class SecureHTTPProviderAdapterTests(TestCase):
    def adapter(self):
        return SecureHTTPProviderAdapter(
            {"allowed_hosts": ["provider.example.com"], "timeout_seconds": 5}
        )

    @patch(
        "apps.providers.http_adapter.socket.getaddrinfo",
        return_value=[
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 443),
            )
        ],
    )
    @patch("apps.providers.http_adapter._PinnedHTTPSConnection")
    def test_post_json_enforces_json_and_bounds_response(
        self, connection_class, getaddrinfo
    ):
        connection = connection_class.return_value
        connection.sock = Mock()
        response = Mock()
        response.status = 200
        response.headers.get_content_type.return_value = "application/json"
        response.read1.side_effect = [b'{"status":"ok"}', b""]
        connection.getresponse.return_value = response

        result = self.adapter().post_json(
            url="https://provider.example.com/check", payload={"id": "ver_123"}
        )

        self.assertEqual(result, {"status": "ok"})
        getaddrinfo.assert_called_once_with(
            "provider.example.com",
            443,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
        self.assertEqual(
            connection_class.call_args.kwargs["endpoints"],
            ((socket.AF_INET, ("8.8.8.8", 443)),),
        )
        connection.request.assert_called_once_with(
            "POST",
            "/check",
            body=b'{"id":"ver_123"}',
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    def test_blocks_private_destinations_and_non_https_urls(self):
        with self.assertRaisesRegex(SecureHTTPAdapterError, "HTTPS"):
            self.adapter().post_json(
                url="http://provider.example.com/check", payload={}
            )
        with self.assertRaisesRegex(SecureHTTPAdapterError, "allowlisted"):
            self.adapter().post_json(url="https://other.example.com/check", payload={})

    @patch(
        "apps.providers.http_adapter.socket.getaddrinfo",
        return_value=[
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 443),
            )
        ],
    )
    @patch("apps.providers.http_adapter._PinnedHTTPSConnection")
    def test_timeout_is_explicitly_retryable(self, connection_class, getaddrinfo):
        connection_class.return_value.request.side_effect = socket.timeout(
            "private detail"
        )

        with self.assertRaises(SecureHTTPAdapterError) as exc:
            self.adapter().post_json(
                url="https://provider.example.com/check", payload={}
            )

        self.assertEqual(exc.exception.error_code, "provider_timeout")
        self.assertTrue(exc.exception.retryable)
        self.assertEqual(exc.exception.provider_check_status, "timeout")
        self.assertEqual(exc.exception.public_message, "Provider invocation failed.")

    @patch(
        "apps.providers.http_adapter.socket.getaddrinfo",
        return_value=[
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 443),
            )
        ],
    )
    def test_blocks_private_dns_resolution(self, getaddrinfo):
        with self.assertRaisesRegex(SecureHTTPAdapterError, "private"):
            self.adapter().post_json(
                url="https://provider.example.com/check", payload={}
            )

    def test_rejects_malformed_port(self):
        with self.assertRaises(SecureHTTPAdapterError) as exc:
            self.adapter().post_json(
                url="https://provider.example.com:not-a-port/check", payload={}
            )

        self.assertEqual(exc.exception.error_code, "provider_url_invalid")

    @patch("apps.providers.http_adapter.socket.socket")
    @patch("apps.providers.http_adapter.ssl.create_default_context")
    def test_pinned_connection_uses_vetted_ip_and_original_hostname_for_tls(
        self, create_default_context, socket_factory
    ):
        raw_socket = socket_factory.return_value
        tls_socket = Mock()
        create_default_context.return_value.wrap_socket.return_value = tls_socket
        connection = _PinnedHTTPSConnection(
            "provider.example.com",
            443,
            endpoints=((socket.AF_INET, ("8.8.8.8", 443)),),
            deadline=time.monotonic() + 3,
        )

        connection.connect()

        raw_socket.connect.assert_called_once_with(("8.8.8.8", 443))
        create_default_context.return_value.wrap_socket.assert_called_once_with(
            raw_socket,
            server_hostname="provider.example.com",
        )
        self.assertIs(connection.sock, tls_socket)

    @patch(
        "apps.providers.http_adapter.time.monotonic",
        side_effect=[0.0, 1.0, 2.0, 3.0],
    )
    @patch("apps.providers.http_adapter.socket.socket")
    @patch("apps.providers.http_adapter.ssl.create_default_context")
    def test_pinned_connection_recomputes_deadline_for_each_endpoint(
        self, create_default_context, socket_factory, monotonic
    ):
        first_socket = Mock()
        first_socket.connect.side_effect = socket.timeout("first endpoint timed out")
        second_socket = Mock()
        socket_factory.side_effect = [first_socket, second_socket]
        connection = _PinnedHTTPSConnection(
            "provider.example.com",
            443,
            endpoints=(
                (socket.AF_INET, ("8.8.8.8", 443)),
                (socket.AF_INET, ("8.8.4.4", 443)),
            ),
            deadline=10.0,
        )

        connection.connect()

        first_socket.settimeout.assert_called_once_with(9.0)
        first_socket.close.assert_called_once()
        self.assertEqual(
            second_socket.settimeout.call_args_list,
            [call(8.0), call(7.0)],
        )
        second_socket.connect.assert_called_once_with(("8.8.4.4", 443))
        create_default_context.return_value.wrap_socket.assert_called_once_with(
            second_socket,
            server_hostname="provider.example.com",
        )

    @patch("apps.providers.http_adapter.socket.getaddrinfo")
    def test_dns_resolution_is_bounded_by_request_deadline(self, getaddrinfo):
        release_resolution = threading.Event()
        getaddrinfo.side_effect = lambda *args, **kwargs: (
            release_resolution.wait(timeout=1) or []
        )
        try:
            with self.assertRaises(SecureHTTPAdapterError) as exc:
                _resolve_public_addresses(
                    "provider.example.com",
                    443,
                    deadline=time.monotonic() + 0.01,
                )
        finally:
            release_resolution.set()

        self.assertEqual(exc.exception.error_code, "provider_timeout")
        self.assertTrue(exc.exception.retryable)

    @patch("apps.providers.http_adapter.threading.Timer")
    @patch("apps.providers.http_adapter._PinnedHTTPSConnection")
    @patch(
        "apps.providers.http_adapter._resolve_public_addresses",
        return_value=((socket.AF_INET, ("8.8.8.8", 443)),),
    )
    @patch(
        "apps.providers.http_adapter.time.monotonic",
        side_effect=[0.0, 0.1, 0.2, 0.3, 0.4, 5.1],
    )
    def test_absolute_deadline_applies_while_response_is_streaming(
        self,
        monotonic,
        resolve_public_addresses,
        connection_class,
        timer_class,
    ):
        connection = connection_class.return_value
        connection.sock = Mock()
        response = connection.getresponse.return_value
        response.status = 200
        response.headers.get_content_type.return_value = "application/json"
        response.read1.return_value = b'{"status":"ok"}'

        with self.assertRaises(SecureHTTPAdapterError) as exc:
            self.adapter().post_json(
                url="https://provider.example.com/check", payload={}
            )

        self.assertEqual(exc.exception.error_code, "provider_timeout")
        self.assertTrue(exc.exception.retryable)
        timer_class.return_value.cancel.assert_called_once()
