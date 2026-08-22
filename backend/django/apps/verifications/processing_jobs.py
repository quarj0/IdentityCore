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


def _lease_deadline(now=None):
    return (now or timezone.now()) + timedelta(
        seconds=settings.PROCESSING_JOB_LEASE_SECONDS
    )


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


def acquire_processing_job(*, job_type: str, resource) -> ProcessingJob | None:
    """Acquire or renew one job without allowing concurrent duplicate execution."""
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
        if job.status == ProcessingJobStatus.PROCESSING and job.lease_expires_at > now:
            return None
        if job.attempt_count >= job.max_attempts:
            return None
        job.status = ProcessingJobStatus.PROCESSING
        job.attempt_count += 1
        job.heartbeat_at = now
        job.lease_expires_at = _lease_deadline(now)
        job.error_code = ""
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
    ProcessingJob.objects.filter(
        pk=job.pk,
        status=ProcessingJobStatus.PROCESSING,
    ).update(heartbeat_at=now, lease_expires_at=_lease_deadline(now))


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

    decision = VerificationDecision.objects.filter(
        verification_id=job.verification_id,
        reason_code="provider_route_exhausted",
    ).first()
    if decision is None:
        return

    capability = (decision.evidence_summary_json or {}).get("capability")
    liveness_check = (
        LivenessCheck.objects.select_related("selfie_capture")
        .filter(
            public_id=job.resource_public_id,
            tenant_id=job.tenant_id,
        )
        .first()
    )
    if liveness_check is None:
        return

    if capability == ProviderCheckType.LIVENESS:
        if liveness_check.status == LivenessCheckStatus.INCONCLUSIVE:
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
        face_match = (
            liveness_check.verification.face_matches.filter(
                selfie_capture=liveness_check.selfie_capture,
                status=FaceMatchStatus.INCONCLUSIVE,
            )
            .order_by("-matched_at")
            .first()
        )
        if face_match is not None:
            face_match.status = FaceMatchStatus.ERROR
            face_match.matched_at = now
            face_match.save(update_fields=["status", "matched_at", "updated_at"])


@transaction.atomic
def complete_processing_job(job: ProcessingJob) -> None:
    now = timezone.now()
    locked = ProcessingJob.objects.select_for_update().get(pk=job.pk)
    if locked.status in {
        ProcessingJobStatus.COMPLETED,
        ProcessingJobStatus.EXHAUSTED,
    }:
        return
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
    ProcessingJob.objects.filter(pk=job.pk).update(
        status=ProcessingJobStatus.QUEUED,
        heartbeat_at=now,
        lease_expires_at=now,
        error_code=error_code,
    )


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
            LivenessCheck.objects.filter(
                public_id=locked.resource_public_id,
                tenant_id=locked.tenant_id,
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

        # Provider-route exhaustion commits the verification decision/outbox first.
        # Treat that lifecycle decision as finished work even if the worker died
        # before its biometric row cleanup; complete_processing_job repairs the row.
        if (
            job.verification.status
            in {
                *TERMINAL_STATUSES,
                VerificationStatus.MANUAL_REVIEW_REQUIRED,
            }
            and VerificationDecision.objects.filter(
                verification_id=job.verification_id,
                reason_code="provider_route_exhausted",
            ).exists()
        ):
            return True

        # A committed biometric sub-result is not the same as a committed
        # verification decision. If finalization rolled back, the job must be
        # redispatched so it can resume from persisted provider evidence.
        return (
            LivenessCheck.objects.filter(
                public_id=job.resource_public_id,
                tenant_id=job.tenant_id,
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
            if _resource_processing_finished(job):
                already_finished = True
                should_exhaust = False
            elif job.attempt_count >= job.max_attempts:
                already_finished = False
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
            complete_processing_job(job)
        elif should_exhaust:
            exhaust_processing_job(job)
            exhausted += 1
        elif dispatch_processing_job(job.public_id):
            recovered += 1
    return recovered, exhausted
