import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)
from apps.verifications.transitions import TERMINAL_STATUSES, transition_verification

logger = logging.getLogger(__name__)

COMMITTED_PROVIDER_RESULT_RECOVERY = "committed_provider_result_recovery"
COMMITTED_PROVIDER_RESULT_RECOVERY_CONSUMED = (
    "committed_provider_result_recovery_consumed"
)


class ProcessingJobOwnershipLost(RuntimeError):
    """Raised when a worker no longer owns the durable processing lease."""


def _lease_deadline(now=None):
    return (now or timezone.now()) + timedelta(
        seconds=settings.PROCESSING_JOB_LEASE_SECONDS
    )


def _assert_processing_job_owner(
    locked: ProcessingJob, owner: ProcessingJob
) -> None:
    if (
        locked.status != ProcessingJobStatus.PROCESSING
        or locked.attempt_count != owner.attempt_count
    ):
        raise ProcessingJobOwnershipLost(
            f"Processing job {locked.public_id} is owned by another attempt."
        )


def lock_processing_job_for_finalization(job: ProcessingJob) -> ProcessingJob:
    """Lock and validate a job before any verification finalization writes."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError(
            "Processing-job finalization ownership must be checked inside an atomic block."
        )
    locked = ProcessingJob.objects.select_for_update().get(pk=job.pk)
    _assert_processing_job_owner(locked, job)
    return locked


def enqueue_processing_job(*, job_type: str, resource) -> ProcessingJob:
    """Persist work before dispatch so a lost broker message remains recoverable."""
    now = timezone.now()
    job, created = ProcessingJob.objects.get_or_create(
        job_type=job_type,
        resource_public_id=resource.public_id,
        defaults={
            "tenant": resource.tenant,
            "verification": resource.verification,
            "status": ProcessingJobStatus.QUEUED,
            "max_attempts": settings.PROCESSING_JOB_MAX_ATTEMPTS,
            "lease_expires_at": now,
        },
    )
    if created or job.status == ProcessingJobStatus.QUEUED:
        transaction.on_commit(lambda: dispatch_processing_job(job.public_id))
    return job


def queue_identity_document_processing(identity_document) -> ProcessingJob:
    return enqueue_processing_job(
        job_type=ProcessingJobType.IDENTITY_DOCUMENT,
        resource=identity_document,
    )


def queue_biometrics_processing(liveness_check) -> ProcessingJob:
    return enqueue_processing_job(
        job_type=ProcessingJobType.BIOMETRICS,
        resource=liveness_check,
    )


def dispatch_processing_job(job_public_id: str) -> bool:
    """Reserve a dispatch window before publishing one resource-only message."""
    with transaction.atomic():
        job = ProcessingJob.objects.select_for_update().get(public_id=job_public_id)
        if job.status != ProcessingJobStatus.QUEUED:
            return False
        job.lease_expires_at = _lease_deadline()
        job.save(update_fields=["lease_expires_at", "updated_at"])

    try:
        if job.job_type == ProcessingJobType.IDENTITY_DOCUMENT:
            from apps.identity_documents.tasks import process_identity_document_task

            process_identity_document_task.delay(job.resource_public_id)
        elif job.job_type == ProcessingJobType.BIOMETRICS:
            from apps.biometrics.tasks import process_verification_biometrics_task

            process_verification_biometrics_task.delay(job.resource_public_id)
        else:  # pragma: no cover - protected by model choices
            raise ValueError("Unsupported processing job type.")
    except Exception:
        ProcessingJob.objects.filter(
            pk=job.pk,
            status=ProcessingJobStatus.QUEUED,
        ).update(lease_expires_at=timezone.now())
        logger.exception("Failed to dispatch processing job %s.", job.public_id)
        return False
    return True


def _provider_check_is_reusable(check) -> bool:
    from apps.providers.models import ProviderCheckStatus

    return bool(
        check
        and check.status == ProviderCheckStatus.COMPLETED
        and check.normalized_result_json
    )


def _repair_biometric_provider_check_links(resource) -> bool:
    """Relink/reuse committed provider evidence before biometric redelivery."""
    from apps.biometrics.models import FaceMatchStatus, LivenessCheckStatus
    from apps.providers.models import ProviderCheckStatus, ProviderCheckType

    verification = resource.verification
    reusable_result_found = False

    def latest_completed(check_type: str, metadata_key: str, resource_id: str):
        candidates = verification.provider_checks.filter(
            check_type=check_type,
            status=ProviderCheckStatus.COMPLETED,
        ).order_by("-completed_at", "-created_at")
        return next(
            (
                check
                for check in candidates
                if check.normalized_result_json
                and (check.request_metadata_json or {}).get(metadata_key) == resource_id
            ),
            None,
        )

    current = verification.provider_checks.filter(
        public_id=resource.provider_check_id
    ).first()
    current_is_reusable = _provider_check_is_reusable(current)
    if (
        resource.status == LivenessCheckStatus.INCONCLUSIVE
        and not current_is_reusable
    ):
        recovered = latest_completed(
            ProviderCheckType.LIVENESS,
            "liveness_check_id",
            resource.public_id,
        )
        if recovered is not None:
            resource.provider_check_id = recovered.public_id
            resource.save(update_fields=["provider_check_id", "updated_at"])
            current_is_reusable = True
    reusable_result_found = reusable_result_found or current_is_reusable

    face_match = (
        verification.face_matches.filter(selfie_capture=resource.selfie_capture)
        .order_by("-matched_at", "-created_at")
        .first()
    )
    if face_match is None:
        return reusable_result_found

    current = verification.provider_checks.filter(
        public_id=face_match.provider_check_id
    ).first()
    current_is_reusable = _provider_check_is_reusable(current)
    if (
        face_match.status == FaceMatchStatus.INCONCLUSIVE
        and not current_is_reusable
    ):
        recovered = latest_completed(
            ProviderCheckType.FACE_MATCH,
            "face_match_id",
            face_match.public_id,
        )
        if recovered is not None:
            face_match.provider_check_id = recovered.public_id
            face_match.save(update_fields=["provider_check_id", "updated_at"])
            current_is_reusable = True
    return reusable_result_found or current_is_reusable


def _route_exhaustion_resource_reference(
    job: ProcessingJob, *, liveness_check, decision: VerificationDecision
) -> tuple[str, str] | None:
    """Return the exact biometric resource that originated route exhaustion."""
    from apps.providers.models import ProviderCheckType, ProviderExecutionAttempt

    summary = decision.evidence_summary_json or {}
    capability = summary.get("capability")
    if capability not in {ProviderCheckType.LIVENESS, ProviderCheckType.FACE_MATCH}:
        return None

    if capability == ProviderCheckType.LIVENESS:
        explicit_id = str(summary.get("liveness_check_id") or "")
        if explicit_id:
            return (
                (capability, explicit_id)
                if explicit_id == job.resource_public_id
                else None
            )
        valid_resource_ids = {job.resource_public_id}
        metadata_key = "liveness_check_id"
    else:
        face_match_ids = set(
            liveness_check.verification.face_matches.filter(
                selfie_capture=liveness_check.selfie_capture
            ).values_list("public_id", flat=True)
        )
        explicit_id = str(summary.get("face_match_id") or "")
        if explicit_id:
            return (
                (capability, explicit_id)
                if explicit_id in face_match_ids
                else None
            )
        if not face_match_ids:
            return None
        valid_resource_ids = face_match_ids
        metadata_key = "face_match_id"

    attempts = ProviderExecutionAttempt.objects.select_related(
        "provider_check", "route"
    ).filter(
        provider_check__verification_id=job.verification_id,
        provider_check__check_type=capability,
        completed_at__lte=decision.decided_at,
    )
    route_id = summary.get("provider_route_id")
    if route_id:
        attempts = attempts.filter(route__public_id=route_id)

    groups: dict[str, dict] = {}
    for attempt in attempts:
        metadata = attempt.provider_check.request_metadata_json or {}
        resource_id = str(metadata.get(metadata_key) or "")
        group = groups.setdefault(
            attempt.execution_id,
            {
                "attempts": [],
                "last_completed_at": attempt.completed_at,
                "resource_ids": set(),
            },
        )
        group["attempts"].append(attempt)
        group["last_completed_at"] = max(
            group["last_completed_at"], attempt.completed_at
        )
        if resource_id in valid_resource_ids:
            group["resource_ids"].add(resource_id)

    expected_attempt_count = summary.get("attempt_count")
    expected_error_codes = set(summary.get("error_codes") or [])
    candidates = []
    for group in groups.values():
        group_attempts = group["attempts"]
        if expected_attempt_count is not None and len(group_attempts) != int(
            expected_attempt_count
        ):
            continue
        group_error_codes = {
            attempt.error_code for attempt in group_attempts if attempt.error_code
        }
        if expected_error_codes and group_error_codes != expected_error_codes:
            continue
        if len(group["resource_ids"]) != 1:
            continue
        candidates.append(group)

    if not candidates:
        return None

    origin = max(candidates, key=lambda group: group["last_completed_at"])
    resource_id = next(iter(origin["resource_ids"]))
    return capability, resource_id


def _provider_route_exhaustion_decision_for_job(
    job: ProcessingJob, *, liveness_check=None
) -> VerificationDecision | None:
    if job.job_type != ProcessingJobType.BIOMETRICS:
        return None
    if job.verification.status not in {
        *TERMINAL_STATUSES,
        VerificationStatus.MANUAL_REVIEW_REQUIRED,
    }:
        return None

    from apps.biometrics.models import LivenessCheck

    decision = VerificationDecision.objects.filter(
        verification_id=job.verification_id,
        reason_code="provider_route_exhausted",
    ).first()
    if decision is None:
        return None
    if liveness_check is None:
        liveness_check = (
            LivenessCheck.objects.select_related("selfie_capture", "verification")
            .filter(
                public_id=job.resource_public_id,
                tenant_id=job.tenant_id,
            )
            .first()
        )
    if liveness_check is None:
        return None
    if (
        _route_exhaustion_resource_reference(
            job,
            liveness_check=liveness_check,
            decision=decision,
        )
        is None
    ):
        return None
    return decision


def acquire_processing_job(*, job_type: str, resource) -> ProcessingJob | None:
    """Acquire one generation without allowing concurrent duplicate execution."""
    now = timezone.now()
    with transaction.atomic():
        job, _ = ProcessingJob.objects.select_for_update().get_or_create(
            job_type=job_type,
            resource_public_id=resource.public_id,
            defaults={
                "tenant": resource.tenant,
                "verification": resource.verification,
                "status": ProcessingJobStatus.QUEUED,
                "max_attempts": settings.PROCESSING_JOB_MAX_ATTEMPTS,
                "lease_expires_at": now,
            },
        )
        if job.status in {
            ProcessingJobStatus.COMPLETED,
            ProcessingJobStatus.EXHAUSTED,
        }:
            return None
        if (
            job.status == ProcessingJobStatus.PROCESSING
            and job.lease_expires_at > now
        ):
            return None

        has_reusable_provider_result = False
        if job_type == ProcessingJobType.BIOMETRICS:
            has_reusable_provider_result = _repair_biometric_provider_check_links(
                resource
            )

        recovery_grace = bool(
            job_type == ProcessingJobType.BIOMETRICS
            and job.attempt_count >= job.max_attempts
            and job.error_code == COMMITTED_PROVIDER_RESULT_RECOVERY
            and has_reusable_provider_result
        )
        if job.attempt_count >= job.max_attempts and not recovery_grace:
            return None

        job.status = ProcessingJobStatus.PROCESSING
        # Every worker acquisition advances the durable generation. The recovery-only
        # generation may be max_attempts + 1, but provider I/O is reused rather than
        # replayed, so this does not expand the external-provider attempt budget.
        job.attempt_count += 1
        job.error_code = (
            COMMITTED_PROVIDER_RESULT_RECOVERY_CONSUMED
            if recovery_grace
            else ""
        )
        job.heartbeat_at = now
        job.lease_expires_at = _lease_deadline(now)
        job.save(
            update_fields=[
                "status",
                "attempt_count",
                "heartbeat_at",
                "lease_expires_at",
                "error_code",
                "updated_at",
            ]
        )
        return job


def heartbeat_processing_job(job: ProcessingJob) -> None:
    now = timezone.now()
    lease_expires_at = _lease_deadline(now)
    updated = ProcessingJob.objects.filter(
        pk=job.pk,
        status=ProcessingJobStatus.PROCESSING,
        attempt_count=job.attempt_count,
    ).update(
        heartbeat_at=now,
        lease_expires_at=lease_expires_at,
    )
    if updated != 1:
        raise ProcessingJobOwnershipLost(
            f"Processing job {job.public_id} heartbeat lost ownership."
        )
    job.heartbeat_at = now
    job.lease_expires_at = lease_expires_at


def _repair_biometric_route_exhaustion(job: ProcessingJob, *, now) -> None:
    """Finish biometric resource state committed around provider-route exhaustion."""
    if job.job_type != ProcessingJobType.BIOMETRICS:
        return

    from apps.biometrics.models import (
        FaceMatchStatus,
        LivenessCheck,
        LivenessCheckStatus,
    )
    from apps.providers.models import ProviderCheckType

    liveness_check = (
        LivenessCheck.objects.select_related("selfie_capture", "verification")
        .filter(
            public_id=job.resource_public_id,
            tenant_id=job.tenant_id,
        )
        .first()
    )
    if liveness_check is None:
        return
    decision = _provider_route_exhaustion_decision_for_job(
        job, liveness_check=liveness_check
    )
    if decision is None:
        return

    reference = _route_exhaustion_resource_reference(
        job,
        liveness_check=liveness_check,
        decision=decision,
    )
    if reference is None:
        return
    capability, resource_public_id = reference

    if capability == ProviderCheckType.LIVENESS:
        if (
            resource_public_id == liveness_check.public_id
            and liveness_check.status == LivenessCheckStatus.INCONCLUSIVE
        ):
            liveness_check.status = LivenessCheckStatus.ERROR
            liveness_check.failure_reason = "provider_route_exhausted"
            liveness_check.checked_at = now
            liveness_check.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "checked_at",
                    "updated_at",
                ]
            )
        return

    if capability == ProviderCheckType.FACE_MATCH:
        face_match = liveness_check.verification.face_matches.filter(
            public_id=resource_public_id,
            selfie_capture=liveness_check.selfie_capture,
            status=FaceMatchStatus.INCONCLUSIVE,
        ).first()
        if face_match is not None:
            face_match.status = FaceMatchStatus.ERROR
            face_match.matched_at = now
            face_match.save(
                update_fields=["status", "matched_at", "updated_at"]
            )


@transaction.atomic
def complete_processing_job(job: ProcessingJob) -> None:
    now = timezone.now()
    locked = ProcessingJob.objects.select_for_update().get(pk=job.pk)
    if locked.status == ProcessingJobStatus.COMPLETED:
        if locked.attempt_count == job.attempt_count:
            return
        raise ProcessingJobOwnershipLost(
            f"Processing job {locked.public_id} was completed by another attempt."
        )
    _assert_processing_job_owner(locked, job)
    _repair_biometric_route_exhaustion(locked, now=now)
    locked.status = ProcessingJobStatus.COMPLETED
    locked.heartbeat_at = now
    locked.lease_expires_at = now
    locked.completed_at = now
    locked.error_code = ""
    locked.save(
        update_fields=[
            "status",
            "heartbeat_at",
            "lease_expires_at",
            "completed_at",
            "error_code",
            "updated_at",
        ]
    )


def defer_processing_job(job: ProcessingJob, *, error_code: str) -> None:
    now = timezone.now()
    updated = ProcessingJob.objects.filter(
        pk=job.pk,
        status=ProcessingJobStatus.PROCESSING,
        attempt_count=job.attempt_count,
    ).update(
        status=ProcessingJobStatus.QUEUED,
        heartbeat_at=now,
        lease_expires_at=now,
        error_code=error_code,
    )
    if updated != 1:
        raise ProcessingJobOwnershipLost(
            f"Processing job {job.public_id} defer lost ownership."
        )
    job.status = ProcessingJobStatus.QUEUED
    job.heartbeat_at = now
    job.lease_expires_at = now
    job.error_code = error_code


def exhaust_processing_job(job: ProcessingJob) -> None:
    """Route terminal retry exhaustion to human review with safe audit evidence."""
    from apps.biometrics.models import LivenessCheck, LivenessCheckStatus
    from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus

    now = timezone.now()
    with transaction.atomic():
        locked = (
            ProcessingJob.objects.select_for_update()
            .select_related(
                "tenant", "verification", "verification__verification_subject"
            )
            .get(pk=job.pk)
        )
        if locked.status in {
            ProcessingJobStatus.COMPLETED,
            ProcessingJobStatus.EXHAUSTED,
        }:
            return
        locked.status = ProcessingJobStatus.EXHAUSTED
        locked.completed_at = now
        locked.heartbeat_at = now
        locked.lease_expires_at = now
        locked.error_code = "processing_retries_exhausted"
        locked.save(
            update_fields=[
                "status",
                "completed_at",
                "heartbeat_at",
                "lease_expires_at",
                "error_code",
                "updated_at",
            ]
        )

        if locked.job_type == ProcessingJobType.IDENTITY_DOCUMENT:
            IdentityDocument.objects.filter(
                public_id=locked.resource_public_id,
                tenant_id=locked.tenant_id,
            ).update(status=IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED)
        elif locked.job_type == ProcessingJobType.BIOMETRICS:
            # Exhaustion describes unfinished orchestration, not invalid evidence.
            LivenessCheck.objects.filter(
                public_id=locked.resource_public_id,
                tenant_id=locked.tenant_id,
                status=LivenessCheckStatus.INCONCLUSIVE,
            ).update(
                status=LivenessCheckStatus.ERROR,
                failure_reason="processing_retries_exhausted",
                checked_at=now,
            )

        verification = locked.verification
        lifecycle_already_final = verification.status in {
            *TERMINAL_STATUSES,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        }
        if not lifecycle_already_final:
            from apps.notifications.services import (
                queue_verification_status_notifications,
            )
            from apps.verifications.evidence_commit import (
                schedule_verification_evidence_report_after_commit,
            )
            from apps.webhooks.services import queue_webhook_events

            VerificationDecision.objects.update_or_create(
                verification=verification,
                defaults={
                    "tenant": locked.tenant,
                    "decision": VerificationStatus.MANUAL_REVIEW_REQUIRED,
                    "decision_type": VerificationDecisionType.SYSTEM,
                    "reason_code": "processing_retries_exhausted",
                    "reason_detail": (
                        "Automated processing could not finish after bounded recovery "
                        "attempts and requires human review."
                    ),
                    "evidence_summary_json": {
                        "processing_job_type": locked.job_type,
                        "attempt_count": locked.attempt_count,
                    },
                    "decided_by": None,
                    "decided_at": now,
                },
            )
            transition_verification(
                verification,
                VerificationStatus.MANUAL_REVIEW_REQUIRED,
                clear_completed_at=True,
            )
            queue_webhook_events(
                tenant=locked.tenant,
                event_type="verification.manual_review_required",
                payload={
                    "verification_id": verification.public_id,
                    "external_reference": verification.external_reference,
                    "status": verification.status,
                    "reason_code": "processing_retries_exhausted",
                },
            )
            queue_verification_status_notifications(
                verification=verification,
                decision=verification.status,
                risk_level="high",
            )
            schedule_verification_evidence_report_after_commit(verification)

        record_audit_event(
            tenant=locked.tenant,
            actor=verification.verification_subject,
            action="verification.processing_retries_exhausted",
            target_type="verification",
            target_id=verification.public_id,
            metadata={
                "processing_job_id": locked.public_id,
                "processing_job_type": locked.job_type,
                "attempt_count": locked.attempt_count,
            },
        )


def _resource_processing_finished(job: ProcessingJob) -> bool:
    """Recognize committed side effects left by a worker lost at teardown."""
    if job.job_type == ProcessingJobType.IDENTITY_DOCUMENT:
        from apps.identity_documents.models import (
            IdentityDocument,
            IdentityDocumentStatus,
        )

        return IdentityDocument.objects.filter(
            public_id=job.resource_public_id,
            tenant_id=job.tenant_id,
            status__in=[
                IdentityDocumentStatus.PROCESSED,
                IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED,
                IdentityDocumentStatus.REJECTED,
                IdentityDocumentStatus.FAILED,
            ],
        ).exists()
    if job.job_type == ProcessingJobType.BIOMETRICS:
        from apps.biometrics.models import LivenessCheck, LivenessCheckStatus

        liveness_check = (
            LivenessCheck.objects.select_related("selfie_capture", "verification")
            .filter(
                public_id=job.resource_public_id,
                tenant_id=job.tenant_id,
            )
            .first()
        )
        if liveness_check is None:
            return False

        if _provider_route_exhaustion_decision_for_job(
            job, liveness_check=liveness_check
        ) is not None:
            return True

        return (
            LivenessCheck.objects.filter(
                pk=liveness_check.pk,
                verification__status__in=[
                    VerificationStatus.VERIFIED,
                    VerificationStatus.REJECTED,
                    VerificationStatus.MANUAL_REVIEW_REQUIRED,
                    VerificationStatus.FAILED,
                    VerificationStatus.CANCELLED,
                    VerificationStatus.EXPIRED,
                ],
            )
            .exclude(status=LivenessCheckStatus.INCONCLUSIVE)
            .exists()
        )
    return False


def recover_stale_processing_jobs(*, limit: int = 100) -> tuple[int, int]:
    """Redispatch due work or exhaust it once its bounded attempts are spent."""
    now = timezone.now()
    job_ids = list(
        ProcessingJob.objects.filter(
            status__in=[
                ProcessingJobStatus.QUEUED,
                ProcessingJobStatus.PROCESSING,
            ],
            lease_expires_at__lte=now,
        )
        .order_by("lease_expires_at")
        .values_list("public_id", flat=True)[:limit]
    )
    recovered = 0
    exhausted = 0
    for public_id in job_ids:
        with transaction.atomic():
            job = ProcessingJob.objects.select_for_update().get(public_id=public_id)
            if (
                job.status
                not in {
                    ProcessingJobStatus.QUEUED,
                    ProcessingJobStatus.PROCESSING,
                }
                or job.lease_expires_at > timezone.now()
            ):
                continue

            has_reusable_provider_result = False
            if job.job_type == ProcessingJobType.BIOMETRICS:
                from apps.biometrics.models import LivenessCheck

                resource = (
                    LivenessCheck.objects.select_related(
                        "verification", "selfie_capture"
                    )
                    .filter(
                        public_id=job.resource_public_id,
                        tenant_id=job.tenant_id,
                    )
                    .first()
                )
                if resource is not None:
                    has_reusable_provider_result = (
                        _repair_biometric_provider_check_links(resource)
                    )

            if _resource_processing_finished(job):
                already_finished = True
                should_exhaust = False
            elif job.attempt_count >= job.max_attempts:
                already_finished = False
                if (
                    job.job_type == ProcessingJobType.BIOMETRICS
                    and has_reusable_provider_result
                    and job.error_code
                    != COMMITTED_PROVIDER_RESULT_RECOVERY_CONSUMED
                ):
                    # PENDING means the grace has been discovered/queued but has not
                    # been consumed by a worker. Broker publication can retry without
                    # spending it; acquisition changes the marker to CONSUMED.
                    should_exhaust = False
                    job.status = ProcessingJobStatus.QUEUED
                    job.lease_expires_at = timezone.now()
                    job.error_code = COMMITTED_PROVIDER_RESULT_RECOVERY
                    job.save(
                        update_fields=[
                            "status",
                            "lease_expires_at",
                            "error_code",
                            "updated_at",
                        ]
                    )
                else:
                    should_exhaust = True
            else:
                already_finished = False
                should_exhaust = False
                job.status = ProcessingJobStatus.QUEUED
                job.lease_expires_at = timezone.now()
                job.error_code = "stale_processing_lease"
                job.save(
                    update_fields=[
                        "status",
                        "lease_expires_at",
                        "error_code",
                        "updated_at",
                    ]
                )
        if already_finished:
            try:
                complete_processing_job(job)
            except ProcessingJobOwnershipLost:
                continue
        elif should_exhaust:
            exhaust_processing_job(job)
            exhausted += 1
        elif dispatch_processing_job(job.public_id):
            recovered += 1
    return recovered, exhausted
