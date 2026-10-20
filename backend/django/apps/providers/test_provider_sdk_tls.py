"""Real backend transport interoperability with the packaged Python Provider SDK."""

from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils import timezone

from apps.providers.http_adapter import SecureHTTPProviderAdapter
from common.provider_signing import ProviderSigningContext, verify_message

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "provider-sdk/python"))
from identitycore_provider import (
    ProviderRuntime,
    SigningKey,
    SQLiteStore,
    derive_signing_secret,
)


class PackagedProviderTLSIntegrationTests(SimpleTestCase):
    def test_backend_negotiation_async_result_callback_and_deletion_over_verified_tls(
        self,
    ):
        credential = "synthetic-sdk-provider-credential"
        signing = ProviderSigningContext(
            "pec_synthetic",
            derive_signing_secret(credential),
            "provider-response:sdk-tls:sandbox",
        )
        key = SigningKey(
            signing.key_id,
            signing.secret,
            "ten_synthetic",
            "sandbox",
            frozenset({"document_ocr"}),
        )
        observed = []
        with tempfile.TemporaryDirectory(
            prefix="identitycore-packaged-provider-tls-"
        ) as directory:
            store = SQLiteStore(
                Path(directory) / "provider.sqlite", encryption_key=bytes(range(32))
            )
            runtime = ProviderRuntime(
                keys={key.key_id: key},
                store=store,
                handlers={
                    "document_ocr": lambda operation_id, inputs: {
                        "contract_version": "1",
                        "capability": "document_ocr",
                        "status": "completed",
                        "extracted_fields": {"name": "Synthetic SDK subject"},
                    }
                },
                cancel_handler=lambda _: True,
                delete_handler=lambda _: True,
            )

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    if self.headers.get("Authorization") != "Bearer " + credential:
                        self.send_error(403)
                        return
                    body = self.rfile.read(int(self.headers["Content-Length"]))
                    response = runtime.handle(
                        method="POST",
                        path=self.path,
                        body=body,
                        headers=dict(self.headers.items()),
                    )
                    observed.append(response.status)
                    self.send_response(response.status)
                    self.send_header("Content-Length", str(len(response.body)))
                    for name, value in response.headers.items():
                        self.send_header(name, value)
                    self.end_headers()
                    self.wfile.write(response.body)

            private_key = Path(directory) / "tls.key"
            certificate = Path(directory) / "tls.pem"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(private_key),
                    "-out",
                    str(certificate),
                    "-days",
                    "1",
                    "-subj",
                    "/CN=provider.example.test",
                    "-addext",
                    "subjectAltName=DNS:provider.example.test",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            private_key.chmod(0o600)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.load_cert_chain(certificate, private_key)
            server.socket = tls.wrap_socket(server.socket, server_side=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                trusted = ssl.create_default_context(cafile=str(certificate))
                adapter = SecureHTTPProviderAdapter(
                    {
                        "allowed_hosts": ["provider.example.test"],
                        "timeout_seconds": 5,
                        "https_proxy": "",
                    }
                )
                with patch(
                    "apps.providers.http_adapter._resolve_public_addresses",
                    return_value=((socket.AF_INET, ("127.0.0.1", server.server_port)),),
                ), patch(
                    "apps.providers.http_adapter.ssl.create_default_context",
                    return_value=trusted,
                ):

                    def invoke(payload):
                        return adapter.post_json(
                            url=f"https://provider.example.test:{server.server_port}/invoke",
                            payload=payload,
                            headers={"Authorization": "Bearer " + credential},
                            signing=signing,
                        )

                    negotiated = invoke(
                        {
                            "contract_version": "1",
                            "operation": "connection_test",
                            "environment": "sandbox",
                            "challenge": "synthetic-challenge",
                            "capabilities": ["document_ocr"],
                            "operation_contract": "ic-provider-operations-v1",
                        }
                    )
                    self.assertEqual(
                        negotiated["operation_contract"], "ic-provider-operations-v1"
                    )
                    self.assertEqual(
                        invoke(
                            {
                                "contract_version": "1",
                                "capability": "document_ocr",
                                "environment": "sandbox",
                                "inputs": {},
                            }
                        )["status"],
                        "completed",
                    )
                    binding = {
                        "operation_contract": "ic-provider-operations-v1",
                        "operation_id": "pop_synthetic",
                        "configuration_id": key.key_id,
                        "tenant_id": key.tenant_id,
                        "project_id": "prj_synthetic",
                        "environment": "sandbox",
                        "capability": "document_ocr",
                        "contract_version": "1",
                        "request_sha256": "0" * 64,
                        "lease_generation": 1,
                        "deadline": (timezone.now() + timedelta(minutes=5)).isoformat(),
                        "callback_path": "/api/v1/providers/operations/pop_synthetic/callback",
                        "lease_token": "synthetic-operation-lease-only",
                    }
                    request = {"contract_version": "1", "binding": binding}
                    self.assertEqual(
                        invoke({**request, "operation": "start", "inputs": {}})[
                            "status"
                        ],
                        "pending",
                    )
                    self.assertEqual(
                        invoke({**request, "operation": "poll"})["status"], "pending"
                    )
                    self.assertEqual(runtime.work_once()["status"], "completed")
                    self.assertEqual(
                        invoke({**request, "operation": "poll"})["result"][
                            "extracted_fields"
                        ]["name"],
                        "Synthetic SDK subject",
                    )
                    body, headers = runtime.callback(binding)
                    verify_message(
                        method="POST",
                        path=binding["callback_path"],
                        body=body,
                        headers=headers,
                        keys={key.key_id: key.secret},
                        claim_nonce=lambda *_: True,
                    )
                    self.assertEqual(
                        invoke({**request, "operation": "delete"})["status"], "deleted"
                    )
                    self.assertNotIn("result", invoke({**request, "operation": "poll"}))
                self.assertEqual(observed, [200] * 7)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
