import http.client
import ipaddress
import json
import queue
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit


DEFAULT_MAX_RESPONSE_BYTES = 1 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 10
MAX_TIMEOUT_SECONDS = 30
BLOCKED_HOSTNAMES = {"metadata.google.internal", "instance-data.ec2.internal"}


class SecureHTTPAdapterError(RuntimeError):
    public_message = "Provider invocation failed."

    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        retryable: bool = False,
        provider_check_status: str | None = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.retryable = retryable
        if provider_check_status is not None:
            self.provider_check_status = provider_check_status


def _provider_timeout_error() -> SecureHTTPAdapterError:
    return SecureHTTPAdapterError(
        "Provider request timed out.",
        error_code="provider_timeout",
        retryable=True,
        provider_check_status="timeout",
    )


def _remaining_seconds(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _provider_timeout_error()
    return remaining


def _resolve_public_addresses(
    hostname: str, port: int, *, deadline: float
) -> tuple[tuple[int, tuple], ...]:
    normalized = hostname.rstrip(".").lower()
    if normalized in BLOCKED_HOSTNAMES or normalized.endswith(".internal"):
        raise SecureHTTPAdapterError(
            "Provider destination is not allowed.", error_code="provider_ssrf_blocked"
        )
    result_queue: queue.Queue[tuple[list[tuple] | None, Exception | None]] = queue.Queue(
        maxsize=1
    )

    def resolve() -> None:
        try:
            result_queue.put(
                (
                    socket.getaddrinfo(
                        hostname,
                        port,
                        type=socket.SOCK_STREAM,
                        proto=socket.IPPROTO_TCP,
                    ),
                    None,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised via caller outcome
            result_queue.put((None, exc))

    resolver = threading.Thread(target=resolve, daemon=True)
    resolver.start()
    try:
        address_info, resolution_error = result_queue.get(
            timeout=_remaining_seconds(deadline)
        )
    except queue.Empty as exc:
        raise _provider_timeout_error() from exc
    if resolution_error is not None:
        if isinstance(resolution_error, (TimeoutError, socket.timeout)):
            raise _provider_timeout_error() from resolution_error
        raise SecureHTTPAdapterError(
            "Provider destination could not be resolved.",
            error_code="provider_destination_unresolved",
            retryable=True,
        ) from resolution_error
    if not address_info:
        raise SecureHTTPAdapterError(
            "Provider destination could not be resolved.",
            error_code="provider_destination_unresolved",
            retryable=True,
        )
    vetted_endpoints = []
    seen = set()
    for family, _, _, _, sockaddr in address_info:
        address = sockaddr[0]
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global:
            raise SecureHTTPAdapterError(
                "Provider destination resolves to a private or reserved network.",
                error_code="provider_ssrf_blocked",
            )
        endpoint_key = (family, sockaddr)
        if endpoint_key not in seen:
            seen.add(endpoint_key)
            vetted_endpoints.append(endpoint_key)
    return tuple(vetted_endpoints)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection whose TCP peer is selected from prevalidated endpoints."""

    def __init__(
        self,
        hostname: str,
        port: int,
        *,
        endpoints: tuple[tuple[int, tuple], ...],
        deadline: float,
    ):
        super().__init__(
            hostname,
            port=port,
            timeout=_remaining_seconds(deadline),
            context=ssl.create_default_context(),
        )
        self._vetted_endpoints = endpoints
        self._deadline = deadline

    def connect(self) -> None:
        last_error = None
        for family, sockaddr in self._vetted_endpoints:
            raw_socket = socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            try:
                raw_socket.settimeout(_remaining_seconds(self._deadline))
                raw_socket.connect(sockaddr)
                raw_socket.settimeout(_remaining_seconds(self._deadline))
                self.sock = self._context.wrap_socket(
                    raw_socket,
                    server_hostname=self.host,
                )
                return
            except OSError as exc:
                last_error = exc
                raw_socket.close()
        if last_error is not None:
            raise last_error
        raise OSError("No vetted provider endpoint is available.")


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
            max(
                1024,
                int(
                    self.configuration.get(
                        "max_response_bytes", DEFAULT_MAX_RESPONSE_BYTES
                    )
                ),
            ),
            10 * DEFAULT_MAX_RESPONSE_BYTES,
        )

    def _validate_destination(
        self, url: str, *, deadline: float
    ) -> tuple[str, int, str, tuple[tuple[int, tuple], ...]]:
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
        try:
            port = parsed.port or 443
        except ValueError as exc:
            raise SecureHTTPAdapterError(
                "Provider destination is malformed.",
                error_code="provider_url_invalid",
            ) from exc
        endpoints = _resolve_public_addresses(hostname, port, deadline=deadline)
        request_target = parsed.path or "/"
        if parsed.query:
            request_target = f"{request_target}?{parsed.query}"
        return hostname, port, request_target, endpoints

    def post_json(
        self, *, url: str, payload: dict, headers: dict | None = None
    ) -> dict:
        deadline = time.monotonic() + self.timeout_seconds
        hostname, port, request_target, endpoints = self._validate_destination(
            url, deadline=deadline
        )
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        request_headers.update(headers or {})
        connection = _PinnedHTTPSConnection(
            hostname,
            port,
            endpoints=endpoints,
            deadline=deadline,
        )
        deadline_reached = threading.Event()

        def abort_request() -> None:
            deadline_reached.set()
            connection.close()

        watchdog = threading.Timer(_remaining_seconds(deadline), abort_request)
        watchdog.daemon = True
        watchdog.start()
        try:
            connection.request(
                "POST",
                request_target,
                body=body,
                headers=request_headers,
            )
            response = connection.getresponse()
            if deadline_reached.is_set() or time.monotonic() >= deadline:
                raise _provider_timeout_error()
            if 300 <= response.status < 400:
                raise SecureHTTPAdapterError(
                    "Provider redirects are not permitted.",
                    error_code="provider_redirect_blocked",
                )
            if response.status >= 400:
                raise SecureHTTPAdapterError(
                    "Provider returned an HTTP error.",
                    error_code=f"provider_http_{response.status}",
                    retryable=response.status in {408, 425, 429}
                    or response.status >= 500,
                )
            content_type = response.headers.get_content_type().lower()
            if content_type != "application/json":
                raise SecureHTTPAdapterError(
                    "Provider returned an unsupported content type.",
                    error_code="provider_invalid_content_type",
                )
            chunks = []
            bytes_read = 0
            read = getattr(response, "read1", response.read)
            while bytes_read <= self.max_response_bytes:
                if deadline_reached.is_set():
                    raise _provider_timeout_error()
                connection.sock.settimeout(_remaining_seconds(deadline))
                chunk = read(
                    min(64 * 1024, self.max_response_bytes + 1 - bytes_read)
                )
                if deadline_reached.is_set() or time.monotonic() >= deadline:
                    raise _provider_timeout_error()
                if not chunk:
                    break
                chunks.append(chunk)
                bytes_read += len(chunk)
            response_body = b"".join(chunks)
        except SecureHTTPAdapterError:
            raise
        except (TimeoutError, socket.timeout) as exc:
            raise _provider_timeout_error() from exc
        except (OSError, http.client.HTTPException) as exc:
            if deadline_reached.is_set() or time.monotonic() >= deadline:
                raise _provider_timeout_error() from exc
            raise SecureHTTPAdapterError(
                "Provider request failed.",
                error_code="provider_network_error",
                retryable=True,
            ) from exc
        finally:
            watchdog.cancel()
            connection.close()

        if len(response_body) > self.max_response_bytes:
            raise SecureHTTPAdapterError(
                "Provider response is too large.",
                error_code="provider_response_too_large",
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
