"""Synthetic stdin/stdout test driver. Never host this control surface in production."""

import base64
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python"))
from identitycore_provider import ProviderRuntime, SQLiteStore, SigningKey

now = [1800000000]
key = SigningKey(
    "pec_synthetic",
    "synthetic-wire-secret",
    "ten_synthetic",
    "sandbox",
    frozenset({"document_ocr"}),
)
leases = {}


def handler(operation_id, inputs):
    time.sleep(min(inputs.get("delay_milliseconds", 0), 250) / 1000)
    return {
        "contract_version": "1",
        "capability": "document_ocr",
        "status": "completed",
        "extracted_fields": {"custom_attribute": "Private synthetic value"},
    }


with tempfile.TemporaryDirectory(prefix="identitycore-provider-harness-") as directory:
    store = SQLiteStore(
        Path(directory) / "provider.sqlite",
        encryption_key=bytes(range(32)),
        clock=lambda: now[0],
    )
    runtime = ProviderRuntime(
        keys={key.key_id: key},
        store=store,
        handlers={"document_ocr": handler},
        cancel_handler=lambda _: True,
        delete_handler=lambda _: True,
    )
    for line in sys.stdin:
        try:
            command = json.loads(line)
            action = command["action"]
            if action == "ping":
                output = {"ready": True}
            elif action == "handle":
                response = runtime.handle(
                    method="POST",
                    path="/invoke",
                    body=base64.b64decode(command["body"]),
                    headers=command["headers"],
                    now=now[0],
                )
                output = {
                    "status": response.status,
                    "body": base64.b64encode(response.body).decode(),
                    "headers": response.headers,
                }
            elif action == "claim":
                lease = store.claim_job(lease_seconds=30)
                if lease is not None:
                    leases[lease.operation_id] = lease
                output = {"claimed": lease is not None}
            elif action == "complete":
                output = store.complete(
                    leases[command["operation_id"]], command["result"]
                )
            elif action == "callback":
                body, headers = runtime.callback(command["binding"], timestamp=now[0])
                output = {"body": base64.b64encode(body).decode(), "headers": headers}
            elif action == "advance":
                now[0] += command["seconds"]
                output = {"now": now[0]}
            elif action == "redaction":
                needle = b"Private synthetic value"
                output = {
                    "safe": key.secret not in repr(key)
                    and all(
                        needle not in path.read_bytes()
                        for path in Path(directory).iterdir()
                    )
                    and all(
                        "Private synthetic value" not in repr(lease)
                        and "synthetic-operation-lease-only" not in repr(lease)
                        for lease in leases.values()
                    )
                }
            else:
                raise ValueError()
        except Exception:
            output = {"rejected": True}
        print(json.dumps(output, ensure_ascii=False, allow_nan=False), flush=True)
