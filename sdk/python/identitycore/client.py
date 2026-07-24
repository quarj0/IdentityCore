from __future__ import annotations

import json
import socket
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from identitycore.errors import (
    IdentityCoreAPIError,
    IdentityCoreConnectionError,
    IdentityCoreError,
    IdentityCoreTimeoutError,
)

__version__ = "0.2.0"
Transport = Callable[[str, str, dict[str, str], Optional[bytes], float], Tuple[int, bytes]]


def _human_message(message: str) -> str:
    if any(token in message.lower() for token in ("unexpected token", "invalidtag", "not valid json", "json.parse", "syntaxerror")):
        return "The service is temporarily unavailable. Please try again shortly."
    return message or "Request failed. Please try again."


def _default_transport(method: str, url: str, headers: dict[str, str], body: Optional[bytes], timeout: float) -> Tuple[int, bytes]:
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def _query(params: dict[str, Any]) -> str:
    filtered = {key: value for key, value in params.items() if value not in (None, "")}
    return f"?{urlencode(filtered)}" if filtered else ""


def _path_segment(value: str) -> str:
    """Encode an identifier before interpolating it into an API path."""
    return quote(str(value), safe="")


@dataclass
class _PoliciesClient:
    client: "IdentityCoreClient"

    def list(self) -> list[dict[str, Any]]:
        return self.client.request("GET", "/policies/")

    def retrieve(self, policy_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"/policies/{_path_segment(policy_id)}")


@dataclass
class _VerificationsClient:
    client: "IdentityCoreClient"

    def create(self, *, purpose: str, policy_id: str, verification_subject: dict[str, Any], project_id: str = "", external_reference: str = "", redirect_url: str = "", metadata: Optional[dict[str, Any]] = None, idempotency_key: str = "") -> dict[str, Any]:
        return self.client.request("POST", "/verifications/", {
            "purpose": purpose,
            "policy_id": policy_id,
            "project_id": project_id,
            "verification_subject": verification_subject,
            "external_reference": external_reference,
            "redirect_url": redirect_url,
            "metadata": metadata or {},
        }, idempotency_key=idempotency_key or f"ik_{uuid.uuid4().hex}")

    def list(self, *, status: str = "", external_reference: str = "", page: int | None = None, page_size: int | None = None) -> dict[str, Any]:
        query = _query({"status": status, "external_reference": external_reference, "page": page, "page_size": page_size})
        return self.client.request("GET", f"/verifications/{query}")

    def iter(self, *, status: str = "", external_reference: str = "", page_size: int = 100) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            response = self.list(status=status, external_reference=external_reference, page=page, page_size=page_size)
            yield from response.get("results", [])
            pagination = response.get("pagination", {})
            if page >= int(pagination.get("total_pages", page)):
                return
            page += 1

    def retrieve(self, verification_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"/verifications/{_path_segment(verification_id)}")

    def cancel(self, verification_id: str, *, reason: str = "") -> dict[str, Any]:
        return self.client.request("POST", f"/verifications/{_path_segment(verification_id)}/cancel", {"reason": reason})

    def resend_link(self, verification_id: str, *, channel: str = "email") -> dict[str, Any]:
        return self.client.request("POST", f"/verifications/{_path_segment(verification_id)}/resend-link", {"channel": channel})

    def evidence_report(self, verification_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"/verifications/{_path_segment(verification_id)}/evidence-report")


class IdentityCoreClient:
    def __init__(self, *, api_origin: str, client_id: str, client_secret: str, timeout: float = 30, max_retries: int = 2, retry_backoff: float = 0.25, transport: Optional[Transport] = None, sleep: Callable[[float], None] = time.sleep) -> None:
        parsed = urlparse(api_origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise IdentityCoreError("api_origin must be an absolute HTTP(S) URL.")
        if not client_id or not client_secret:
            raise IdentityCoreError("client_id and client_secret are required.")
        if timeout <= 0 or max_retries < 0 or retry_backoff < 0:
            raise IdentityCoreError("timeout must be positive and retry settings cannot be negative.")
        self.api_origin = api_origin.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.transport = transport or _default_transport
        self._sleep = sleep
        self.policies = _PoliciesClient(self)
        self.verifications = _VerificationsClient(self)

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/health")

    def request(self, method: str, path: str, body: Optional[dict[str, Any]] = None, *, idempotency_key: str = "", request_id: str = "", headers: Optional[dict[str, str]] = None) -> Any:
        method = method.upper()
        url = f"{self.api_origin}/api/v1{path}"
        request_headers = {
            "Accept": "application/json",
            "X-Client-Id": self.client_id,
            "Authorization": f"Bearer {self.client_secret}",
            "X-Request-Id": request_id or f"req_{uuid.uuid4().hex}",
            "User-Agent": f"identitycore-python/{__version__}",
        }
        if headers:
            request_headers.update(headers)
        if idempotency_key:
            request_headers["Idempotency-Key"] = idempotency_key
        encoded_body = None
        if body is not None:
            request_headers["Content-Type"] = "application/json"
            encoded_body = json.dumps(body, separators=(",", ":")).encode("utf-8")

        retryable_method = method in {"GET", "HEAD", "OPTIONS"} or bool(idempotency_key)
        for attempt in range(self.max_retries + 1):
            try:
                status, response_body = self.transport(method, url, request_headers, encoded_body, self.timeout)
            except (socket.timeout, TimeoutError) as exc:
                if retryable_method and attempt < self.max_retries:
                    self._sleep(self.retry_backoff * (2**attempt))
                    continue
                raise IdentityCoreTimeoutError("The request timed out. Please try again.") from exc
            except (URLError, OSError) as exc:
                if retryable_method and attempt < self.max_retries:
                    self._sleep(self.retry_backoff * (2**attempt))
                    continue
                raise IdentityCoreConnectionError("Could not connect to IdentityCore.") from exc
            if retryable_method and status in {408, 429, 500, 502, 503, 504} and attempt < self.max_retries:
                self._sleep(self.retry_backoff * (2**attempt))
                continue
            return self._parse_response(status, response_body)
        raise IdentityCoreConnectionError("Could not connect to IdentityCore.")

    def _parse_response(self, status: int, response_body: bytes) -> Any:
        try:
            payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IdentityCoreAPIError("The service is temporarily unavailable. Please try again shortly.", code="invalid_response", status=status) from exc
        if status >= 400 or not payload.get("success", False):
            error = payload.get("error") or {}
            raise IdentityCoreAPIError(_human_message(error.get("message", "Request failed. Please try again.")), code=error.get("code", "request_failed"), status=status, request_id=payload.get("request_id", ""), details=error.get("details") or {})
        return payload.get("data")
