"""Framework-neutral signed provider endpoint and durable operation worker."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Mapping
from threading import Event, Thread

from .contracts import OPERATION_CONTRACT, validate_binding, validate_result
from .wire import ProtocolError, SigningKey, json_bytes, parse_json, sign, verify


@dataclass(frozen=True)
class Response:
    status: int
    body: bytes = field(repr=False)
    headers: dict[str, str]


class ProviderRuntime:
    def __init__(
        self,
        *,
        keys: Mapping[str, SigningKey],
        store,
        handlers: Mapping[str, Callable],
        cancel_handler: Callable,
        delete_handler: Callable,
    ):
        if not keys or not callable(cancel_handler) or not callable(delete_handler):
            raise ValueError(
                "Provider keys, durable storage and explicit lifecycle handlers are required."
            )
        self.keys = dict(keys)
        self.store = store
        self.handlers = dict(handlers)
        self.cancel_handler = cancel_handler
        self.delete_handler = delete_handler

    def handle(self, *, method, path, body: bytes, headers, now=None):
        sent_at = None
        try:
            key, nonce = verify(
                method=method,
                path=path,
                body=body,
                headers=headers,
                keys=self.keys,
                claim_nonce=self.store.claim_nonce,
                now=now,
            )
            sent_at = int(__import__("time").time()) if now is None else now
        except ProtocolError:
            return Response(
                403,
                json_bytes(
                    {
                        "status": "failed",
                        "error": {"code": "provider_authentication_failed"},
                    }
                ),
                {"Content-Type": "application/json", "Cache-Control": "no-store"},
            )
        except Exception:
            return Response(
                503,
                json_bytes(
                    {
                        "status": "failed",
                        "error": {"code": "provider_replay_store_unavailable"},
                    }
                ),
                {"Content-Type": "application/json", "Cache-Control": "no-store"},
            )
        status = 200
        try:
            request = parse_json(body)
            if method.upper() != "POST":
                raise ProtocolError("Provider operations require POST.")
            if request.get("contract_version") != "1":
                raise ProtocolError("Provider contract version is unsupported.")
            operation = request.get("operation")
            if operation is not None and not isinstance(operation, str):
                raise ProtocolError("Provider operation must be a string.")
            if operation == "connection_test":
                if set(request) - {
                    "contract_version",
                    "operation",
                    "environment",
                    "challenge",
                    "capabilities",
                    "operation_contract",
                }:
                    raise ProtocolError("Connection test fields are unsupported.")
                capabilities = request.get("capabilities")
                if (
                    request.get("environment") != key.environment
                    or not isinstance(request.get("challenge"), str)
                    or not 1 <= len(request["challenge"]) <= 256
                    or not isinstance(capabilities, list)
                    or any(
                        not isinstance(value, str) or value not in key.capabilities
                        for value in capabilities
                    )
                    or not capabilities
                    or len(capabilities) != len(set(capabilities))
                ):
                    raise ProtocolError("Provider negotiation scope does not match.")
                requested_contract = request.get("operation_contract", "sync")
                if not isinstance(
                    requested_contract, str
                ) or requested_contract not in {"sync", OPERATION_CONTRACT}:
                    raise ProtocolError("Provider operation contract is unsupported.")
                payload = {
                    "contract_version": "1",
                    "status": "completed",
                    "challenge": request["challenge"],
                    "capabilities": capabilities,
                }
                if "operation_contract" in request:
                    payload["operation_contract"] = requested_contract
            elif operation in {"start", "poll", "cancel", "delete"}:
                expected = {"contract_version", "operation", "binding"} | (
                    {"inputs"} if operation == "start" else set()
                )
                if set(request) != expected:
                    raise ProtocolError("Provider operation fields are unsupported.")
                binding = request["binding"]
                deadline = validate_binding(
                    binding,
                    key,
                    now=datetime.fromtimestamp(sent_at, timezone.utc),
                    completion=operation in {"start", "poll"},
                )
                if operation == "start":
                    if not isinstance(request["inputs"], dict):
                        raise ProtocolError("Provider inputs must be an object.")
                    payload = self.store.admit(binding, request["inputs"], deadline)
                elif operation == "poll":
                    payload = self.store.poll(binding)
                else:
                    # Fence workers before external cleanup. Lifecycle handlers must
                    # themselves be idempotent by operation_id across crash retries.
                    self.store.control(binding, "cancel")
                    handler = (
                        self.delete_handler
                        if operation == "delete"
                        else self.cancel_handler
                    )
                    if handler(binding) is not True:
                        raise RuntimeError(
                            "Provider lifecycle handler did not acknowledge."
                        )
                    payload = self.store.control(binding, operation)
            elif operation is None:
                if set(request) != {
                    "contract_version",
                    "capability",
                    "environment",
                    "inputs",
                }:
                    raise ProtocolError(
                        "Synchronous invocation fields are unsupported."
                    )
                capability = request.get("capability")
                if (
                    request.get("environment") != key.environment
                    or not isinstance(capability, str)
                    or capability not in key.capabilities
                    or capability not in self.handlers
                    or not isinstance(request.get("inputs"), dict)
                ):
                    raise ProtocolError("Provider invocation scope does not match.")
                payload = validate_result(
                    capability, self.handlers[capability](None, request["inputs"])
                )
            else:
                raise ProtocolError("Provider operation is unsupported.")
        except ProtocolError:
            status = 400
            payload = {
                "contract_version": "1",
                "status": "failed",
                "error": {"code": "provider_invalid_request", "retryable": False},
            }
        except Exception:
            status = 503
            payload = {
                "contract_version": "1",
                "status": "failed",
                "error": {
                    "code": "provider_temporarily_unavailable",
                    "retryable": True,
                },
            }
        encoded = json_bytes(payload)
        signed = sign(
            method=method,
            path=path,
            body=encoded,
            key=key,
            timestamp=sent_at,
            nonce=nonce,
        )
        return Response(
            status,
            encoded,
            {**signed, "Content-Type": "application/json", "Cache-Control": "no-store"},
        )

    def work_once(self, *, lease_seconds=30):
        lease = self.store.claim_job(lease_seconds=lease_seconds)
        if lease is None:
            return None
        capability = lease.binding["capability"]
        if capability not in self.handlers:
            raise ProtocolError("The operation capability handler is unavailable.")
        # Business side effects must also use this stable operation id for
        # idempotency: no network protocol can promise exactly-once side effects.
        stopped = Event()

        def heartbeat():
            while not stopped.wait(max(0.25, lease_seconds / 3)):
                try:
                    if self.store.renew(lease, lease_seconds=lease_seconds) is not True:
                        return
                except Exception:
                    return

        thread = Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            result = self.handlers[capability](lease.operation_id, lease.inputs)
            validate_result(capability, result)
            return self.store.complete(lease, result)
        except Exception:
            raise ProtocolError(
                "Provider processing did not complete; its durable lease will permit retry."
            ) from None
        finally:
            stopped.set()
            thread.join(timeout=2)

    def callback(self, binding, *, timestamp=None):
        key = self.keys.get(binding["configuration_id"])
        if key is None:
            raise ProtocolError("Provider callback key is unavailable.")
        validate_binding(binding, key)
        payload = self.store.poll(binding)
        if payload["status"] not in {"completed", "failed"}:
            raise ProtocolError("The operation has no terminal result to deliver.")
        body = json_bytes(payload)
        return body, sign(
            method="POST",
            path=binding["callback_path"],
            body=body,
            key=key,
            timestamp=timestamp,
        )
