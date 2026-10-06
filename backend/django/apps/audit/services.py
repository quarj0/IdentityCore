import hashlib
import hmac
import json

from apps.accounts.models import PlatformUser
from apps.api_clients.models import APIClient
from apps.audit.models import AuditActorType, AuditEvent


def verify_audit_chain(*, tenant_id: int | str) -> tuple[bool, str]:
    previous_hash = ""
    for event in AuditEvent.objects.filter(tenant_id=tenant_id).order_by("id"):
        from apps.audit.integrity import event_authentication, event_hash

        try:
            expected = event_hash(event)
            authenticated = bool(
                event.integrity_key_id and event.authentication_tag
            ) and hmac.compare_digest(
                event.authentication_tag, event_authentication(event)
            )
        except (ValueError, TypeError, KeyError):
            return False, event.public_id
        if (
            event.previous_event_hash != previous_hash
            or not hmac.compare_digest(event.integrity_hash, expected)
            or not authenticated
        ):
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
        encoded = json.dumps(sensitive_metadata, sort_keys=True, default=str).encode(
            "utf-8"
        )
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
        device_fingerprint=(
            request.headers.get("X-Device-Fingerprint", "")
            if request is not None
            else ""
        ),
        metadata_json=metadata or {},
        sensitive_metadata_hash=sensitive_hash,
    )


def lock_audit_chain(tenant_id):
    """Serialize chain appends without blocking FK key-share checks.

    Webhook producers and endpoint mutations acquire this before endpoint locks,
    so audit appends cannot invert their lock ordering.
    """
    from apps.tenants.models import Tenant

    if tenant_id is not None:
        Tenant.objects.select_for_update(no_key=True).only("pk").get(pk=tenant_id)
