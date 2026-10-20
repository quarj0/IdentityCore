from email.message import Message
from unittest.mock import Mock, patch

from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from redis.exceptions import ConnectionError as RedisConnectionError

from common.provider_signing import (
    ProviderSigningContext,
    derive_provider_signing_secret,
    sign_message,
    verify_message,
)
from apps.providers.configuration import (
    activate_configuration,
    create_configuration,
    invoke_configured_provider,
    test_configuration,
    validate_public_configuration,
)
from apps.providers.http_adapter import (
    SecureHTTPAdapterError,
    SecureHTTPProviderAdapter,
)
from apps.providers import test_configuration as configuration_fixtures


class SignedTransportTests(SimpleTestCase):
    def setUp(self):
        caches["provider_signatures"].clear()
        self.context = ProviderSigningContext(
            "key-one", "synthetic-signing-secret", "provider-response:one:sandbox"
        )
        self.adapter = SecureHTTPProviderAdapter(
            {
                "allowed_hosts": ["provider.example.test"],
                "timeout_seconds": 5,
                "https_proxy": "",
            }
        )
        self.connection = Mock()
        self.connection.sock = Mock()
        self.response_body = b'{"status":"completed","score":1.0}'
        self.mutate_headers = lambda headers: headers
        self.response_calls = 0
        self.response_status = 200
        self.content_type = "application/json"

        def response():
            self.response_calls += 1
            request = self.connection.request.call_args
            outgoing = request.kwargs["headers"]
            # Verify the bytes actually sent, not a separate JSON serialization.
            verify_message(
                method="POST",
                path=request.args[1],
                body=request.kwargs["body"],
                headers=outgoing,
                keys={self.context.key_id: self.context.secret},
                claim_nonce=lambda _key, _ttl: True,
            )
            signed = sign_message(
                method="POST",
                path=request.args[1],
                body=self.response_body,
                key_id=self.context.key_id,
                secret=self.context.secret,
                nonce=outgoing["X-IC-Nonce"],
            )
            headers = Message()
            headers["Content-Type"] = self.content_type
            for key, value in self.mutate_headers(signed.headers()).items():
                headers[key] = value
            result = Mock()
            result.status = self.response_status
            result.headers = headers
            result.read1.side_effect = [self.response_body, b""]
            return result

        self.connection.getresponse.side_effect = response
        self.connection_patch = patch(
            "apps.providers.http_adapter._PinnedHTTPSConnection",
            return_value=self.connection,
        )
        self.address_patch = patch(
            "apps.providers.http_adapter._resolve_public_addresses",
            return_value=((2, ("8.8.8.8", 443)),),
        )
        self.connection_patch.start()
        self.address_patch.start()
        self.addCleanup(self.connection_patch.stop)
        self.addCleanup(self.address_patch.stop)

    def invoke(self):
        return self.adapter.post_json(
            url="https://provider.example.test/check",
            payload={"value": 1.0, "text": "é"},
            signing=self.context,
        )

    def test_signed_request_and_exact_response_bytes_are_verified(self):
        self.assertEqual(self.invoke(), {"status": "completed", "score": 1.0})
        self.assertEqual(
            self.connection.request.call_args.kwargs["body"],
            b'{"value":1.0,"text":"\\u00e9"}',
        )
        self.assertNotIn(self.context.secret, repr(self.context))

    def test_invalid_missing_stale_and_unbound_responses_fail_closed(self):
        for header, value in [
            ("X-IC-Signature", "0" * 64),
            ("X-IC-Nonce", "another-nonce"),
            ("X-IC-Timestamp", "1"),
            ("X-IC-Signature", None),
        ]:
            with self.subTest(header=header, value=value):

                def mutate(headers):
                    if value is None:
                        headers.pop(header)
                    else:
                        headers[header] = value
                    return headers

                self.mutate_headers = mutate
                with self.assertRaises(SecureHTTPAdapterError) as error:
                    self.invoke()
                self.assertEqual(
                    error.exception.error_code, "provider_signature_invalid"
                )
                self.assertFalse(error.exception.retryable)

    def test_shared_store_failure_returns_controlled_retryable_failure(self):
        with patch("common.provider_signing.caches") as stores:
            stores.__getitem__.return_value.add.side_effect = RedisConnectionError(
                "synthetic outage"
            )
            with self.assertRaises(SecureHTTPAdapterError) as error:
                self.invoke()
        self.assertEqual(
            error.exception.error_code, "provider_replay_store_unavailable"
        )
        self.assertTrue(error.exception.retryable)

    def test_unsigned_http_errors_cannot_control_routing(self):
        for status in (400, 401, 408, 425, 429, 500, 503):
            with self.subTest(status=status):
                self.response_status = status
                self.content_type = "text/html"
                self.response_body = b"upstream failure"
                self.mutate_headers = lambda _headers: {}
                with self.assertRaises(SecureHTTPAdapterError) as error:
                    self.invoke()
                self.assertEqual(
                    error.exception.error_code, "provider_signature_invalid"
                )
                self.assertFalse(error.exception.retryable)

    def test_authenticated_http_errors_preserve_retry_classification(self):
        self.response_body = b"upstream failure"
        self.content_type = "text/plain"
        for status in (400, 401, 408, 425, 429, 500, 503):
            with self.subTest(status=status):
                self.response_status = status
                with self.assertRaises(SecureHTTPAdapterError) as error:
                    self.invoke()
                self.assertEqual(error.exception.error_code, f"provider_http_{status}")
                self.assertEqual(
                    error.exception.retryable, status in (408, 425, 429, 500, 503)
                )

    def test_authenticated_error_replay_is_rejected(self):
        self.response_status = 503

        def outgoing(**kwargs):
            return sign_message(**{**kwargs, "nonce": "fixed-error-nonce"})

        with patch("apps.providers.http_adapter.sign_message", side_effect=outgoing):
            for expected in ("provider_http_503", "provider_signature_invalid"):
                with self.assertRaises(SecureHTTPAdapterError) as error:
                    self.invoke()
                self.assertEqual(error.exception.error_code, expected)

    def test_signed_error_body_limits_still_apply(self):
        self.response_status = 503
        self.adapter.max_response_bytes = 4
        with self.assertRaises(SecureHTTPAdapterError) as error:
            self.invoke()
        self.assertEqual(error.exception.error_code, "provider_response_too_large")

    def test_replayed_response_is_rejected(self):
        signed = sign_message(
            method="POST",
            path="/check",
            body=b"ignored",
            key_id=self.context.key_id,
            secret=self.context.secret,
            nonce="fixed-outgoing-nonce",
        )

        def outgoing(**kwargs):
            return sign_message(**{**kwargs, "nonce": signed.nonce})

        with patch("apps.providers.http_adapter.sign_message", side_effect=outgoing):
            self.invoke()
            with self.assertRaises(SecureHTTPAdapterError) as error:
                self.invoke()
        self.assertEqual(error.exception.error_code, "provider_signature_invalid")


class SignedConfigurationTests(TestCase):
    def setUp(self):
        self.fixture = configuration_fixtures.ConfigurationTests()
        self.fixture.setUp()

    def test_connection_test_and_runtime_receive_scoped_signing_context(self):
        fixture = self.fixture
        fixture.public = {**fixture.public, "signing_mode": "hmac_v1"}
        config = fixture.create()
        contexts = []

        def reply(**kwargs):
            contexts.append(kwargs["signing"])
            payload = kwargs["payload"]
            if payload.get("operation") == "connection_test":
                return {
                    "status": "completed",
                    "contract_version": "1",
                    "challenge": payload["challenge"],
                    "capabilities": payload["capabilities"],
                }
            return {
                "status": "completed",
                "contract_version": "1",
                "capability": "document_ocr",
            }

        with patch(
            "apps.providers.configuration.SecureHTTPProviderAdapter.post_json",
            side_effect=reply,
        ):
            checked = test_configuration(config=config, user=fixture.requester)
            activate_configuration(config=checked, user=fixture.requester)
            invoke_configured_provider(
                provider=fixture.provider,
                environment="sandbox",
                capability="document_ocr",
                inputs={},
                timeout_seconds=5,
            )
        self.assertEqual(len(contexts), 2)
        for context in contexts:
            self.assertEqual(context.key_id, config.public_id)
            self.assertEqual(
                context.secret,
                derive_provider_signing_secret(fixture.credentials["api_key"]),
            )
            self.assertEqual(
                context.replay_namespace,
                f"provider-response:{fixture.provider.public_id}:sandbox",
            )

    def test_invalid_signing_modes_are_validation_errors(self):
        for mode in ["unsupported", None, [], {}]:
            with self.subTest(mode=mode), self.assertRaises(ValidationError):
                validate_public_configuration(
                    {**self.fixture.public, "signing_mode": mode}
                )

    def _promote_modes(self, source_mode, target_mode):
        fixture = self.fixture
        if source_mode is not None:
            fixture.public = {**fixture.public, "signing_mode": source_mode}
        source = fixture.sandbox()
        configuration = {**fixture.public}
        if target_mode is None:
            configuration.pop("signing_mode", None)
        else:
            configuration["signing_mode"] = target_mode
        return create_configuration(
            provider=fixture.provider,
            user=fixture.requester,
            environment="production",
            public_configuration=configuration,
            credentials={"api_key": "independent-production-credential"},
            source=source,
        )

    def test_promotion_diff_shows_explicit_authentication_downgrade(self):
        config = self._promote_modes("hmac_v1", "bearer")
        self.assertEqual(
            config.diff_json["signing_mode"], {"before": "hmac_v1", "after": "bearer"}
        )

    def test_promotion_diff_shows_omitted_legacy_mode_upgrade(self):
        config = self._promote_modes(None, "hmac_v1")
        self.assertEqual(
            config.diff_json["signing_mode"], {"before": "bearer", "after": "hmac_v1"}
        )

    def test_promotion_diff_shows_omitted_target_authentication_downgrade(self):
        config = self._promote_modes("hmac_v1", None)
        self.assertEqual(
            config.diff_json["signing_mode"], {"before": "hmac_v1", "after": "bearer"}
        )

    def test_equivalent_legacy_modes_do_not_create_a_false_diff(self):
        config = self._promote_modes(None, "bearer")
        self.assertNotIn("signing_mode", config.diff_json)
