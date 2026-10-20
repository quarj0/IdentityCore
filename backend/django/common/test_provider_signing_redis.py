"""Actual cross-process nonce claims against an explicitly supplied test Redis."""

import hashlib
import json
import multiprocessing
import os
import time
import uuid
from unittest import skipUnless

from django.conf import settings
from django.core.cache import caches
from django.test import SimpleTestCase, override_settings
from redis import Redis

from common.provider_signing import (
    ProviderSignatureError,
    SIGNATURE_VERSION,
    sign_message,
    verify_message,
)


def _claim_nonce_worker(cache_definition, headers, now, namespace, barrier, result):
    import django

    django.setup()
    try:
        with override_settings(
            CACHES={**settings.CACHES, "provider_signatures": cache_definition}
        ):
            barrier.wait(timeout=20)
            verify_message(
                method="POST",
                path="/check",
                body=b'{"status":"completed"}',
                headers=headers,
                keys={"old": "synthetic-old-key", "new": "synthetic-new-key"},
                now=now,
                expected_nonce=headers["X-IC-Nonce"],
                replay_namespace=namespace,
            )
        result.put("accepted")
    except ProviderSignatureError:
        result.put("replayed")
    except Exception as error:
        result.put(type(error).__name__)


@skipUnless(
    os.getenv("PROVIDER_SIGNING_REDIS_TEST_URL"),
    "Explicit isolated test Redis required",
)
class ProviderSigningRedisTests(SimpleTestCase):
    def test_nonce_is_claimed_once_across_processes_and_rotating_keys(self):
        definition = {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": os.environ["PROVIDER_SIGNING_REDIS_TEST_URL"],
            "KEY_PREFIX": "identitycore-provider-test",
            "OPTIONS": {"socket_connect_timeout": 1, "socket_timeout": 1},
        }
        now = int(time.time())
        nonce = "race_" + uuid.uuid4().hex
        namespace = "provider-test:" + uuid.uuid4().hex
        context = multiprocessing.get_context("spawn")
        barrier = context.Barrier(8)
        result = context.Queue()
        workers = []
        digest = hashlib.sha256(
            json.dumps(
                [SIGNATURE_VERSION, namespace, nonce], separators=(",", ":")
            ).encode()
        ).hexdigest()
        with override_settings(
            CACHES={**settings.CACHES, "provider_signatures": definition}
        ):
            try:
                for index in range(8):
                    key_id, secret = (
                        ("old", "synthetic-old-key")
                        if index % 2
                        else ("new", "synthetic-new-key")
                    )
                    signed = sign_message(
                        method="POST",
                        path="/check",
                        body=b'{"status":"completed"}',
                        key_id=key_id,
                        secret=secret,
                        timestamp=now,
                        nonce=nonce,
                    )
                    worker = context.Process(
                        target=_claim_nonce_worker,
                        args=(
                            definition,
                            signed.headers(),
                            now,
                            namespace,
                            barrier,
                            result,
                        ),
                    )
                    workers.append(worker)
                    worker.start()
                outcomes = [result.get(timeout=30) for _ in workers]
                for worker in workers:
                    worker.join(timeout=5)
                    self.assertEqual(worker.exitcode, 0)
                self.assertEqual(outcomes.count("accepted"), 1, outcomes)
                self.assertEqual(outcomes.count("replayed"), 7, outcomes)
                client = Redis.from_url(definition["LOCATION"])
                try:
                    ttl = client.ttl(caches["provider_signatures"].make_key(digest))
                    self.assertGreater(ttl, 0)
                    self.assertLessEqual(ttl, 600)
                finally:
                    client.close()
            finally:
                for worker in workers:
                    if worker.is_alive():
                        worker.terminate()
                        worker.join(timeout=5)
                caches["provider_signatures"].delete(digest)
                result.close()
                result.join_thread()
