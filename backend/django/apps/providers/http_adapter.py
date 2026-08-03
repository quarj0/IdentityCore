import ipaddress
import json
import socket
from urllib import error, request
from urllib.parse import urlsplit


DEFAULT_MAX_RESPONSE_BYTES = 1 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 10
MAX_TIMEOUT_SECONDS = 30
BLOCKED_HOSTNAMES = {"metadata.google.internal", "instance-data.ec2.internal"}


class SecureHTTPAdapterError(RuntimeError):
    def __init__(self, message: str, *, error_code: str):
        super().__init__(message)
        self.error_code = error_code


class _NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, new_url):
        return None


def _resolve_public_addresses(hostname: str) -> None:
    normalized = hostname.rstrip(".").lower()
    if normalized in BLOCKED_HOSTNAMES or normalized.endswith(".internal"):
        raise SecureHTTPAdapterError(
            "Provider destination is not allowed.", error_code="provider_ssrf_blocked"
        )
    try:
        addresses = {
            sockaddr[4][0]
            for sockaddr in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise SecureHTTPAdapterError(
            "Provider destination could not be resolved.",
            error_code="provider_destination_unresolved",
        ) from exc
    if not addresses:
        raise SecureHTTPAdapterError(
            "Provider destination could not be resolved.",
            error_code="provider_destination_unresolved",
        )
    for address in addresses:
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global:
            raise SecureHTTPAdapterError(
                "Provider destination resolves to a private or reserved network.",
                error_code="provider_ssrf_blocked",
            )


class SecureHTTPProviderAdapter:
    """Bounded JSON HTTP client for explicitly allowlisted providers."""

    def __init__(self, configuration: dict):
        self.configuration = configuration or {}
        self.allowed_hosts = {
            str(host).strip().lower().rstrip(".")
            for host in self.configuration.get("allowed_hosts", [])
            if str(host).strip()
        }
        self.timeout_seconds = min(
            max(
                1,
                int(self.configuration.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
            ),
            MAX_TIMEOUT_SECONDS,
        )
        self.max_response_bytes = min(
            max(1024, int(self.configuration.get("max_response_bytes", DEFAULT_MAX_RESPONSE_BYTES))),
            10 * DEFAULT_MAX_RESPONSE_BYTES,
        )

    def _validate_destination(self, url: str) -> None:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https":
            raise SecureHTTPAdapterError(
                "Provider destinations must use HTTPS.",
                error_code="provider_tls_required",
            )
        if not hostname or parsed.username or parsed.password:
            raise SecureHTTPAdapterError(
                "Provider destination is malformed.", error_code="provider_url_invalid"
            )
        if hostname not in self.allowed_hosts:
            raise SecureHTTPAdapterError(
                "Provider destination is not allowlisted.",
                error_code="provider_destination_not_allowlisted",
            )
        _resolve_public_addresses(hostname)

    def post_json(self, *, url: str, payload: dict, headers: dict | None = None) -> dict:
        self._validate_destination(url)
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request_headers = {"Accept": "application/json", "Content-Type": "application/json"}
        request_headers.update(headers or {})
        http_request = request.Request(
            url,
            data=body,
            headers=request_headers,
            method="POST",
        )
        opener = request.build_opener(_NoRedirectHandler)
        try:
            with opener.open(http_request, timeout=self.timeout_seconds) as response:
                content_type = response.headers.get_content_type().lower()
                if content_type != "application/json":
                    raise SecureHTTPAdapterError(
                        "Provider returned an unsupported content type.",
                        error_code="provider_invalid_content_type",
                    )
                response_body = response.read(self.max_response_bytes + 1)
        except SecureHTTPAdapterError:
            raise
        except error.HTTPError as exc:
            if 300 <= exc.code < 400:
                raise SecureHTTPAdapterError(
                    "Provider redirects are not permitted.",
                    error_code="provider_redirect_blocked",
                ) from exc
            raise SecureHTTPAdapterError(
                "Provider returned an HTTP error.",
                error_code=f"provider_http_{exc.code}",
            ) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise SecureHTTPAdapterError(
                "Provider request timed out.", error_code="provider_timeout"
            ) from exc
        except error.URLError as exc:
            raise SecureHTTPAdapterError(
                "Provider request failed.", error_code="provider_network_error"
            ) from exc

        if len(response_body) > self.max_response_bytes:
            raise SecureHTTPAdapterError(
                "Provider response is too large.", error_code="provider_response_too_large"
            )
        try:
            parsed = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecureHTTPAdapterError(
                "Provider returned invalid JSON.", error_code="provider_invalid_json"
            ) from exc
        if not isinstance(parsed, dict):
            raise SecureHTTPAdapterError(
                "Provider returned an invalid response shape.",
                error_code="provider_invalid_response",
            )
        return parsed
