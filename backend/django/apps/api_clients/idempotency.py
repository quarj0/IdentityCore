import hashlib
import json
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from apps.api_clients.models import APIIdempotencyRecord


class IdempotencyConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "idempotency_conflict"
    default_detail = "This Idempotency-Key conflicts with an earlier request."


@dataclass(frozen=True)
class IdempotencyResult:
    record: APIIdempotencyRecord | None
    response_data: dict | list | None = None
    response_status: int | None = None

    @property
    def is_replay(self) -> bool:
        return self.record is None


def _request_hash(request) -> str:
    canonical_payload = json.dumps(
        request.data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def begin_idempotent_request(*, request, tenant, operation: str) -> IdempotencyResult:
    """Claim an idempotency key inside the caller's outer transaction.

    Keeping the transaction open until ``complete_idempotent_request`` means a
    concurrent request waits for the first response and then replays it.
    """

    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError(
            "Idempotent operations must run inside transaction.atomic()."
        )

    key = request.headers.get("Idempotency-Key", "").strip()
    if not key:
        raise ValidationError({"idempotency_key": "Idempotency-Key is required."})
    if len(key) > 255:
        raise ValidationError(
            {"idempotency_key": "Idempotency-Key must be 255 characters or fewer."}
        )

    api_client = getattr(request, "api_client", None)
    user = None if api_client is not None else request.user
    principal_filter = {"api_client": api_client} if api_client else {"user": user}
    lookup = {"tenant": tenant, "key": key, **principal_filter}
    request_hash = _request_hash(request)
    now = timezone.now()

    record = APIIdempotencyRecord.objects.select_for_update().filter(**lookup).first()
    if record is not None and record.expires_at <= now:
        record.delete()
        record = None

    if record is None:
        defaults = {
            "operation": operation,
            "request_hash": request_hash,
            "method": request.method,
            "path": request.path,
            "expires_at": now + timedelta(hours=settings.IDEMPOTENCY_RECORD_TTL_HOURS),
        }
        try:
            with transaction.atomic():
                record = APIIdempotencyRecord.objects.create(**lookup, **defaults)
        except IntegrityError:
            record = APIIdempotencyRecord.objects.select_for_update().get(**lookup)

    request_matches = (
        record.operation == operation
        and record.request_hash == request_hash
        and record.method == request.method
        and record.path == request.path
    )
    if not request_matches:
        raise IdempotencyConflict(
            "This Idempotency-Key was already used with a different request."
        )

    if record.response_data_json is not None:
        return IdempotencyResult(
            record=None,
            response_data=record.response_data_json,
            response_status=record.response_status or status.HTTP_200_OK,
        )

    return IdempotencyResult(record=record)


def complete_idempotent_request(
    result: IdempotencyResult, *, response_data: dict | list, response_status: int
) -> None:
    if result.record is None:
        raise ValueError("A replayed idempotency result cannot be completed again.")
    result.record.response_data_json = response_data
    result.record.response_status = response_status
    result.record.save(
        update_fields=["response_data_json", "response_status", "updated_at"]
    )
