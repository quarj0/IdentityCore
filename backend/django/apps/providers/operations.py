"""Durable signed provider operations; transport always runs outside SQL locks."""

from contextvars import ContextVar
from datetime import timedelta
import hmac
import secrets

from django.db import transaction
from django.utils import timezone

from apps.audit.services import lock_audit_chain
from apps.evidence.access import protected_value
from apps.evidence.models import SubjectResourceRestriction
from apps.evidence.services import _audit, _transition
from apps.evidence.validation import digest
from apps.providers.adapters import (
    ProviderContractError,
    normalize_provider_result,
    validate_liveness_evidence,
)
from apps.providers.assurance import require_certification, _current_configuration
from apps.providers.configuration import configuration_digest, _signing_context
from apps.providers.http_adapter import (
    SecureHTTPProviderAdapter,
    SecureHTTPAdapterError,
)
from apps.providers.models import ProviderOperation
from apps.providers.services import _lock_provider_consent, _lock_processing_owner
from apps.verifications.models import ProcessingJob
from apps.verifications.processing_jobs import (
    ProcessingJobOwnershipLost,
    ProviderOperationPending,
)
from apps.verifications.transitions import TERMINAL_STATUSES

CONTRACT = "ic-provider-operations-v1"
current_invocation = ContextVar("provider_invocation", default=None)
TERMINAL = {"completed", "failed", "cancelled", "expired"}


def _related():
    return ProviderOperation.objects.select_related(
        "tenant",
        "project",
        "verification__verification_subject",
        "configuration__provider__tenant",
        "configuration__provider__tenant__organization",
        "provider_check__verification",
        "processing_job",
    )


def _live(record):
    if (
        record.deleted_at
        or record.verification.deleted_at
        or record.verification.status in TERMINAL_STATUSES
        or record.verification.expires_at <= timezone.now()
        or record.project.deleted_at
        or record.project.status != "active"
        or record.tenant.deleted_at
        or record.tenant.status != "active"
        or record.verification.verification_subject.deleted_at
        or SubjectResourceRestriction.objects.filter(
            subject_id=record.verification.verification_subject_id
        ).exists()
    ):
        raise ProcessingJobOwnershipLost("Provider operation context is unavailable.")
    _lock_provider_consent(record.provider_check, record.processing_job)
    job = ProcessingJob.objects.select_for_update().get(pk=record.processing_job_id)
    if job.status not in {"processing", "queued"} or job.deleted_at:
        raise ProcessingJobOwnershipLost("Provider operation worker is unavailable.")
    _current_configuration(record.configuration)
    if configuration_digest(record.configuration) != record.configuration_digest:
        raise ProviderContractError("Provider operation configuration changed.")
    require_certification(
        record.configuration,
        record.capability,
        minimum_level=record.configuration.public_configuration_json[
            "required_assurance"
        ],
    )
    return job


def envelope(record):
    return {
        "operation_contract": CONTRACT,
        **record.scope_json,
        "lease_token": protected_value(record, "lease_json")["token"],
    }


@transaction.atomic
def _admit(config, capability, inputs):
    context = current_invocation.get()
    if context is None or context[1] is None:
        raise ProviderContractError(
            "Asynchronous invocation requires a durable worker job."
        )
    check, job = context
    _lock_provider_consent(check, job)
    _lock_processing_owner(job)
    fingerprint = digest(inputs)
    record = _related().filter(provider_check=check).first()
    if record is None:
        if check.verification.project_id is None:
            raise ProviderContractError(
                "Asynchronous invocation requires an explicit project."
            )
        now = timezone.now()
        deadline = now + timedelta(
            seconds=config.public_configuration_json.get(
                "operation_timeout_seconds", 900
            )
        )
        deadline = min(deadline, check.verification.expires_at)
        record = ProviderOperation(
            tenant_id=check.tenant_id,
            project_id=check.verification.project_id,
            verification_id=check.verification_id,
            configuration=config,
            provider_check=check,
            processing_job=job,
            capability=capability,
            request_sha256=fingerprint,
            configuration_digest=configuration_digest(config),
            lease_json={"token": secrets.token_urlsafe(32)},
            lease_generation=job.lease_generation,
            deadline=deadline,
            delete_after=deadline + timedelta(days=1),
            next_poll_at=now,
            transport_lease_until=now,
            scope_json={},
        )
        record.ensure_public_id()
        record.scope_json = {
            "operation_id": record.public_id,
            "configuration_id": config.public_id,
            "tenant_id": check.tenant.public_id,
            "project_id": record.project.public_id,
            "environment": config.environment,
            "capability": capability,
            "contract_version": "1",
            "request_sha256": fingerprint,
            "lease_generation": record.lease_generation,
            "deadline": deadline.isoformat(),
            "callback_path": f"/api/v1/providers/operations/{record.public_id}/callback",
        }
        record.save()
        _audit(record, None, "provider.operation_admitted", capability=capability)
    if (
        record.request_sha256 != fingerprint
        or record.configuration_id != config.pk
        or record.processing_job_id != job.pk
    ):
        raise ProviderContractError("Provider operation request binding changed.")
    _live(record)
    if record.status in {"cancelled", "expired"}:
        raise SecureHTTPAdapterError(
            "Provider operation is unavailable.",
            error_code="provider_operation_" + record.status,
        )
    if record.status in {"completed", "failed"}:
        return record, None
    now = timezone.now()
    if now >= record.deadline:
        _transition(
            record,
            status="expired",
            completed_at=now,
            invalidation_reason="deadline_exceeded",
            lease_json={},
        )
        _audit(record, None, "provider.operation_expired")
        return record, None
    if record.next_poll_at > now or record.transport_lease_until > now:
        raise ProviderOperationPending(job, record.public_id, record.next_poll_at)
    action = "start" if record.status == "created" else "poll"
    # Failed/ambiguous starts repeat the same operation id and fingerprint; providers
    # MUST persist admission idempotently before accepting work.
    _transition(record, transport_lease_until=now + timedelta(seconds=35))
    return record, action


def _validate_response(record, response):
    if not isinstance(response, dict) or set(response) - {
        "binding",
        "status",
        "result",
        "retry_after_seconds",
    }:
        raise ProviderContractError("Invalid operation response fields.")
    binding = response.get("binding")
    expected = envelope(record)
    if not isinstance(binding, dict) or set(binding) != set(expected):
        raise ProviderContractError("Operation result binding is incomplete.")
    if any(
        (type(binding[key]) is not type(value) or binding[key] != value)
        for key, value in expected.items()
        if key != "lease_token"
    ):
        raise ProviderContractError("Operation result binding does not match.")
    if not isinstance(binding.get("lease_token"), str) or not hmac.compare_digest(
        binding["lease_token"], expected["lease_token"]
    ):
        raise ProviderContractError("Operation lease does not match.")
    state = response.get("status")
    if state == "pending":
        delay = response.get("retry_after_seconds", 10)
        if type(delay) is not int or not 5 <= delay <= 300 or "result" in response:
            raise ProviderContractError("Invalid pending operation response.")
        return None, delay
    if state not in {"completed", "failed"} or "retry_after_seconds" in response:
        raise ProviderContractError("Invalid operation completion status.")
    raw = response.get("result")
    if (
        not isinstance(raw, dict)
        or raw.get("contract_version") != "1"
        or raw.get("capability") != record.capability
    ):
        raise ProviderContractError(
            "Operation result capability or version does not match."
        )
    result = normalize_provider_result(record.capability, raw)
    if (state == "failed") != (result["status"] == "failed"):
        raise ProviderContractError("Operation and result status do not match.")
    if record.capability == "liveness" and result["status"] == "completed":
        validate_liveness_evidence(result)
    return result, None


@transaction.atomic
def accept_response(operation_id, response, *, configuration_id=None):
    reference = (
        ProviderOperation.objects.only("tenant_id")
        .filter(public_id=operation_id)
        .first()
    )
    if reference is None:
        raise ProviderContractError("Provider operation is unavailable.")
    lock_audit_chain(reference.tenant_id)
    record = _related().get(public_id=operation_id)
    if configuration_id is not None and record.configuration_id != configuration_id:
        raise ProviderContractError("Provider operation is unavailable.")
    _live(record)
    if record.status in {"cancelled", "expired"} or timezone.now() >= record.deadline:
        raise ProviderContractError(
            "Provider operation is no longer accepting results."
        )
    result, delay = _validate_response(record, response)
    if record.status in {"completed", "failed"}:
        if result is None or digest(result) != record.result_sha256:
            raise ProviderContractError("Conflicting provider operation completion.")
        return record
    now = timezone.now()
    if result is None:
        interval = record.configuration.public_configuration_json.get(
            "poll_interval_seconds", 10
        )
        _transition(
            record,
            status="pending",
            next_poll_at=min(
                record.deadline, now + timedelta(seconds=max(interval, delay))
            ),
            transport_lease_until=now,
        )
    else:
        _transition(
            record,
            status=response["status"],
            result_json=result,
            result_sha256=digest(result),
            completed_at=now,
            transport_lease_until=now,
        )
        _audit(record, None, "provider.operation_completed", outcome=response["status"])
        job = ProcessingJob.objects.get(pk=record.processing_job_id)
        if (
            job.status == "queued"
            and job.error_code == "provider_pending:" + record.public_id
        ):
            job.lease_expires_at = now
            job.save(update_fields=["lease_expires_at", "updated_at"])
    return record


def invoke(config, capability, inputs, *, transfer_inputs, timeout_seconds):
    record, action = _admit(config, capability, inputs)
    if action is not None:
        public = {
            **config.public_configuration_json,
            "timeout_seconds": timeout_seconds,
        }
        try:
            response = SecureHTTPProviderAdapter(public).post_json(
                url=public["endpoint_url"],
                payload={
                    "contract_version": "1",
                    "operation": action,
                    "binding": envelope(record),
                    **(
                        {"inputs": transfer_inputs(inputs)} if action == "start" else {}
                    ),
                },
                headers={
                    "Authorization": "Bearer " + config.credentials_json["api_key"]
                },
                signing=_signing_context(config),
            )
            record = accept_response(
                record.public_id, response, configuration_id=config.pk
            )
        except SecureHTTPAdapterError:
            # An uncertain transport outcome cannot cause a second external job or
            # route fallback. Reconcile the same admitted id on the next worker pass.
            now = timezone.now()
            with transaction.atomic():
                lock_audit_chain(record.tenant_id)
                record = _related().get(pk=record.pk)
                if record.status not in TERMINAL:
                    _transition(
                        record,
                        next_poll_at=now + timedelta(seconds=10),
                        transport_lease_until=now,
                    )
            raise ProviderOperationPending(
                current_invocation.get()[1], record.public_id, record.next_poll_at
            ) from None
    if record.status in {"completed", "failed"}:
        result = protected_value(record, "result_json")
        if digest(result) != record.result_sha256:
            raise ProviderContractError("Provider operation result integrity failed.")
        return result
    if record.status == "expired":
        raise SecureHTTPAdapterError(
            "Provider operation expired.",
            error_code="provider_operation_expired",
            provider_check_status="timeout",
        )
    raise ProviderOperationPending(
        current_invocation.get()[1], record.public_id, record.next_poll_at
    )


def find_operation(job, capability, metadata):
    if job is None:
        return None
    for record in (
        _related()
        .filter(processing_job=job, capability=capability, deleted_at__isnull=True)
        .order_by("-pk")
    ):
        stored = protected_value(record.provider_check, "request_metadata_json")
        route_fields = {
            "provider_route_id",
            "provider_route_version",
            "provider_route_step",
        }
        if {key: value for key, value in stored.items() if key not in route_fields} == (
            metadata or {}
        ):
            return record
    return None
