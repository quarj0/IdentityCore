import json
import unittest
from unittest.mock import Mock, patch

from check_deployment_health import check


class ReadinessProbeTests(unittest.TestCase):
    def test_transient_unready_candidate_retries_and_requires_fresh_status(self):
        unhealthy = Mock()
        unhealthy.__enter__ = Mock(return_value=unhealthy)
        unhealthy.__exit__ = Mock(return_value=False)
        unhealthy.status = 200
        unhealthy.headers = {"Cache-Control": "no-store"}
        unhealthy.read.return_value = json.dumps(
            {"data": {"status": "unavailable"}}
        ).encode()
        healthy = Mock()
        healthy.__enter__ = Mock(return_value=healthy)
        healthy.__exit__ = Mock(return_value=False)
        healthy.status = 200
        healthy.headers = {"Cache-Control": "no-store"}
        healthy.read.return_value = json.dumps({"data": {"status": "ready"}}).encode()
        opener = Mock()
        opener.open.side_effect = [unhealthy, healthy]
        with patch("check_deployment_health.build_opener", return_value=opener), patch(
            "check_deployment_health.time.sleep"
        ):
            self.assertTrue(check("https://candidate.example.org", timeout=1))
        self.assertEqual(opener.open.call_count, 2)

    def test_unsafe_scheme_and_cookie_origin_credentials_are_rejected_before_request(
        self,
    ):
        with patch("check_deployment_health.build_opener") as opener:
            for base in [
                "http://candidate.example.org",
                "https://user:secret@candidate.example.org",
                "https://candidate.example.org?token=secret",
                "https://candidate.example.org/path",
            ]:
                self.assertFalse(check(base, timeout=1))
            opener.assert_not_called()

    def test_missing_cache_boundary_and_redirects_cannot_certify_readiness(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.status = 302
        response.headers = {}
        response.read.return_value = b'{"data":{"status":"ready"}}'
        opener = Mock()
        opener.open.return_value = response
        with patch("check_deployment_health.build_opener", return_value=opener), patch(
            "check_deployment_health.time.monotonic", side_effect=[0, 0, 0.1, 2, 2]
        ), patch("check_deployment_health.time.sleep"):
            self.assertFalse(check("https://candidate.example.org", timeout=1))


if __name__ == "__main__":
    unittest.main()
