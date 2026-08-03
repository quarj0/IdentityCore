import hashlib
import json

from apps.accounts.models import PlatformUser
from apps.api_clients.models import APIClient
from apps.audit.models import AuditActorType, AuditEvent


def verify_audit_chain(*, tenant_id: int | str) -> tuple[bool, str]:
    previous_hash = ""
    for event in AuditEvent.objects.filter(tenant_id=tenant_id).order_by("id"):
        payload = {
            "tenant_id": event.tenant_id,
            "actor_type": event.actor_type,
            "actor_id": event.actor_id,
            "action": event.action,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "device_fingerprint": event.device_fingerprint,
            "metadata_json": event.metadata_json,
            "sensitive_metadata_hash": event.sensitive_metadata_hash,
            "previous_event_hash": event.previous_event_hash,
            "created_at": event.created_at.isoformat(),
        }
        expected = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).hexdigest()
        if event.previous_event_hash != previous_hash or event.integrity_hash != expected:
            return False, event.public_id
        previous_hash = event.integrity_hash
    return True, ""


def infer_actor(actor) -> tuple[str, str]:
    if actor is None:
        return AuditActorType.SYSTEM, ""
    if isinstance(actor, PlatformUser):
        return AuditActorType.PLATFORM_USER, actor.public_id
    if isinstance(actor, APIClient):
        return AuditActorType.API_CLIENT, actor.public_id
    if hasattr(actor, "public_id"):
        return AuditActorType.VERIFICATION_SUBJECT, actor.public_id
    return AuditActorType.SYSTEM, ""


def record_audit_event(
    *,
    tenant=None,
    tenant_id: str | None = None,
    action: str,
    target_type: str,
    target_id: str,
    actor=None,
    request=None,
    metadata: dict | None = None,
    sensitive_metadata: dict | None = None,
) -> AuditEvent:
    actor_type, actor_id = infer_actor(actor)
    sensitive_hash = ""
    if sensitive_metadata:
        encoded = json.dumps(sensitive_metadata, sort_keys=True, default=str).encode("utf-8")
        sensitive_hash = hashlib.sha256(encoded).hexdigest()

    if tenant_id is None:
        tenant_id = getattr(tenant, "pk", None)

    return AuditEvent.objects.create(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip_address=request.META.get("REMOTE_ADDR") if request is not None else None,
        user_agent=request.headers.get("User-Agent", "") if request is not None else "",
        device_fingerprint=request.headers.get("X-Device-Fingerprint", "") if request is not None else "",
        metadata_json=metadata or {},
        sensitive_metadata_hash=sensitive_hash,
    )
