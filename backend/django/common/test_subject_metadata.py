import base64
import hashlib
import hmac
import json
import time

from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from common.subject_metadata import (
    PORTAL_AGENT,
    SubjectMetadataMiddleware,
    subject_metadata,
)

SECRET = "synthetic-metadata-secret-at-least-32-characters"


def signed_headers(
    path, *, authorization="Bearer synthetic", ip="192.0.2.40", **overrides
):
    payload = {
        "v": 1,
        "ts": int(time.time()),
        "method": "GET",
        "path": path,
        "authorization": hashlib.sha256(authorization.encode()).hexdigest(),
        "request_id": "synthetic-request",
        "ip": ip,
        "user_agent": "ApplicantBrowser/1.0",
        **overrides,
    }
    encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    return {
        "HTTP_AUTHORIZATION": authorization,
        "HTTP_X_REQUEST_ID": "synthetic-request",
        "HTTP_USER_AGENT": PORTAL_AGENT,
        "REMOTE_ADDR": "10.0.0.5",
        "HTTP_X_IC_SUBJECT_METADATA": encoded,
        "HTTP_X_IC_SUBJECT_SIGNATURE": hmac.new(
            SECRET.encode(), encoded.encode(), hashlib.sha256
        ).hexdigest(),
    }


@override_settings(VERIFICATION_METADATA_SECRET=SECRET)
class SubjectMetadataTests(SimpleTestCase):
    path = "/api/v1/sessions/ses_test/consent"

    def invoke(self, headers, *, path=None):
        request = RequestFactory().get(path or self.path, **headers)

        def downstream(request):
            context = subject_metadata(request)
            return JsonResponse(
                {
                    "ip": context.ip_address,
                    "agent": context.user_agent,
                    "peer": request.META["REMOTE_ADDR"],
                    "attribution": context.attribution,
                }
            )

        return SubjectMetadataMiddleware(downstream)(request)

    def test_signed_context_preserves_transport_peer(self):
        response = self.invoke(signed_headers(self.path))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["ip"], "192.0.2.40")
        self.assertEqual(data["agent"], "ApplicantBrowser/1.0")
        self.assertEqual(data["peer"], "10.0.0.5")
        self.assertEqual(data["attribution"]["client_ip"], "ingress_asserted")

    def test_unavailable_ip_does_not_become_proxy_ip(self):
        response = self.invoke(signed_headers(self.path, ip=None))
        self.assertIsNone(json.loads(response.content)["ip"])

    def test_binding_freshness_and_payload_validation(self):
        for changes in (
            {"path": "/different"},
            {"method": "POST"},
            {"authorization": "other"},
            {"request_id": "other"},
            {"ts": 1},
            {"ts": int(time.time()) + 120},
            {"ts": True},
            {"ip": "spoof, 192.0.2.1"},
            {"ip": "fe80::1%eth0"},
            {"user_agent": "a" * 1025},
            {"user_agent": "bad\nagent"},
            {"user_agent": None},
        ):
            with self.subTest(changes=changes):
                headers = signed_headers(
                    self.path,
                    **{
                        k: v
                        for k, v in changes.items()
                        if k not in ("path", "authorization")
                    }
                )
                if "path" in changes:
                    headers = signed_headers(changes["path"])
                if "authorization" in changes:
                    headers["HTTP_AUTHORIZATION"] = "Bearer other"
                self.assertEqual(self.invoke(headers).status_code, 400)

    def test_forged_missing_and_oversized_headers_fail_closed(self):
        for key, value in (
            ("HTTP_X_IC_SUBJECT_SIGNATURE", "0" * 64),
            ("HTTP_X_IC_SUBJECT_SIGNATURE", "é" * 64),
            ("HTTP_X_IC_SUBJECT_METADATA", "a" * 8193),
            ("HTTP_X_IC_SUBJECT_METADATA", ""),
        ):
            headers = signed_headers(self.path)
            headers[key] = value
            self.assertEqual(self.invoke(headers).status_code, 400)
        self.assertEqual(
            self.invoke({"HTTP_USER_AGENT": PORTAL_AGENT}).status_code, 400
        )
        self.assertEqual(
            self.invoke(
                signed_headers("/api/v1/tenant/"), path="/api/v1/tenant/"
            ).status_code,
            400,
        )

    def test_encoded_context_and_signature_are_redacted(self):
        from common.safe_logging import redact_value
        headers = signed_headers(self.path)
        redacted = redact_value(headers)
        self.assertEqual(redacted["HTTP_X_IC_SUBJECT_METADATA"], "[REDACTED]")
        self.assertEqual(redacted["HTTP_X_IC_SUBJECT_SIGNATURE"], "[REDACTED]")

    def test_direct_clients_ignore_forwarded_headers(self):
        response = self.invoke(
            {
                "REMOTE_ADDR": "192.0.2.12",
                "HTTP_USER_AGENT": "SDK",
                "HTTP_X_FORWARDED_FOR": "8.8.8.8",
            }
        )
        data = json.loads(response.content)
        self.assertEqual(data["ip"], "192.0.2.12")
        self.assertEqual(data["attribution"]["source"], "direct")

    @override_settings(VERIFICATION_METADATA_SECRET="")
    def test_unconfigured_portal_is_explicitly_unattributed(self):
        response = self.invoke(
            {"REMOTE_ADDR": "10.0.0.5", "HTTP_USER_AGENT": PORTAL_AGENT}
        )
        data = json.loads(response.content)
        self.assertIsNone(data["ip"])
        self.assertEqual(data["attribution"]["source"], "unattributed_portal")
