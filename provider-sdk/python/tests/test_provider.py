from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import multiprocessing
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from identitycore_provider import (
    OPERATION_CONTRACT,
    ProviderRuntime,
    ProtocolError,
    SigningKey,
    SQLiteStore,
    json_bytes,
    sign,
    verify,
)

NOW = 1800000000
STORAGE_KEY = bytes(range(32))


def nonce_process(path, digest, output):
    store = SQLiteStore(path, encryption_key=STORAGE_KEY, clock=lambda: NOW)
    output.put(store.claim_nonce(digest, NOW + 300))


class ProviderSDKTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "provider.sqlite"
        self.store = SQLiteStore(
            self.path, encryption_key=STORAGE_KEY, clock=lambda: NOW
        )
        self.key = SigningKey(
            "pec_synthetic",
            "synthetic-wire-secret",
            "ten_synthetic",
            "sandbox",
            frozenset({"document_ocr"}),
        )
        self.processed = []

        def handler(operation_id, inputs):
            self.processed.append(operation_id)
            return {
                "contract_version": "1",
                "capability": "document_ocr",
                "status": "completed",
                "extracted_fields": {"custom_attribute": inputs["custom_attribute"]},
            }

        self.runtime = ProviderRuntime(
            keys={self.key.key_id: self.key},
            store=self.store,
            handlers={"document_ocr": handler},
            cancel_handler=lambda _binding: True,
            delete_handler=lambda _binding: True,
        )
        self.binding = {
            "operation_contract": OPERATION_CONTRACT,
            "operation_id": "pop_synthetic",
            "configuration_id": self.key.key_id,
            "tenant_id": self.key.tenant_id,
            "project_id": "prj_synthetic",
            "environment": "sandbox",
            "capability": "document_ocr",
            "contract_version": "1",
            "request_sha256": "0" * 64,
            "lease_generation": 1,
            "deadline": datetime.fromtimestamp(NOW + 900, timezone.utc).isoformat(),
            "callback_path": "/api/v1/providers/operations/pop_synthetic/callback",
            "lease_token": "synthetic-operation-lease-only",
        }

    def request(self, payload, *, nonce=None):
        body = json_bytes(payload)
        headers = sign(
            method="POST",
            path="/invoke",
            body=body,
            key=self.key,
            timestamp=NOW,
            nonce=nonce,
        )
        response = self.runtime.handle(
            method="POST", path="/invoke", body=body, headers=headers, now=NOW
        )
        return response, json.loads(response.body)

    def start(self):
        response, payload = self.request(
            {
                "contract_version": "1",
                "operation": "start",
                "binding": self.binding,
                "inputs": {"custom_attribute": "Private synthetic value"},
            }
        )
        self.assertEqual(response.status, 200, payload)
        self.assertEqual(payload["status"], "pending")

    def test_exact_wire_signature_matches_published_language_neutral_fixture(self):
        fixture = json.loads(
            (
                Path(__file__).resolve().parents[3]
                / "docs/fixtures/provider-signing-v1.json"
            ).read_text()
        )
        key = SigningKey(
            fixture["key_id"], fixture["secret"], "ten_fixture", "sandbox", frozenset()
        )
        headers = sign(
            method=fixture["method"],
            path=fixture["path"],
            body=fixture["canonical_body"].encode(),
            key=key,
            timestamp=fixture["timestamp"],
            nonce=fixture["nonce"],
        )
        self.assertEqual(headers["X-IC-Signature"], fixture["signature"])
        verify(
            method=fixture["method"],
            path=fixture["path"],
            body=fixture["canonical_body"].encode(),
            headers=headers,
            keys={key.key_id: key},
            claim_nonce=self.store.claim_nonce,
            now=fixture["timestamp"],
        )
        with self.assertRaises(ProtocolError):
            verify(
                method=fixture["method"],
                path=fixture["path"],
                body=fixture["canonical_body"].encode() + b" ",
                headers=headers,
                keys={key.key_id: key},
                claim_nonce=self.store.claim_nonce,
                now=fixture["timestamp"],
            )

    def test_durable_admission_reopen_worker_completion_and_callback(self):
        self.start()
        self.store = SQLiteStore(
            self.path, encryption_key=STORAGE_KEY, clock=lambda: NOW
        )
        self.runtime.store = self.store
        self.start()
        result = self.runtime.work_once()
        self.assertEqual(
            result["result"]["extracted_fields"],
            {"custom_attribute": "Private synthetic value"},
        )
        self.assertEqual(self.processed, ["pop_synthetic"])
        self.assertIsNone(self.runtime.work_once())
        body, headers = self.runtime.callback(self.binding, timestamp=NOW)
        self.assertNotIn("Private synthetic value", repr(self.runtime))
        self.assertEqual(json.loads(body)["status"], "completed")
        verify(
            method="POST",
            path=self.binding["callback_path"],
            body=body,
            headers=headers,
            keys={self.key.key_id: self.key},
            claim_nonce=lambda *_: True,
            now=NOW,
        )
        raw = self.path.read_bytes()
        self.assertNotIn(b"Private synthetic value", raw)
        self.assertNotIn(self.binding["lease_token"].encode(), raw)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_replay_claims_are_atomic_across_processes(self):
        context = multiprocessing.get_context("spawn")
        output = context.Queue()
        processes = [
            context.Process(
                target=nonce_process, args=(str(self.path), "same-nonce", output)
            )
            for _ in range(4)
        ]
        for process in processes:
            process.start()
        for process in processes:
            process.join(10)
            self.assertEqual(process.exitcode, 0)
        self.assertEqual(
            sorted(output.get(timeout=2) for _ in processes),
            [False, False, False, True],
        )

    def test_one_worker_owns_an_operation_and_stale_lease_cannot_complete(self):
        self.start()
        with ThreadPoolExecutor(max_workers=4) as pool:
            leases = list(pool.map(lambda _: self.store.claim_job(), range(4)))
        first = next(lease for lease in leases if lease is not None)
        self.assertEqual(sum(lease is not None for lease in leases), 1)
        self.store.clock = lambda: NOW + 31
        replacement = self.store.claim_job()
        self.assertEqual(replacement.generation, first.generation + 1)
        result = {
            "contract_version": "1",
            "capability": "document_ocr",
            "status": "completed",
        }
        with self.assertRaises(ProtocolError):
            self.store.complete(first, result)
        self.store.complete(replacement, result)

    def test_cancel_fences_worker_and_delete_scrubs_values_and_raw_lease(self):
        self.start()
        lease = self.store.claim_job()
        response, payload = self.request(
            {"contract_version": "1", "operation": "cancel", "binding": self.binding}
        )
        self.assertEqual(payload["status"], "cancelled")
        with self.assertRaises(ProtocolError):
            self.store.complete(
                lease,
                {
                    "contract_version": "1",
                    "capability": "document_ocr",
                    "status": "completed",
                },
            )
        for _ in range(2):
            response, payload = self.request(
                {
                    "contract_version": "1",
                    "operation": "delete",
                    "binding": self.binding,
                }
            )
            self.assertEqual(response.status, 200, payload)
            self.assertEqual(payload["status"], "deleted")
        with self.store._transaction() as db:
            content = self.store._decrypt(
                db.execute("SELECT * FROM operations").fetchone()
            )
        self.assertEqual(
            content, {"binding_sha256": sha256(json_bytes(self.binding)).hexdigest()}
        )

    def test_forged_scope_wrong_types_and_duplicate_json_are_rejected(self):
        for name, value in (
            ("tenant_id", "ten_foreign"),
            ("environment", "production"),
            ("lease_generation", True),
            ("capability", []),
        ):
            response, _ = self.request(
                {
                    "contract_version": "1",
                    "operation": "start",
                    "binding": {**self.binding, name: value},
                    "inputs": {},
                }
            )
            self.assertEqual(response.status, 400, (name, value))
        body = b'{"contract_version":"1","contract_version":"999"}'
        headers = sign(
            method="POST", path="/invoke", body=body, key=self.key, timestamp=NOW
        )
        self.assertEqual(
            self.runtime.handle(
                method="POST", path="/invoke", body=body, headers=headers, now=NOW
            ).status,
            400,
        )
        _, first = self.request(
            {
                "contract_version": "1",
                "operation": "connection_test",
                "environment": "sandbox",
                "challenge": "synthetic-challenge",
                "capabilities": ["document_ocr"],
                "operation_contract": OPERATION_CONTRACT,
            },
            nonce="replay-fixed-nonce",
        )
        replay, _ = self.request(
            {
                "contract_version": "1",
                "operation": "connection_test",
                "environment": "sandbox",
                "challenge": "synthetic-challenge",
                "capabilities": ["document_ocr"],
                "operation_contract": OPERATION_CONTRACT,
            },
            nonce="replay-fixed-nonce",
        )
        self.assertEqual(first["operation_contract"], OPERATION_CONTRACT)
        self.assertEqual(replay.status, 403)
