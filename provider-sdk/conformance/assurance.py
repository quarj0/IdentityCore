#!/usr/bin/env python3
"""Real HTTP protocol/worker checks against a packaged SDK's isolated test driver.

This produces synthetic SDK interoperability evidence, never a deployment certificate.
Drivers are stdin control processes and MUST NOT be deployed as provider endpoints.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import queue
import shlex
import subprocess
import sys
import threading
import time
from urllib import error, request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from identitycore_provider import SigningKey, json_bytes, parse_json, sign, verify

SYNC_CASES = {
    "success",
    "malformed",
    "timeout",
    "replay",
    "version_negotiation",
    "capability_binding",
    "environment_binding",
    "deletion",
    "redaction",
}
ASYNC_CASES = {
    "pending",
    "callback_authentication",
    "polling",
    "duplicate_completion",
    "conflicting_completion",
    "late_completion",
    "cancellation",
    "lease_binding",
}
KEY = SigningKey(
    "pec_synthetic",
    "synthetic-wire-secret",
    "ten_synthetic",
    "sandbox",
    frozenset({"document_ocr"}),
)
NOW = 1800000000


class CheckFailed(RuntimeError):
    pass


def require(condition):
    if not condition:
        raise CheckFailed("Protocol assertion failed.")


class Driver:
    def __init__(self, command):
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.messages = queue.Queue()
        self.lock = threading.Lock()

        def read():
            for line in self.process.stdout:
                self.messages.put(line)
            self.messages.put(None)

        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()
        try:
            require(self.send({"action": "ping"}) == {"ready": True})
        except Exception:
            self.close()
            raise

    def send(self, command):
        with self.lock:
            self.process.stdin.write(json.dumps(command) + "\n")
            self.process.stdin.flush()
            response = self.messages.get(timeout=45)
            if response is None:
                raise CheckFailed("Driver exited.")
            return json.loads(response)

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process.stdout.close()
        self.reader.join(timeout=2)


class Suite:
    def __init__(self, driver):
        self.driver = driver
        self.now = NOW
        self.sequence = 0
        suite = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                size = int(self.headers.get("Content-Length", "0"))
                if size < 0 or size > 256 * 1024:
                    self.send_error(413)
                    return
                body = self.rfile.read(size)
                try:
                    response = suite.driver.send(
                        {
                            "action": "handle",
                            "body": base64.b64encode(body).decode(),
                            "headers": dict(self.headers.items()),
                        }
                    )
                    wire = base64.b64decode(response["body"], validate=True)
                    self.send_response(response["status"])
                    self.send_header("Content-Length", str(len(wire)))
                    for name, value in response["headers"].items():
                        self.send_header(name, value)
                    self.end_headers()
                    self.wfile.write(wire)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                except Exception:
                    try:
                        self.send_error(502)
                    except (BrokenPipeError, ConnectionResetError):
                        pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/invoke"
        # Ignore ambient HTTP proxy only for this explicitly bound synthetic loopback fixture.
        self.opener = request.build_opener(request.ProxyHandler({}))

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def exchange(self, payload=None, *, body=None, nonce=None, timeout=5, expected=200):
        encoded = json_bytes(payload) if body is None else body
        headers = sign(
            method="POST",
            path="/invoke",
            body=encoded,
            key=KEY,
            timestamp=self.now,
            nonce=nonce,
        )
        req = request.Request(
            self.url,
            data=encoded,
            headers={**headers, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            response = self.opener.open(req, timeout=timeout)
        except error.HTTPError as rejected:
            response = rejected
        with response:
            raw = response.read(256 * 1024 + 1)
            require(response.status == expected)
            if response.status != 403:
                verify(
                    method="POST",
                    path="/invoke",
                    body=raw,
                    headers=dict(response.headers.items()),
                    keys={KEY.key_id: KEY},
                    claim_nonce=lambda *_: True,
                    now=self.now,
                    expected_nonce=headers["X-IC-Nonce"],
                    replay_namespace="provider-response",
                )
            return parse_json(raw)

    def binding(self, **changes):
        self.sequence += 1
        operation = "pop_suite_" + str(self.sequence)
        return {
            "operation_contract": "ic-provider-operations-v1",
            "operation_id": operation,
            "configuration_id": KEY.key_id,
            "tenant_id": KEY.tenant_id,
            "project_id": "prj_synthetic",
            "environment": KEY.environment,
            "capability": "document_ocr",
            "contract_version": "1",
            "request_sha256": "0" * 64,
            "lease_generation": 1,
            "deadline": datetime.fromtimestamp(
                self.now + 900, timezone.utc
            ).isoformat(),
            "callback_path": f"/api/v1/providers/operations/{operation}/callback",
            "lease_token": "synthetic-operation-lease-only",
            **changes,
        }

    def operation(self, binding, action, *, expected=200):
        payload = {"contract_version": "1", "operation": action, "binding": binding}
        if action == "start":
            payload["inputs"] = {"custom_attribute": "Private synthetic value"}
        return self.exchange(payload, expected=expected)

    def admit(self):
        binding = self.binding()
        require(self.operation(binding, "start")["status"] == "pending")
        return binding

    @staticmethod
    def result():
        return {
            "contract_version": "1",
            "capability": "document_ocr",
            "status": "completed",
            "extracted_fields": {"custom_attribute": "Private synthetic value"},
        }

    def claim(self):
        require(self.driver.send({"action": "claim"}) == {"claimed": True})

    def complete(self, binding, result=None):
        return self.driver.send(
            {
                "action": "complete",
                "operation_id": binding["operation_id"],
                "result": result or self.result(),
            }
        )

    def check(self, name):
        sync = {
            "contract_version": "1",
            "capability": "document_ocr",
            "environment": "sandbox",
            "inputs": {},
        }
        if name == "success":
            require(self.exchange(sync)["status"] == "completed")
        elif name == "malformed":
            self.exchange(
                body=b'{"contract_version":"1","contract_version":"999"}', expected=400
            )
        elif name == "timeout":
            sync["inputs"] = {"delay_milliseconds": 250}
            try:
                self.exchange(sync, timeout=0.05)
            except (TimeoutError, error.URLError) as exc:
                if isinstance(exc, error.URLError) and not isinstance(
                    exc.reason, TimeoutError
                ):
                    raise CheckFailed("Expected a transport timeout.") from None
            else:
                raise CheckFailed("Expected a transport timeout.")
            time.sleep(0.3)
        elif name == "replay":
            self.exchange(sync, nonce="same-synthetic-http-replay")
            self.exchange(sync, nonce="same-synthetic-http-replay", expected=403)
        elif name == "version_negotiation":
            self.exchange({**sync, "contract_version": "999"}, expected=400)
            negotiated = self.exchange(
                {
                    "contract_version": "1",
                    "operation": "connection_test",
                    "environment": "sandbox",
                    "challenge": "synthetic-challenge",
                    "capabilities": ["document_ocr"],
                    "operation_contract": "ic-provider-operations-v1",
                }
            )
            require(
                negotiated["operation_contract"] == "ic-provider-operations-v1"
                and negotiated["challenge"] == "synthetic-challenge"
            )
            for contract in (None, [], {}):
                self.exchange(
                    {
                        "contract_version": "1",
                        "operation": "connection_test",
                        "environment": "sandbox",
                        "challenge": "synthetic-challenge",
                        "capabilities": ["document_ocr"],
                        "operation_contract": contract,
                    },
                    expected=400,
                )
        elif name == "capability_binding":
            self.exchange({**sync, "capability": "liveness"}, expected=400)
        elif name == "environment_binding":
            self.exchange({**sync, "environment": "production"}, expected=400)
        elif name in {"deletion", "cancellation"}:
            binding = self.admit()
            self.claim()
            action = "delete" if name == "deletion" else "cancel"
            require(
                self.operation(binding, action)["status"]
                == ("deleted" if action == "delete" else "cancelled")
            )
            require(self.complete(binding) == {"rejected": True})
            require("result" not in self.operation(binding, "poll"))
            self.operation(binding, "delete")
        elif name == "redaction":
            require(self.driver.send({"action": "redaction"}) == {"safe": True})
        elif name == "pending":
            binding = self.admit()
            require(self.operation(binding, "start")["status"] == "pending")
            self.operation(binding, "delete")
        elif name == "polling":
            binding = self.admit()
            self.claim()
            require(self.operation(binding, "poll")["status"] == "pending")
            require(self.complete(binding)["status"] == "completed")
            require(self.operation(binding, "poll")["result"] == self.result())
        elif name == "callback_authentication":
            binding = self.admit()
            self.claim()
            require(self.complete(binding)["status"] == "completed")
            callback = self.driver.send({"action": "callback", "binding": binding})
            body = base64.b64decode(callback["body"], validate=True)
            arguments = dict(
                method="POST",
                path=binding["callback_path"],
                headers=callback["headers"],
                keys={KEY.key_id: KEY},
                claim_nonce=lambda *_: True,
                now=self.now,
            )
            verify(body=body, **arguments)
            require(parse_json(body)["result"] == self.result())
            try:
                verify(body=body + b" ", **arguments)
            except ValueError:
                pass
            else:
                raise CheckFailed("Altered callback bytes were accepted.")
            # The packaged runtime must also reject tampered request bytes.
            signed = sign(
                method="POST",
                path="/invoke",
                body=json_bytes(sync),
                key=KEY,
                timestamp=self.now,
            )
            response = self.driver.send(
                {
                    "action": "handle",
                    "body": base64.b64encode(json_bytes(sync) + b" ").decode(),
                    "headers": signed,
                }
            )
            require(response["status"] == 403)
        elif name in {"duplicate_completion", "conflicting_completion"}:
            binding = self.admit()
            self.claim()
            first = self.complete(binding)
            require(first["status"] == "completed")
            if name == "duplicate_completion":
                require(self.complete(binding) == first)
            else:
                changed = self.result()
                changed["extracted_fields"] = {
                    "custom_attribute": "Different synthetic value"
                }
                require(self.complete(binding, changed) == {"rejected": True})
        elif name == "lease_binding":
            binding = self.admit()
            for change in (
                {"deadline": "2027-02-30T00:00:00Z"},
                {"deadline": "2027-01-01T00:00:00+00:99"},
                {"deadline": "2027-01-01T00:00:00+15:00"},
                {"deadline": "0000-01-01T00:00:00Z"},
                {"lease_generation": True},
                {"lease_generation": 9007199254740992},
            ):
                self.operation({**binding, **change}, "poll", expected=400)
            self.operation(
                {**binding, "lease_token": "different-synthetic-lease-only"},
                "poll",
                expected=400,
            )
            self.exchange(
                body=b'{"contract_version":"1","inputs":{"score":1e999}}', expected=400
            )
            self.exchange(
                body=b'{"contract_version":"1","inputs":'
                + b"[" * 65
                + b"0"
                + b"]" * 65
                + b"}",
                expected=400,
            )
            self.operation(
                {**binding, "project_id": "prj_foreign"}, "poll", expected=400
            )
            self.operation(binding, "delete")
        elif name == "late_completion":
            binding = self.admit()
            self.claim()
            self.now = self.driver.send({"action": "advance", "seconds": 901})["now"]
            require(self.complete(binding) == {"rejected": True})
            self.operation(binding, "delete")
        else:
            raise CheckFailed("Unknown assurance case.")


def run(command, sdk):
    driver = Driver(command)
    suite = Suite(driver)
    outcomes = {}
    try:
        # Expiry advances the controlled clock only after the other cases complete.
        order = sorted(
            (SYNC_CASES | ASYNC_CASES) - {"late_completion", "redaction"}
        ) + ["redaction", "late_completion"]
        for name in order:
            try:
                suite.check(name)
                outcomes[name] = "passed"
            except Exception:
                outcomes[name] = "failed"
            print(f"{name}: {outcomes[name]}", file=sys.stderr)
    finally:
        suite.close()
        driver.close()
    return {
        "suite_version": "provider-assurance/v1",
        "sdk": sdk,
        "sdk_source_sha256": source_digest(sdk),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "evidence_kind": "synthetic-sdk-interoperability",
        "deployment_assurance": False,
        "transport": "real-loopback-http",
        "cases": outcomes,
    }


def source_digest(sdk):
    root = Path(__file__).resolve().parents[1] / sdk
    pattern = {
        "python": "identitycore_provider/*.py",
        "javascript": "src/*.js",
        "java": "src/main/java/**/*.java",
        "dotnet": "src/**/*.cs",
    }[sdk]
    digest = hashlib.sha256()
    for path in sorted(root.glob(pattern)):
        if "obj" in path.parts or "bin" in path.parts:
            continue
        digest.update(
            str(path.relative_to(root)).encode() + b"\0" + path.read_bytes() + b"\0"
        )
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--driver",
        required=True,
        help="Executable and arguments for an isolated SDK test driver; no shell expansion.",
    )
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument(
        "--sdk", choices=["python", "javascript", "java", "dotnet"], required=True
    )
    args = parser.parse_args()
    artifact = run(shlex.split(args.driver), args.sdk)
    args.artifact.write_bytes(json_bytes(artifact) + b"\n")
    print("artifact_sha256=" + hashlib.sha256(args.artifact.read_bytes()).hexdigest())
    return (
        0
        if set(artifact["cases"]) == SYNC_CASES | ASYNC_CASES
        and all(value == "passed" for value in artifact["cases"].values())
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
