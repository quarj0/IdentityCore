#!/usr/bin/env python3
"""Dependency-free IdentityCore Provider Contract v1 conformance runner."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import socket
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import urljoin, urlsplit


SIGNATURE_VERSION = "ic-provider-v1"
REQUIRED_CASES = {
    "success",
    "malformed",
    "timeout",
    "replay",
    "version_negotiation",
}


class ConformanceError(RuntimeError):
    """A stable, payload-free conformance failure."""


@dataclass(frozen=True)
class HTTPResult:
    status: int
    headers: dict[str, str]
    body: bytes


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_message(
    *, method: str, path: str, timestamp: int, nonce: str, body: bytes
) -> bytes:
    digest = hashlib.sha256(body).hexdigest()
    return "\n".join(
        (SIGNATURE_VERSION, method.upper(), path, str(timestamp), nonce, digest)
    ).encode("utf-8")


def signature(
    *, method: str, path: str, timestamp: int, nonce: str, body: bytes, secret: str
) -> str:
    message = canonical_message(
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def signing_headers(
    *, path: str, body: bytes, key_id: str, secret: str, timestamp: int, nonce: str
) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-IC-Key-Id": key_id,
        "X-IC-Timestamp": str(timestamp),
        "X-IC-Nonce": nonce,
        "X-IC-Signature-Version": SIGNATURE_VERSION,
        "X-IC-Signature": signature(
            method="POST",
            path=path,
            timestamp=timestamp,
            nonce=nonce,
            body=body,
            secret=secret,
        ),
    }


def load_suite(path: Path) -> dict[str, Any]:
    try:
        suite = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConformanceError("The conformance fixture bundle is unreadable.") from exc
    if not isinstance(suite, dict) or suite.get("suite_version") != "1":
        raise ConformanceError("Unsupported conformance suite version.")
    cases = suite.get("cases")
    if not isinstance(cases, list):
        raise ConformanceError("The conformance fixture bundle has no cases.")
    case_ids = {case.get("id") for case in cases if isinstance(case, dict)}
    if len(cases) != len(REQUIRED_CASES) or case_ids != REQUIRED_CASES:
        raise ConformanceError(
            "The fixture bundle must contain the five required cases."
        )
    return suite


def _parse_json(result: HTTPResult, case_id: str) -> dict[str, Any]:
    content_type = result.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type != "application/json":
        raise ConformanceError(f"{case_id}: response must use application/json.")
    try:
        payload = json.loads(result.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConformanceError(f"{case_id}: response is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ConformanceError(f"{case_id}: response must be a JSON object.")
    return payload


def _verify_response_signature(
    *, result: HTTPResult, path: str, nonce: str, key_id: str, secret: str, case_id: str
) -> None:
    headers = result.headers
    required = (
        "x-ic-key-id",
        "x-ic-timestamp",
        "x-ic-nonce",
        "x-ic-signature-version",
        "x-ic-signature",
    )
    if any(not headers.get(name) for name in required):
        raise ConformanceError(f"{case_id}: signed response headers are required.")
    if headers["x-ic-key-id"] != key_id:
        raise ConformanceError(f"{case_id}: response used an unexpected key ID.")
    if headers["x-ic-nonce"] != nonce:
        raise ConformanceError(
            f"{case_id}: response is not bound to the request nonce."
        )
    if headers["x-ic-signature-version"] != SIGNATURE_VERSION:
        raise ConformanceError(f"{case_id}: response signature version is unsupported.")
    try:
        timestamp = int(headers["x-ic-timestamp"])
    except ValueError as exc:
        raise ConformanceError(f"{case_id}: response timestamp is malformed.") from exc
    if abs(int(time.time()) - timestamp) > 300:
        raise ConformanceError(f"{case_id}: response timestamp is stale.")
    expected = signature(
        method="POST",
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=result.body,
        secret=secret,
    )
    if not hmac.compare_digest(headers["x-ic-signature"], expected):
        raise ConformanceError(f"{case_id}: response signature is invalid.")


def _send(
    *, url: str, body: bytes, headers: dict[str, str], timeout: float
) -> HTTPResult:
    outbound = request.Request(url, data=body, headers=headers, method="POST")
    try:
        with request.urlopen(outbound, timeout=timeout) as response:
            return HTTPResult(
                response.status,
                {key.lower(): value for key, value in response.headers.items()},
                response.read(1_048_577),
            )
    except error.HTTPError as exc:
        return HTTPResult(
            exc.code,
            {key.lower(): value for key, value in exc.headers.items()},
            exc.read(1_048_577),
        )


def _validate_result(
    *,
    case: dict[str, Any],
    result: HTTPResult,
    path: str,
    nonce: str,
    key_id: str,
    secret: str,
) -> None:
    case_id = case["id"]
    if result.status not in case["expected_status"]:
        raise ConformanceError(f"{case_id}: unexpected HTTP status {result.status}.")
    if len(result.body) > 1_048_576:
        raise ConformanceError(f"{case_id}: response exceeds 1 MiB.")
    _verify_response_signature(
        result=result,
        path=path,
        nonce=nonce,
        key_id=key_id,
        secret=secret,
        case_id=case_id,
    )
    payload = _parse_json(result, case_id)
    if case_id in {"success", "replay"} and result.status == 200:
        expected_request = case["request"]
        if payload.get("contract_version") != "1":
            raise ConformanceError("success: contract_version must be 1.")
        if payload.get("invocation_id") != expected_request["invocation_id"]:
            raise ConformanceError("success: invocation_id must match the request.")
        if payload.get("status") != "completed":
            raise ConformanceError("success: status must be completed.")
        if payload.get("outcome") != case.get("expected_outcome", "recognized"):
            raise ConformanceError(f"{case_id}: outcome does not match the fixture.")
        return
    error_payload = payload.get("error")
    if not isinstance(error_payload, dict):
        raise ConformanceError(f"{case_id}: a structured error object is required.")
    if error_payload.get("code") != case["expected_error"]:
        raise ConformanceError(f"{case_id}: error code does not match the fixture.")
    if error_payload.get("retryable") is not False:
        raise ConformanceError(f"{case_id}: fixture rejection must be non-retryable.")
    expected_version = case.get("expected_supported_version")
    if expected_version and expected_version not in payload.get(
        "supported_contract_versions", []
    ):
        raise ConformanceError(
            f"{case_id}: supported contract versions must include {expected_version}."
        )


def run_suite(
    *, base_url: str, fixture_path: Path, key_id: str, secret: str, timeout: float
) -> list[str]:
    if not secret:
        raise ConformanceError("A non-empty conformance secret is required.")
    suite = load_suite(fixture_path)
    path = suite["path"]
    parsed_base = urlsplit(base_url)
    if (
        parsed_base.scheme not in {"http", "https"}
        or not parsed_base.netloc
        or parsed_base.username
        or parsed_base.password
        or parsed_base.query
        or parsed_base.fragment
    ):
        raise ConformanceError("The provider URL must be an absolute HTTP(S) URL.")
    hostname = parsed_base.hostname or ""
    try:
        is_loopback = ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        is_loopback = hostname.lower() == "localhost"
    if not is_loopback:
        raise ConformanceError(
            "The conformance runner accepts loopback providers only."
        )
    if not 0 < timeout <= 10:
        raise ConformanceError(
            "The client timeout must be greater than 0 and at most 10 seconds."
        )
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    passed = []
    for case in suite["cases"]:
        case_id = case["id"]
        body = (
            case["raw_request"].encode("utf-8")
            if "raw_request" in case
            else canonical_json(case["request"])
        )
        timestamp = int(time.time())
        nonce = f"ic-conformance-{case_id}-{secrets.token_hex(8)}"
        headers = signing_headers(
            path=path,
            body=body,
            key_id=key_id,
            secret=secret,
            timestamp=timestamp,
            nonce=nonce,
        )
        headers["X-IC-Conformance-Case"] = case_id
        if case.get("expect_timeout"):
            try:
                _send(url=url, body=body, headers=headers, timeout=timeout)
            except (TimeoutError, socket.timeout):
                passed.append(case_id)
                continue
            except error.URLError as exc:
                if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                    passed.append(case_id)
                    continue
                raise ConformanceError(
                    "timeout: provider request failed before timeout."
                ) from exc
            raise ConformanceError(
                "timeout: provider responded before the client deadline."
            )

        try:
            result = _send(url=url, body=body, headers=headers, timeout=timeout)
        except (error.URLError, TimeoutError, socket.timeout) as exc:
            raise ConformanceError(
                f"{case_id}: local provider request did not return a response."
            ) from exc
        _validate_result(
            case=case,
            result=result,
            path=path,
            nonce=nonce,
            key_id=key_id,
            secret=secret,
        )
        if case_id == "replay":
            try:
                replay = _send(
                    url=url,
                    body=body,
                    headers=headers,
                    timeout=timeout,
                )
            except (error.URLError, TimeoutError, socket.timeout) as exc:
                raise ConformanceError(
                    "replay: local provider request did not return a response."
                ) from exc
            replay_case = dict(case)
            replay_case["expected_status"] = case["replay_status"]
            _validate_result(
                case=replay_case,
                result=replay,
                path=path,
                nonce=nonce,
                key_id=key_id,
                secret=secret,
            )
        passed.append(case_id)
    return passed


def main() -> int:
    default_fixture = Path(__file__).parent / "fixtures" / "provider-contract-v1.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Base URL of the local provider")
    parser.add_argument("--key-id", default="conformance-key")
    parser.add_argument(
        "--secret",
        default=os.environ.get("IDENTITYCORE_CONFORMANCE_SECRET", ""),
        help="Disposable secret; defaults to IDENTITYCORE_CONFORMANCE_SECRET",
    )
    parser.add_argument("--timeout", type=float, default=0.2)
    parser.add_argument("--fixtures", type=Path, default=default_fixture)
    arguments = parser.parse_args()
    try:
        passed = run_suite(
            base_url=arguments.url,
            fixture_path=arguments.fixtures,
            key_id=arguments.key_id,
            secret=arguments.secret,
            timeout=arguments.timeout,
        )
    except ConformanceError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    for case_id in passed:
        print(f"PASS: {case_id}")
    print(f"Provider contract v1 conformance passed ({len(passed)} cases).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
