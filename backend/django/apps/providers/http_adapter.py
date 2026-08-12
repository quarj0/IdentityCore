import base64
import http.client
import ipaddress
import json
import queue
import socket
import ssl
import threading
import time
import urllib.request
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit


DEFAULT_MAX_RESPONSE_BYTES = 1 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 10
MAX_TIMEOUT_SECONDS = 30
BLOCKED_HOSTNAMES = {"metadata.google.internal", "instance-data.ec2.internal"}
DNS_RESOLVER_WORKERS = 4
DNS_RESOLVER_CAPACITY = 8


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


class _BoundedDNSResolver:
    """Resolve hostnames without allowing timed-out calls to grow threads forever."""

    def __init__(self, *, workers: int, capacity: int):
        self._workers = workers
        self._capacity = threading.BoundedSemaphore(capacity)
        self._requests: queue.Queue[
            tuple[str, int, queue.Queue[tuple[list[tuple] | None, Exception | None]]]
        ] = queue.Queue(maxsize=capacity)
        self._start_lock = threading.Lock()
        self._started = False

    def _ensure_started(self) -> None:
        with self._start_lock:
            if self._started:
                return
            for worker_number in range(self._workers):
                worker = threading.Thread(
                    target=self._run,
                    name=f"identitycore-dns-{worker_number + 1}",
                    daemon=True,
                )
                worker.start()
            self._started = True

    def _run(self) -> None:
        while True:
            hostname, port, result_queue = self._requests.get()
            try:
                try:
                    result = socket.getaddrinfo(
                        hostname,
                        port,
                        type=socket.SOCK_STREAM,
                        proto=socket.IPPROTO_TCP,
                    )
                    outcome = (result, None)
                except Exception as exc:  # pragma: no cover - returned to caller
                    outcome = (None, exc)
                try:
                    result_queue.put_nowait(outcome)
                except queue.Full:  # pragma: no cover - defensive only
                    pass
            finally:
                self._capacity.release()
                self._requests.task_done()

    def resolve(self, hostname: str, port: int, *, deadline: float) -> list[tuple]:
        self._ensure_started()
        if not self._capacity.acquire(timeout=_remaining_seconds(deadline)):
            raise _provider_timeout_error()
        result_queue: queue.Queue[tuple[list[tuple] | None, Exception | None]] = (
            queue.Queue(maxsize=1)
        )
        try:
            self._requests.put_nowait((hostname, port, result_queue))
        except queue.Full as exc:  # pragma: no cover - semaphore keeps these aligned
            self._capacity.release()
            raise _provider_timeout_error() from exc
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
        return address_info


_dns_resolver = _BoundedDNSResolver(
    workers=DNS_RESOLVER_WORKERS,
    capacity=DNS_RESOLVER_CAPACITY,
)


def _resolve_addresses(
    hostname: str, port: int, *, deadline: float
) -> tuple[tuple[int, tuple], ...]:
    address_info = _dns_resolver.resolve(hostname, port, deadline=deadline)
    endpoints = []
    seen = set()
    for family, _, _, _, sockaddr in address_info:
        endpoint_key = (family, sockaddr)
        if endpoint_key not in seen:
            seen.add(endpoint_key)
            endpoints.append(endpoint_key)
    return tuple(endpoints)


def _resolve_public_addresses(
    hostname: str, port: int, *, deadline: float
) -> tuple[tuple[int, tuple], ...]:
    normalized = hostname.rstrip(".").lower()
    if normalized in BLOCKED_HOSTNAMES or normalized.endswith(".internal"):
        raise SecureHTTPAdapterError(
            "Provider destination is not allowed.", error_code="provider_ssrf_blocked"
        )
    endpoints = _resolve_addresses(hostname, port, deadline=deadline)
    if not endpoints:
        raise SecureHTTPAdapterError(
            "Provider destination could not be resolved.",
            error_code="provider_destination_unresolved",
            retryable=True,
        )
    vetted_endpoints = []
    for family, sockaddr in endpoints:
        address = sockaddr[0]
        parsed = ipaddress.ip_address(address)
        if not parsed.is_global:
            raise SecureHTTPAdapterError(
                "Provider destination resolves to a private or reserved network.",
                error_code="provider_ssrf_blocked",
            )
        vetted_endpoints.append((family, sockaddr))
    return tuple(vetted_endpoints)


@dataclass(frozen=True)
class _HTTPSProxy:
    hostname: str
    port: int
    use_tls: bool
    headers: dict[str, str]
    endpoints: tuple[tuple[int, tuple], ...]


def _response_socket(response: http.client.HTTPResponse | None):
    if response is None:
        return None
    raw = getattr(getattr(response, "fp", None), "raw", None)
    return getattr(raw, "_sock", None)


def _shutdown_socket(active_socket) -> None:
    if active_socket is None:
        return
    try:
        active_socket.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS connection whose TCP peer is selected from prevalidated endpoints."""

    def __init__(
        self,
        hostname: str,
        port: int,
        *,
        endpoints: tuple[tuple[int, tuple], ...],
        deadline: float,
        proxy: _HTTPSProxy | None = None,
    ):
        super().__init__(
            hostname,
            port=port,
            timeout=_remaining_seconds(deadline),
            context=ssl.create_default_context(),
        )
        self._vetted_endpoints = endpoints
        self._deadline = deadline
        self._proxy = proxy

    def _open_socket(self, family: int, sockaddr: tuple):
        raw_socket = socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        try:
            raw_socket.settimeout(_remaining_seconds(self._deadline))
            raw_socket.connect(sockaddr)
            raw_socket.settimeout(_remaining_seconds(self._deadline))
            return raw_socket
        except Exception:
            raw_socket.close()
            raise

    def connect(self) -> None:
        last_error = None
        if self._proxy is not None:
            if self._proxy.use_tls:
                raise SecureHTTPAdapterError(
                    "TLS-encrypted HTTPS proxies are not supported.",
                    error_code="provider_proxy_unsupported",
                )
            for _, provider_sockaddr in self._vetted_endpoints:
                provider_address = provider_sockaddr[0]
                for family, proxy_sockaddr in self._proxy.endpoints:
                    raw_socket = None
                    try:
                        tunnel_headers = dict(self._proxy.headers)
                        if ipaddress.ip_address(provider_address).version == 6:
                            tunnel_headers["Host"] = f"[{provider_address}]:{self.port}"
                        self.set_tunnel(
                            provider_address,
                            self.port,
                            headers=tunnel_headers,
                        )
                        raw_socket = self._open_socket(family, proxy_sockaddr)
                        self.sock = raw_socket
                        self.sock.settimeout(_remaining_seconds(self._deadline))
                        self._tunnel()
                        self.sock.settimeout(_remaining_seconds(self._deadline))
                        self.sock = self._context.wrap_socket(
                            self.sock,
                            server_hostname=self.host,
                        )
                        return
                    except OSError as exc:
                        last_error = exc
                        if raw_socket is not None:
                            raw_socket.close()
                        self.sock = None
            if last_error is not None:
                raise last_error
            raise OSError("No configured proxy endpoint is available.")
        for family, sockaddr in self._vetted_endpoints:
            raw_socket = None
            try:
                raw_socket = self._open_socket(family, sockaddr)
                self.sock = self._context.wrap_socket(
                    raw_socket,
                    server_hostname=self.host,
                )
                return
            except OSError as exc:
                last_error = exc
                if raw_socket is not None:
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

    def _proxy_for_destination(
        self, hostname: str, port: int, *, deadline: float
    ) -> _HTTPSProxy | None:
        configured_proxy = self.configuration.get("https_proxy")
        if configured_proxy is None:
            configured_proxy = urllib.request.getproxies().get("https")
            bypass_hostname = f"[{hostname}]" if ":" in hostname else hostname
            if configured_proxy and urllib.request.proxy_bypass(
                f"{bypass_hostname}:{port}"
            ):
                return None
        if not configured_proxy:
            return None
        try:
            parsed = urlsplit(str(configured_proxy))
            proxy_hostname = parsed.hostname
        except ValueError as exc:
            raise SecureHTTPAdapterError(
                "HTTPS proxy configuration is malformed.",
                error_code="provider_proxy_invalid",
            ) from exc
        if (
            parsed.scheme not in {"http", "https"}
            or not proxy_hostname
            or (parsed.path not in {"", "/"})
            or parsed.query
            or parsed.fragment
        ):
            raise SecureHTTPAdapterError(
                "HTTPS proxy configuration is malformed.",
                error_code="provider_proxy_invalid",
            )
        try:
            proxy_port = parsed.port
        except ValueError as exc:
            raise SecureHTTPAdapterError(
                "HTTPS proxy configuration is malformed.",
                error_code="provider_proxy_invalid",
            ) from exc
        if parsed.scheme == "https":
            raise SecureHTTPAdapterError(
                "TLS-encrypted HTTPS proxies are not supported.",
                error_code="provider_proxy_unsupported",
            )
        if proxy_port is None:
            proxy_port = 443 if parsed.scheme == "https" else 80
        if proxy_port == 0:
            raise SecureHTTPAdapterError(
                "HTTPS proxy configuration is malformed.",
                error_code="provider_proxy_invalid",
            )
        headers = {}
        if parsed.username is not None:
            credentials = f"{unquote(parsed.username)}:{unquote(parsed.password or '')}"
            encoded = base64.b64encode(credentials.encode("utf-8")).decode("ascii")
            headers["Proxy-Authorization"] = f"Basic {encoded}"
        endpoints = _resolve_addresses(proxy_hostname, proxy_port, deadline=deadline)
        return _HTTPSProxy(
            hostname=proxy_hostname,
            port=proxy_port,
            use_tls=parsed.scheme == "https",
            headers=headers,
            endpoints=endpoints,
        )

    def _validate_destination(self, url: str) -> tuple[str, int, str]:
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
            port = parsed.port
        except ValueError as exc:
            raise SecureHTTPAdapterError(
                "Provider destination is malformed.",
                error_code="provider_url_invalid",
            ) from exc
        if port is None:
            port = 443
        if port == 0:
            raise SecureHTTPAdapterError(
                "Provider destination is malformed.",
                error_code="provider_url_invalid",
            )
        request_target = parsed.path or "/"
        if parsed.query:
            request_target = f"{request_target}?{parsed.query}"
        return hostname, port, request_target

    def post_json(
        self, *, url: str, payload: dict, headers: dict | None = None
    ) -> dict:
        deadline = time.monotonic() + self.timeout_seconds
        hostname, port, request_target = self._validate_destination(url)
        proxy = self._proxy_for_destination(hostname, port, deadline=deadline)
        endpoints = _resolve_public_addresses(
            hostname,
            port,
            deadline=deadline,
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
            proxy=proxy,
        )
        deadline_reached = threading.Event()
        response = None

        def abort_request() -> None:
            deadline_reached.set()
            response_owned_socket = _response_socket(response)
            connection_socket = connection.sock
            _shutdown_socket(response_owned_socket)
            if connection_socket is not response_owned_socket:
                _shutdown_socket(connection_socket)
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
            if connection.sock is not None:
                connection.sock.settimeout(_remaining_seconds(deadline))
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
                active_socket = _response_socket(response) or connection.sock
                if active_socket is not None:
                    active_socket.settimeout(_remaining_seconds(deadline))
                chunk = read(min(64 * 1024, self.max_response_bytes + 1 - bytes_read))
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
