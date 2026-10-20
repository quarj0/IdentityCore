"""Authenticated subject context without changing the transport peer or auth."""

import base64
import hashlib
import hmac
import ipaddress
import json
import re
import time
from dataclasses import dataclass

from django.conf import settings
from django.http import JsonResponse

PORTAL_AGENT = "IdentityCore-Verification-BFF/1"


@dataclass(frozen=True)
class SubjectMetadata:
    ip_address: str | None
    user_agent: str
    source: str

    @property
    def attribution(self):
        return {
            "source": self.source,
            "client_ip": (
                "ingress_asserted"
                if self.source == "verification_portal" and self.ip_address
                else "immediate_peer" if self.source == "direct" else "unavailable"
            ),
            "user_agent": "reported",
        }


def subject_metadata(request):
    context = getattr(request, "subject_metadata", None)
    if context is not None:
        return context
    if request.headers.get("User-Agent") == PORTAL_AGENT:
        return SubjectMetadata(None, "", "unattributed_portal")
    return SubjectMetadata(
        request.META.get("REMOTE_ADDR") or None,
        request.headers.get("User-Agent", "")[:1024],
        "direct",
    )


def _verify(request, envelope, signature):
    secret = settings.VERIFICATION_METADATA_SECRET
    if len(secret) < 32 or len(envelope) > 8192:
        raise ValueError
    if not re.fullmatch(r"[A-Za-z0-9_-]+", envelope) or not re.fullmatch(
        r"[a-f0-9]{64}", signature
    ):
        raise ValueError
    expected = hmac.new(
        secret.encode(), envelope.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise ValueError
    raw = base64.urlsafe_b64decode(envelope + "=" * (-len(envelope) % 4))
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("v") != 1:
        raise ValueError
    timestamp = payload.get("ts")
    if type(timestamp) is not int or abs(time.time() - timestamp) > 60:
        raise ValueError
    expected_binding = {
        "method": request.method,
        "path": request.path,
        "authorization": hashlib.sha256(
            request.headers.get("Authorization", "").encode()
        ).hexdigest(),
        "request_id": request.headers.get("X-Request-Id", ""),
    }
    if any(payload.get(key) != value for key, value in expected_binding.items()):
        raise ValueError
    agent = payload.get("user_agent")
    address = payload.get("ip")
    if (
        not isinstance(agent, str)
        or len(agent) > 1024
        or any(ord(c) < 32 or ord(c) == 127 for c in agent)
    ):
        raise ValueError
    if address is not None:
        if not isinstance(address, str) or "%" in address:
            raise ValueError
        address = str(ipaddress.ip_address(address))
    return SubjectMetadata(address, agent, "verification_portal")


class SubjectMetadataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        envelope = request.headers.get("X-IC-Subject-Metadata", "")
        signature = request.headers.get("X-IC-Subject-Signature", "")
        hosted = request.path.startswith(("/api/v1/sessions/", "/api/v1/uploads/"))
        if (
            envelope
            or signature
            or (
                hosted
                and settings.VERIFICATION_METADATA_SECRET
                and request.headers.get("User-Agent") == PORTAL_AGENT
            )
        ):
            try:
                if not hosted:
                    raise ValueError
                request.subject_metadata = _verify(request, envelope, signature)
            except (ValueError, TypeError, UnicodeError):
                return JsonResponse(
                    {
                        "error": {
                            "code": "invalid_subject_metadata",
                            "message": "Invalid verification request metadata.",
                        }
                    },
                    status=400,
                )
        return self.get_response(request)
