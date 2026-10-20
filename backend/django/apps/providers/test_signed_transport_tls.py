"""Exercise the real signed HTTP transport against a private TLS fixture."""

import json
import socket
import ssl
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.providers.http_adapter import (
    SecureHTTPAdapterError,
    SecureHTTPProviderAdapter,
)
from common.provider_signing import (
    ProviderSigningContext,
    derive_provider_signing_secret,
    sign_message,
    verify_message,
)


class SignedProviderTLSIntegrationTests(SimpleTestCase):
    def test_exact_wire_signatures_over_verified_tls_and_tamper_rejection(self):
        credential = "synthetic-provider-credential-for-tls-test"
        signing = ProviderSigningContext(
            "configuration-one",
            derive_provider_signing_secret(credential),
            "provider-response:tls-fixture:sandbox",
        )
        observed = []
        errors = []
        tamper = False

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                try:
                    body = self.rfile.read(int(self.headers["Content-Length"]))
                    verify_message(
                        method="POST",
                        path=self.path,
                        body=body,
                        headers=dict(self.headers.items()),
                        keys={signing.key_id: signing.secret},
                        claim_nonce=lambda _key, _ttl: True,
                    )
                    if self.headers.get("Authorization") != "Bearer " + credential:
                        raise ValueError("Synthetic fixture authorization failed")
                    observed.append(json.loads(body))
                    response = json.dumps(
                        {"status": "completed", "score": 1.0, "text": "é"},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode("utf-8")
                    proof = sign_message(
                        method="POST",
                        path=self.path,
                        body=response,
                        key_id=signing.key_id,
                        secret=signing.secret,
                        nonce=self.headers["X-IC-Nonce"],
                    )
                    wire = response + b" " if tamper else response
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(wire)))
                    for key, value in proof.headers().items():
                        self.send_header(key, value)
                    self.end_headers()
                    self.wfile.write(wire)
                except Exception as error:
                    errors.append(type(error).__name__)
                    self.send_error(500)

        with tempfile.TemporaryDirectory(
            prefix="identitycore-provider-tls-"
        ) as directory:
            key = Path(directory) / "private.key"
            certificate = Path(directory) / "certificate.pem"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-keyout",
                    str(key),
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
            key.chmod(0o600)
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.load_cert_chain(certificate, key)
            server.socket = tls.wrap_socket(server.socket, server_side=True)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                trusted = ssl.create_default_context(cafile=str(certificate))
                self.assertTrue(trusted.check_hostname)
                self.assertEqual(trusted.verify_mode, ssl.CERT_REQUIRED)
                port = server.server_port
                adapter = SecureHTTPProviderAdapter(
                    {
                        "allowed_hosts": ["provider.example.test"],
                        "timeout_seconds": 5,
                        "https_proxy": "",
                    }
                )
                # Only the fixture destination resolution is replaced. The real
                # socket connection, TLS verification, HTTP and signer execute.
                with patch(
                    "apps.providers.http_adapter._resolve_public_addresses",
                    return_value=((socket.AF_INET, ("127.0.0.1", port)),),
                ), patch(
                    "apps.providers.http_adapter.ssl.create_default_context",
                    return_value=trusted,
                ):
                    arguments = {
                        "url": f"https://provider.example.test:{port}/invoke",
                        "payload": {"value": 1.0, "text": "é"},
                        "headers": {"Authorization": "Bearer " + credential},
                        "signing": signing,
                    }
                    self.assertEqual(
                        adapter.post_json(**arguments),
                        {"status": "completed", "score": 1.0, "text": "é"},
                    )
                    tamper = True
                    with self.assertRaises(SecureHTTPAdapterError) as error:
                        adapter.post_json(**arguments)
                    self.assertEqual(
                        error.exception.error_code, "provider_signature_invalid"
                    )
                self.assertEqual(errors, [])
                self.assertEqual(len(observed), 2)
                self.assertEqual(observed[0], arguments["payload"])
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=5)
