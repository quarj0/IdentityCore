from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from identitycore.errors import IdentityCoreAPIError


Transport = Callable[[str, str, dict[str, str], Optional[bytes], float], Tuple[int, bytes]]


def _human_message(message: str) -> str:
    if any(
        token in message.lower()
        for token in (
            "unexpected token",
            "invalidtag",
            "not valid json",
            "json.parse",
            "syntaxerror",
        )
    ):
        return "The service is temporarily unavailable. Please try again shortly."
    return message or "Request failed. Please try again."


def _default_transport(
    method: str,
    url: str,
    headers: dict[str, str],
    body: Optional[bytes],
    timeout: float,
) -> Tuple[int, bytes]:
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def _query(params: dict[str, Any]) -> str:
    filtered = {key: value for key, value in params.items() if value not in (None, "")}
    return f"?{urlencode(filtered)}" if filtered else ""


@dataclass
class _PoliciesClient:
    client: "IdentityCoreClient"

    def list(self) -> list[dict[str, Any]]:
        return self.client.request("GET", "/policies/")

    def retrieve(self, policy_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"/policies/{policy_id}")


@dataclass
class _VerificationsClient:
    client: "IdentityCoreClient"

    def create(
        self,
        *,
        purpose: str,
        policy_id: str,
        verification_subject: dict[str, Any],
        external_reference: str = "",
        redirect_url: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return self.client.request(
            "POST",
            "/verifications/",
            {
                "purpose": purpose,
                "policy_id": policy_id,
                "verification_subject": verification_subject,
                "external_reference": external_reference,
                "redirect_url": redirect_url,
                "metadata": metadata or {},
            },
        )

    def list(
        self,
        *,
        status: str = "",
        external_reference: str = "",
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        query = _query(
            {
                "status": status,
                "external_reference": external_reference,
                "page": page,
                "page_size": page_size,
            }
        )
        return self.client.request("GET", f"/verifications/{query}")

    def retrieve(self, verification_id: str) -> dict[str, Any]:
        return self.client.request("GET", f"/verifications/{verification_id}")

    def cancel(self, verification_id: str, *, reason: str = "") -> dict[str, Any]:
        return self.client.request(
            "POST",
            f"/verifications/{verification_id}/cancel",
            {"reason": reason},
        )

    def resend_link(self, verification_id: str, *, channel: str = "email") -> dict[str, Any]:
        return self.client.request(
            "POST",
            f"/verifications/{verification_id}/resend-link",
            {"channel": channel},
        )

    def evidence_report(self, verification_id: str) -> dict[str, Any]:
        return self.client.request(
            "GET",
            f"/verifications/{verification_id}/evidence-report",
        )


class IdentityCoreClient:
    def __init__(
        self,
        *,
        api_origin: str,
        client_id: str,
        client_secret: str,
        timeout: float = 30,
        transport: Optional[Transport] = None,
    ) -> None:
        self.api_origin = api_origin.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.transport = transport or _default_transport
        self.policies = _PoliciesClient(self)
        self.verifications = _VerificationsClient(self)

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/health")

    def request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.api_origin}/api/v1{path}"
        headers = {
            "Accept": "application/json",
            "X-Client-Id": self.client_id,
            "Authorization": f"Bearer {self.client_secret}",
        }
        encoded_body = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            encoded_body = json.dumps(body).encode("utf-8")

        status, response_body = self.transport(
            method,
            url,
            headers,
            encoded_body,
            self.timeout,
        )
        return self._parse_response(status, response_body)

    def _parse_response(self, status: int, response_body: bytes) -> Any:
        try:
            payload = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IdentityCoreAPIError(
                "The service is temporarily unavailable. Please try again shortly.",
                code="invalid_response",
                status=status,
            ) from exc

        if status >= 400 or not payload.get("success", False):
            error = payload.get("error") or {}
            message = _human_message(error.get("message", "Request failed. Please try again."))
            raise IdentityCoreAPIError(
                message,
                code=error.get("code", "request_failed"),
                status=status,
                request_id=payload.get("request_id", ""),
                details=error.get("details") or {},
            )

        return payload.get("data")
