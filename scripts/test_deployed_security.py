"""Exercise the promotion gate through a real, locally owned TLS listener."""

import json
import ssl
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from check_deployed_security import CheckFailed, origin, run, security_headers
from email.message import Message


class DeploymentChecksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        cls.cert = root / "cert.pem"
        key = root / "key.pem"
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
                str(cls.cert),
                "-days",
                "1",
                "-subj",
                "/CN=localhost",
                "-addext",
                "subjectAltName=DNS:localhost",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.mode = ""
        cls.revocations = 0
        owner = cls

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_OPTIONS(self):
                self.respond()

            def do_GET(self):
                self.respond()

            def do_POST(self):
                self.respond()

            def do_DELETE(self):
                self.respond()

            def respond(self):
                if self.headers.get("Content-Length"):
                    self.rfile.read(int(self.headers["Content-Length"]))
                status = 200
                if self.path == "/api/v1/auth/me":
                    status = 200 if owner.mode == "anonymous" else 401
                if self.path == "/api/v1/auth/login" and self.command == "GET":
                    status = 405
                if (
                    self.path == "/api/verification/session"
                    and self.headers.get("Origin") == "https://unapproved.invalid"
                ):
                    status = 403
                if owner.mode == "redirect" and self.path == "/api/v1/health":
                    status = 302
                self.send_response(status)
                if owner.mode != "hsts":
                    self.send_header("Strict-Transport-Security", "max-age=31536000")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; script-src 'self' 'nonce-test'"
                    + (
                        "; script-src-elem * 'unsafe-inline'"
                        if owner.mode == "script_elements"
                        else ""
                    ),
                )
                if self.command == "OPTIONS":
                    incoming = self.headers.get("Origin")
                    if incoming == owner.base or owner.mode == "cors":
                        self.send_header("Access-Control-Allow-Origin", incoming)
                        self.send_header("Access-Control-Allow-Credentials", "true")
                        self.send_header(
                            "Access-Control-Allow-Methods", "GET, POST, OPTIONS"
                        )
                        self.send_header(
                            "Access-Control-Allow-Headers",
                            "content-type,x-identitycore-session-scope",
                        )
                        self.send_header("Vary", "Origin")
                if self.command == "POST" and status == 200:
                    if self.path == "/api/v1/auth/login":
                        secure = "" if owner.mode == "cookie" else "; Secure"
                        self.send_header(
                            "Set-Cookie",
                            "identitycore_refresh_dashboard=fixture-secret; Path=/api/v1/auth/; HttpOnly; SameSite=Lax"
                            + secure,
                        )
                    if self.path == "/api/verification/session":
                        for name in (
                            "__Host-identitycore_verify",
                            "__Host-identitycore_verify_id",
                        ):
                            self.send_header(
                                "Set-Cookie",
                                f"{name}=fixture-secret; Path=/; HttpOnly; Secure; SameSite=Strict",
                            )
                    if self.path == "/api/v1/auth/logout":
                        owner.revocations += 1
                self.end_headers()
                self.wfile.write(json.dumps({"data": {"status": "ok"}}).encode())

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(cls.cert), str(key))
        cls.server.socket = context.wrap_socket(cls.server.socket, server_side=True)
        cls.base = f"https://localhost:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def setUp(self):
        type(self).mode = ""
        self.config = {
            "environment": "sandbox",
            "api": self.base,
            "dashboard": self.base,
            "portal": self.base,
            "approved_origins": [self.base],
        }
        self.credentials = {
            "email": "fixture@example.invalid",
            "password": "fixture-secret",
            "session_id": "fixture",
            "session_token": "fixture-secret",
        }

    def test_tls_end_to_end_and_report_does_not_expose_secrets(self):
        report = run(self.config, self.credentials, ca_file=str(self.cert))
        self.assertTrue(report["passed"], report)
        self.assertNotIn("fixture-secret", json.dumps(report))
        self.assertNotIn("fixture@example.invalid", json.dumps(report))

    def test_unsafe_deployments_fail_and_cookie_sessions_are_revoked(self):
        for mode, check in [
            ("hsts", "api_tls_headers"),
            ("cors", "environment_cors"),
            ("cookie", "dashboard_refresh_cookie"),
            ("anonymous", "endpoint_boundaries"),
            ("redirect", "api_tls_headers"),
        ]:
            with self.subTest(mode=mode):
                type(self).mode = mode
                before = type(self).revocations
                report = run(self.config, self.credentials, ca_file=str(self.cert))
                self.assertFalse(report["passed"])
                self.assertFalse(
                    next(
                        item["passed"]
                        for item in report["checks"]
                        if item["check"] == check
                    )
                )
                self.assertEqual(type(self).revocations, before + 1)

    def test_effective_script_element_override_blocks_promotion(self):
        type(self).mode = "script_elements"
        report = run(self.config, self.credentials, ca_file=str(self.cert))
        self.assertFalse(report["passed"])
        self.assertFalse(
            next(
                item["passed"]
                for item in report["checks"]
                if item["check"] == "dashboard_tls_headers"
            )
        )

    def test_duplicate_script_and_framing_directives_follow_browser_semantics(self):
        headers = Message()
        headers["Strict-Transport-Security"] = "max-age=31536000"
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Referrer-Policy"] = "no-referrer"
        headers["X-Frame-Options"] = "DENY"
        prefix = "default-src 'self'; object-src 'none'; base-uri 'self'; "
        for suffix in [
            "frame-ancestors 'none'; script-src *; script-src 'self'",
            "frame-ancestors 'none'; script-src 'self'; script-src-attr 'unsafe-inline'",
            "frame-ancestors *; script-src 'self'",
        ]:
            headers["Content-Security-Policy"] = prefix + suffix
            with self.subTest(suffix=suffix), self.assertRaises(CheckFailed):
                security_headers(headers, html=True)
            del headers["Content-Security-Policy"]

    def test_stale_cookie_policy_still_revokes_the_issued_session(self):
        self.config["refresh_cookie_name"] = "wrong_cookie_name"
        before = type(self).revocations
        report = run(self.config, self.credentials, ca_file=str(self.cert))
        self.assertFalse(report["passed"])
        self.assertEqual(type(self).revocations, before + 1)

    def test_untrusted_certificate_fails_without_sensitive_error(self):
        report = run(self.config, self.credentials)
        self.assertFalse(report["passed"])
        self.assertNotIn("CERTIFICATE", json.dumps(report))

    def test_invalid_configuration_fails_before_requests(self):
        for value in (
            "http://localhost",
            "https://user:secret@localhost",
            "https://localhost/a",
            "https://localhost?token=secret",
            "https://localhost#secret",
        ):
            with self.subTest(value=value), self.assertRaises(CheckFailed):
                origin(value)
        with self.assertRaises(CheckFailed):
            run(self.config, {})
        self.config["approved_origins"] = []
        with self.assertRaises(CheckFailed):
            run(self.config, self.credentials)


if __name__ == "__main__":
    unittest.main()
