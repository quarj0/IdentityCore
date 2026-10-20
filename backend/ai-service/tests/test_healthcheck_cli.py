import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.healthcheck import check


@pytest.fixture
def readiness_server():
    state = {"status": 200, "body": {"ready": True}, "seen_token": None}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            state["seen_token"] = self.headers.get("X-Internal-Token")
            body = json.dumps(state["body"]).encode()
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/ready", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_ready_probe_authenticates_without_logging_credential(readiness_server):
    url, state = readiness_server
    output = io.StringIO()
    assert check(url=url, token="synthetic-readiness-token", output=output) == 0
    assert state["seen_token"] == "synthetic-readiness-token"
    assert "synthetic-readiness-token" not in output.getvalue()


def test_unready_probe_explains_prerequisites_and_keeps_failure_exit(readiness_server):
    url, state = readiness_server
    state.update(
        status=503,
        body={
            "ready": False,
            "missing_requirements": [
                "models.manifest_missing:/private/model-path",
                "object_storage.endpoint_url",
            ],
        },
    )
    output = io.StringIO()
    assert check(url=url, token="synthetic-readiness-token", output=output) == 1
    assert "models.manifest_missing" in output.getvalue()
    assert "object_storage.endpoint_url" in output.getvalue()
    assert "/private/model-path" not in output.getvalue()


@pytest.mark.parametrize("status", [401, 403])
def test_authentication_failure_does_not_echo_raw_response(readiness_server, status):
    url, state = readiness_server
    state.update(status=status, body={"error": "synthetic-readiness-token"})
    output = io.StringIO()
    assert check(url=url, token="synthetic-readiness-token", output=output) == 1
    assert "AI_SERVICE_SHARED_TOKEN" in output.getvalue()
    assert "synthetic-readiness-token" not in output.getvalue()


def test_bad_status_and_malformed_readiness_cannot_become_healthy(readiness_server):
    url, state = readiness_server
    state.update(status=503, body={"ready": True, "missing_requirements": []})
    assert check(url=url, output=io.StringIO()) == 1
    state.update(
        status=200,
        body={"ready": False, "missing_requirements": "synthetic-sensitive-response"},
    )
    output = io.StringIO()
    assert check(url=url, output=output) == 1
    assert "synthetic-sensitive-response" not in output.getvalue()
