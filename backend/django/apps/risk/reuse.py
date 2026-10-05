"""Policy-controlled, expiring duplicate and velocity indexes."""

import hashlib
import hmac
import ipaddress
import json
import re
from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.risk.models import ReuseFingerprint

KINDS = {"document", "portrait", "device", "network"}
CODES = {
    "document": "document_reuse",
    "portrait": "portrait_reuse",
    "device": "device_velocity",
    "network": "network_velocity",
}


def validate_rules(value):
    if value == {}:
        return {}
    required = {
        "version",
        "scope",
        "retention_days",
        "window_minutes",
        "thresholds",
        "action",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(
            "Reuse rules require version, scope, retention_days, window_minutes, thresholds and action."
        )
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("Reuse rules version must be 1.")
    if value["scope"] not in ("tenant", "global") or value["action"] not in (
        "flag",
        "manual_review",
    ):
        raise ValueError("Choose tenant/global scope and flag/manual_review action.")
    for field, minimum, maximum in (
        ("retention_days", 1, 90),
        ("window_minutes", 1, 10080),
    ):
        if type(value[field]) is not int or not minimum <= value[field] <= maximum:
            raise ValueError(f"{field} is outside its supported range.")
    if value["window_minutes"] > value["retention_days"] * 1440:
        raise ValueError("Velocity window cannot exceed fingerprint retention.")
    thresholds = value["thresholds"]
    if not isinstance(thresholds, dict) or not thresholds or set(thresholds) - KINDS:
        raise ValueError("Thresholds must name document, portrait, device or network.")
    if any(type(n) is not int or not 2 <= n <= 1000 for n in thresholds.values()):
        raise ValueError("Reuse thresholds must be integers from 2 to 1000.")
    return value


def _inputs(verification):
    result = {}
    document = (
        verification.identity_documents.filter(deleted_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if document:
        number = (document.extracted_data_json or {}).get("document_number")
        if isinstance(number, str) and 1 <= len(number) <= 255:
            normalized = re.sub(r"[\s-]", "", number).upper()
            if normalized:
                result["document"] = [
                    "number",
                    document.country_profile_id,
                    document.document_type_id,
                    normalized,
                ]
        if "document" not in result:
            capture = (
                document.captures.filter(deleted_at__isnull=True)
                .exclude(checksum_sha256="")
                .order_by("-created_at")
                .first()
            )
            if capture:
                result["document"] = ["media", capture.checksum_sha256]
    selfie = (
        verification.selfie_captures.filter(deleted_at__isnull=True)
        .exclude(checksum_sha256="")
        .order_by("-created_at")
        .first()
    )
    if selfie:
        result["portrait"] = selfie.checksum_sha256
    sessions = verification.sessions.filter(tenant=verification.tenant)
    device = sessions.exclude(device_fingerprint="").order_by("-created_at").first()
    if device:
        result["device"] = device.device_fingerprint
    network = sessions.filter(ip_address__isnull=False).order_by("-created_at").first()
    if network:
        try:
            address = ipaddress.ip_address(network.ip_address)
            result["network"] = str(
                ipaddress.ip_network(
                    f"{address}/{24 if address.version == 4 else 48}", strict=False
                )
            )
        except ValueError:
            pass
    return result


def _digest(environment, kind, scope, value):
    key = (
        getattr(settings, "REUSE_SIGNAL_HASH_KEY", "") or settings.SECRET_KEY
    ).encode()
    message = json.dumps(
        ["reuse-v1", environment, kind, scope, value], separators=(",", ":")
    ).encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _lock_digests(digests):
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            for digest in sorted(set(digests)):
                key = int.from_bytes(bytes.fromhex(digest[:16]), "big", signed=True)
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])


def lock_subject_fingerprints(subject_id):
    # Erasure acquires this after its parent/metadata updates. That order lets a
    # risk finalizer holding a verification row finish before erasure removes its
    # indexes, avoiding subject-row/verification-row lock inversion.
    digest = hashlib.sha256(
        f"identitycore:reuse:subject:{subject_id}".encode()
    ).hexdigest()
    _lock_digests([digest])


@transaction.atomic
def collect_reuse(verification):
    rules = (verification.policy_snapshot_json or {}).get("reuse_rules", {})
    try:
        rules = validate_rules(rules)
    except (ValueError, TypeError):
        return {
            "version": "duplicate-velocity-v1",
            "status": "invalid_configuration",
            "signals": [],
            "recommended_action": "manual_review",
        }
    if not rules:
        return {
            "version": "duplicate-velocity-v1",
            "status": "disabled",
            "signals": [],
            "recommended_action": "ignore",
        }
    scope = rules["scope"]
    if scope == "global" and not getattr(
        settings, "GLOBAL_REUSE_SIGNALS_ENABLED", False
    ):
        return {
            "version": "duplicate-velocity-v1",
            "status": "global_disabled",
            "scope": scope,
            "signals": [],
            "recommended_action": "manual_review",
        }
    from apps.verification_subjects.models import VerificationSubject

    lock_subject_fingerprints(verification.verification_subject_id)
    subject = (
        VerificationSubject.objects.filter(
            pk=verification.verification_subject_id, tenant=verification.tenant
        )
        .values("deleted_at")
        .first()
    )
    if verification.deleted_at or subject is None or subject["deleted_at"]:
        return {
            "version": "duplicate-velocity-v1",
            "status": "erased",
            "signals": [],
            "recommended_action": "ignore",
        }
    environment = (
        verification.project.environment if verification.project_id else "sandbox"
    )
    now = timezone.now()
    observed = verification.created_at
    snapshot = verification.policy_snapshot_json or {}
    metadata_retention = snapshot.get("metadata_retention_days", 90)
    media_retention = snapshot.get("media_retention_days", rules["retention_days"])
    if any(type(n) is not int or n < 1 for n in [metadata_retention, media_retention]):
        return {
            "version": "duplicate-velocity-v1",
            "status": "invalid_configuration",
            "signals": [],
            "recommended_action": "manual_review",
        }
    retention_days = min(rules["retention_days"], metadata_retention)
    inputs = _inputs(verification)
    fingerprints = {}
    for kind, value in inputs.items():
        if kind not in rules["thresholds"]:
            continue
        local = _digest(environment, kind, str(verification.tenant_id), value)
        shared = (
            _digest(environment, kind, "global", value) if scope == "global" else ""
        )
        fingerprints[kind] = (local, shared)
    _lock_digests([d for pair in fingerprints.values() for d in pair if d])
    signals = []
    for kind, (local, shared) in fingerprints.items():
        kind_retention = (
            min(retention_days, media_retention)
            if kind in {"document", "portrait"}
            else retention_days
        )
        expiry = observed + timedelta(days=kind_retention)
        if expiry <= now:
            continue
        ReuseFingerprint.objects.update_or_create(
            verification=verification,
            kind=kind,
            defaults={
                "tenant": verification.tenant,
                "environment": environment,
                "tenant_digest": local,
                "global_digest": shared,
                "observed_at": observed,
                "expires_at": expiry,
            },
        )
        horizon = (
            timedelta(minutes=rules["window_minutes"])
            if kind in {"device", "network"}
            else timedelta(days=kind_retention)
        )
        matches = ReuseFingerprint.objects.filter(
            environment=environment,
            kind=kind,
            expires_at__gt=now,
            observed_at__gte=now - horizon,
            verification__deleted_at__isnull=True,
            verification__verification_subject__deleted_at__isnull=True,
            tenant__deleted_at__isnull=True,
            tenant__status="active",
        ).exclude(verification=verification).exclude(verification__consent_records__withdrawn_at__isnull=False)
        if scope == "global":
            matches = matches.filter(global_digest=shared)
        else:
            matches = matches.filter(tenant=verification.tenant, tenant_digest=local)
        # Query only enough peers to establish the configured threshold. No peer
        # identifiers or raw counts leave this service in either scope.
        threshold = rules["thresholds"][kind]
        if (
            len(list(matches.values_list("pk", flat=True)[: threshold - 1]))
            >= threshold - 1
        ):
            signals.append(CODES[kind])
    return {
        "version": "duplicate-velocity-v1",
        "status": "completed",
        "scope": scope,
        "signals": sorted(signals),
        "unavailable_kinds": sorted(set(rules["thresholds"]) - set(inputs)),
        "recommended_action": rules["action"] if signals else "ignore",
    }
