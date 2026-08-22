from __future__ import annotations

from pathlib import Path
from textwrap import indent


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{path}: expected one match, found {count}: {old[:80]!r}")
    write(path, text.replace(old, new, 1))


def replace_section(path: str, start: str, end: str, replacement: str) -> None:
    text = read(path)
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"{path}: start marker not found: {start!r}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise RuntimeError(f"{path}: end marker not found: {end!r}")
    write(path, text[:start_index] + replacement + text[end_index:])


def wrap_section(path: str, start: str, end: str, prefix: str) -> None:
    text = read(path)
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"{path}: wrap start marker not found: {start!r}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise RuntimeError(f"{path}: wrap end marker not found: {end!r}")
    block = text[start_index:end_index]
    replacement = prefix + indent(block, "    ")
    write(path, text[:start_index] + replacement + text[end_index:])


processing_path = "backend/django/apps/verifications/processing_jobs.py"
replace_once(
    processing_path,
    '''def lock_processing_job_for_finalization(job: ProcessingJob) -> ProcessingJob:
    """Lock and validate a job before any verification finalization writes."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError(
            "Processing-job finalization ownership must be checked inside an atomic block."
        )
    locked = ProcessingJob.objects.select_for_update().get(pk=job.pk)
    _assert_processing_job_owner(locked, job)
    return locked
''',
    '''def lock_processing_job_for_finalization(job: ProcessingJob) -> ProcessingJob:
    """Lock Verification then ProcessingJob and validate the exact acquisition."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError(
            "Processing-job finalization ownership must be checked inside an atomic block."
        )
    Verification.objects.select_for_update().get(pk=job.verification_id)
    locked = ProcessingJob.objects.select_for_update().get(pk=job.pk)
    _assert_processing_job_owner(locked, job)
    return locked
''',
)

new_repair = '''def _repair_biometric_provider_check_links(resource) -> bool:
    """Relink committed evidence and report whether every pending stage is reusable."""
    from apps.biometrics.models import FaceMatchStatus, LivenessCheckStatus
    from apps.providers.models import ProviderCheckStatus, ProviderCheckType

    verification = resource.verification

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

    liveness_ready = resource.status != LivenessCheckStatus.INCONCLUSIVE
    if not liveness_ready:
        current = verification.provider_checks.filter(
            public_id=resource.provider_check_id
        ).first()
        current_is_reusable = _provider_check_is_reusable(current)
        if not current_is_reusable:
            recovered = latest_completed(
                ProviderCheckType.LIVENESS,
                "liveness_check_id",
                resource.public_id,
            )
            if recovered is not None:
                resource.provider_check_id = recovered.public_id
                resource.save(update_fields=["provider_check_id", "updated_at"])
                current_is_reusable = True
        liveness_ready = current_is_reusable

    face_match = (
        verification.face_matches.filter(selfie_capture=resource.selfie_capture)
        .order_by("-matched_at", "-created_at")
        .first()
    )
    if face_match is None:
        return liveness_ready

    face_ready = face_match.status != FaceMatchStatus.INCONCLUSIVE
    if not face_ready:
        current = verification.provider_checks.filter(
            public_id=face_match.provider_check_id
        ).first()
        current_is_reusable = _provider_check_is_reusable(current)
        if not current_is_reusable:
            recovered = latest_completed(
                ProviderCheckType.FACE_MATCH,
                "face_match_id",
                face_match.public_id,
            )
            if recovered is not None:
                face_match.provider_check_id = recovered.public_id
                face_match.save(update_fields=["provider_check_id", "updated_at"])
                current_is_reusable = True
        face_ready = current_is_reusable

    return liveness_ready and face_ready


'''
replace_section(
    processing_path,
    "def _repair_biometric_provider_check_links(resource) -> bool:\n",
    "def _route_exhaustion_resource_reference(\n",
    new_repair,
)

provider_path = "backend/django/apps/providers/services.py"
replace_once(
    provider_path,
    '''def invoke_provider_check(
    *,
    provider_check: ProviderCheck,
    operation: Callable[..., dict],
    operation_kwargs: dict,
    request_metadata: dict | None = None,
    normalize: Callable[[dict], dict] | None = None,
) -> dict:
''',
    '''def _lock_processing_owner(processing_job) -> None:
    if processing_job is None:
        return
    from apps.verifications.processing_jobs import lock_processing_job_for_finalization

    lock_processing_job_for_finalization(processing_job)


def invoke_provider_check(
    *,
    provider_check: ProviderCheck,
    operation: Callable[..., dict],
    operation_kwargs: dict,
    request_metadata: dict | None = None,
    normalize: Callable[[dict], dict] | None = None,
    processing_job=None,
) -> dict:
''',
)
replace_once(
    provider_path,
    '''    provider_check.save(
        update_fields=[
            "status",
            "started_at",
            "completed_at",
            "request_metadata_json",
            "updated_at",
        ]
    )

    try:
''',
    '''    with transaction.atomic():
        _lock_processing_owner(processing_job)
        provider_check.save(
            update_fields=[
                "status",
                "started_at",
                "completed_at",
                "request_metadata_json",
                "updated_at",
            ]
        )

    try:
''',
)
replace_once(
    provider_path,
    '''        provider_check.save(
            update_fields=[
                "status",
                "completed_at",
                "duration_ms",
                "error_code",
                "error_message",
                "response_metadata_json",
                "normalized_result_json",
                "updated_at",
            ]
        )
        raise
''',
    '''        with transaction.atomic():
            _lock_processing_owner(processing_job)
            provider_check.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "duration_ms",
                    "error_code",
                    "error_message",
                    "response_metadata_json",
                    "normalized_result_json",
                    "updated_at",
                ]
            )
        raise
''',
)
replace_once(
    provider_path,
    '''    provider_check.save(
        update_fields=[
            "status",
            "completed_at",
            "duration_ms",
            "error_code",
            "error_message",
            "response_metadata_json",
            "normalized_result_json",
            "updated_at",
        ]
    )
    return normalized
''',
    '''    with transaction.atomic():
        _lock_processing_owner(processing_job)
        provider_check.save(
            update_fields=[
                "status",
                "completed_at",
                "duration_ms",
                "error_code",
                "error_message",
                "response_metadata_json",
                "normalized_result_json",
                "updated_at",
            ]
        )
    return normalized
''',
)
replace_once(
    provider_path,
    '''def _record_execution_attempt(
    *,
    provider_check: ProviderCheck,
    execution_id: str,
    route,
    route_step,
    sequence: int,
    provider_attempt: int,
    outcome: str,
    error_code: str = "",
    retryable: bool = False,
    fallback_reason: str = "",
    timeout_seconds: int,
    started_at,
) -> ProviderExecutionAttempt:
    return ProviderExecutionAttempt.objects.create(
        provider_check=provider_check,
        execution_id=execution_id,
        route=route,
        route_step=route_step,
        sequence=sequence,
        provider_attempt=provider_attempt,
        outcome=outcome,
        error_code=error_code,
        retryable=retryable,
        fallback_reason=fallback_reason,
        timeout_seconds=timeout_seconds,
        started_at=started_at,
        completed_at=timezone.now(),
    )
''',
    '''def _record_execution_attempt(
    *,
    provider_check: ProviderCheck,
    execution_id: str,
    route,
    route_step,
    sequence: int,
    provider_attempt: int,
    outcome: str,
    error_code: str = "",
    retryable: bool = False,
    fallback_reason: str = "",
    timeout_seconds: int,
    started_at,
    processing_job=None,
) -> ProviderExecutionAttempt:
    with transaction.atomic():
        _lock_processing_owner(processing_job)
        return ProviderExecutionAttempt.objects.create(
            provider_check=provider_check,
            execution_id=execution_id,
            route=route,
            route_step=route_step,
            sequence=sequence,
            provider_attempt=provider_attempt,
            outcome=outcome,
            error_code=error_code,
            retryable=retryable,
            fallback_reason=fallback_reason,
            timeout_seconds=timeout_seconds,
            started_at=started_at,
            completed_at=timezone.now(),
        )
''',
)

provider_text = read(provider_path)
execute_start = provider_text.find("def execute_provider_route(\n")
execute_end = provider_text.find("\ndef get_or_create_system_provider(", execute_start)
if execute_start < 0 or execute_end < 0:
    raise RuntimeError("provider execute_provider_route markers not found")
execute = provider_text[execute_start:execute_end]
needle = '''    """Execute bounded attempts across one resolved provider chain.

    ``operation`` receives the selected provider and the route timeout. Adapters must
    enforce that timeout at their I/O boundary.
    """
'''
replacement = needle + '''    from apps.verifications.processing_jobs import ProcessingJobOwnershipLost

'''
if execute.count(needle) != 1:
    raise RuntimeError("execute docstring marker mismatch")
execute = execute.replace(needle, replacement, 1)
needle = '''                    request_metadata=check_metadata,
                )
            except Exception as exc:
'''
replacement = '''                    request_metadata=check_metadata,
                    processing_job=processing_job,
                )
            except ProcessingJobOwnershipLost:
                raise
            except Exception as exc:
'''
if execute.count(needle) != 1:
    raise RuntimeError("invoke/except marker mismatch")
execute = execute.replace(needle, replacement, 1)
execute = execute.replace(
    "                    started_at=now,\n                )",
    "                    started_at=now,\n                    processing_job=processing_job,\n                )",
)
execute = execute.replace(
    "                    started_at=started_at,\n                )",
    "                    started_at=started_at,\n                    processing_job=processing_job,\n                )",
)
provider_text = provider_text[:execute_start] + execute + provider_text[execute_end:]
write(provider_path, provider_text)

biometric_path = "backend/django/apps/biometrics/tasks.py"
replace_once(
    biometric_path,
    '''    complete_processing_job,
    heartbeat_processing_job,
)
''',
    '''    complete_processing_job,
    heartbeat_processing_job,
    lock_processing_job_for_finalization,
)
''',
)
wrap_section(
    biometric_path,
    "            selfie_capture.face_count = face_count\n",
    "\n\n        if face_match is not None",
    "            with transaction.atomic():\n"
    "                lock_processing_job_for_finalization(processing_job)\n",
)
wrap_section(
    biometric_path,
    "            face_match.status = (\n",
    "\n    except ProcessingJobOwnershipLost:",
    "            with transaction.atomic():\n"
    "                lock_processing_job_for_finalization(processing_job)\n",
)

document_path = "backend/django/apps/identity_documents/tasks.py"
replace_once(
    document_path,
    "from celery import shared_task\nfrom django.utils import timezone\n",
    "from celery import shared_task\nfrom django.db import transaction\nfrom django.utils import timezone\n",
)
replace_once(
    document_path,
    '''    defer_processing_job,
    heartbeat_processing_job,
)
''',
    '''    defer_processing_job,
    heartbeat_processing_job,
    lock_processing_job_for_finalization,
)
''',
)
wrap_section(
    document_path,
    "            capture.quality_score = Decimal(\n",
    "\n\n        if quality_provider_check is not None:",
    "            with transaction.atomic():\n"
    "                lock_processing_job_for_finalization(processing_job)\n",
)
wrap_section(
    document_path,
    "        if quality_provider_check is not None:\n",
    "\n\n        primary_capture = captures[0]",
    "        with transaction.atomic():\n"
    "            lock_processing_job_for_finalization(processing_job)\n",
)
wrap_section(
    document_path,
    "        identity_document.extracted_data_json = {\n",
    "\n\n        for capture in captures:",
    "        with transaction.atomic():\n"
    "            lock_processing_job_for_finalization(processing_job)\n",
)

for path in (processing_path, provider_path, biometric_path, document_path):
    compile(read(path), path, "exec")

print("IC-072 post-merge ownership patch applied successfully.")
