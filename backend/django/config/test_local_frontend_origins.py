from django.conf import settings
from django.test import SimpleTestCase


class SampleEnvironmentOriginsTests(SimpleTestCase):
    def test_sample_cors_allows_every_local_frontend(self):
        sample = (settings.BASE_DIR.parent.parent / ".env.example").read_text()
        value = next(
            line.split("=", 1)[1]
            for line in sample.splitlines()
            if line.startswith("DJANGO_CORS_ALLOWED_ORIGINS=")
        )
        allowed = set(value.split(","))
        expected = {
            f"http://{host}:{port}"
            for host in ("localhost", "127.0.0.1")
            for port in range(3000, 3005)
        }
        self.assertTrue(expected.issubset(allowed), expected - allowed)
