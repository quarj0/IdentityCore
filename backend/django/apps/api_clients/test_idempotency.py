from threading import Event, Thread
from types import SimpleNamespace
from unittest import skipUnless

from django.db import close_old_connections, connection, transaction
from django.test import TransactionTestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.idempotency import (
    begin_idempotent_request,
    complete_idempotent_request,
)
from apps.api_clients.models import APIClient
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class IdempotencyConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        organization = Organization.objects.create(
            name="Concurrent Org", slug="concurrent-org", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Concurrent Tenant",
            slug="concurrent-tenant",
            status="active",
        )
        user = PlatformUser.objects.create_user(
            email="concurrent@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        api_client = APIClient(
            tenant=self.tenant,
            created_by=user,
            name="Concurrent client",
            scopes_json=["verifications:create"],
        )
        api_client.set_client_secret("concurrent-secret")
        api_client.save()
        self.api_client_id = api_client.pk
        self.tenant_id = self.tenant.pk

    @staticmethod
    def _request(api_client):
        return SimpleNamespace(
            data={"purpose": "Concurrent request"},
            method="POST",
            path="/api/v1/verifications/",
            headers={"Idempotency-Key": "concurrent-key"},
            api_client=api_client,
        )

    @skipUnless(
        connection.vendor == "postgresql",
        "Concurrent idempotency locking requires PostgreSQL.",
    )
    def test_concurrent_same_key_waits_and_replays_original_response(self):
        first_claimed = Event()
        second_started = Event()
        results = {}
        errors = []

        def first_request():
            close_old_connections()
            try:
                api_client = APIClient.objects.get(pk=self.api_client_id)
                tenant = Tenant.objects.get(pk=self.tenant_id)
                with transaction.atomic():
                    result = begin_idempotent_request(
                        request=self._request(api_client),
                        tenant=tenant,
                        operation="verification.create",
                    )
                    first_claimed.set()
                    if not second_started.wait(timeout=5):
                        raise AssertionError("The concurrent request did not start.")
                    complete_idempotent_request(
                        result,
                        response_data={"id": "ver_original"},
                        response_status=201,
                    )
                    results["first"] = result.is_replay
            except Exception as exc:  # pragma: no cover - asserted in parent thread
                errors.append(exc)
            finally:
                close_old_connections()

        def second_request():
            close_old_connections()
            try:
                if not first_claimed.wait(timeout=5):
                    raise AssertionError("The first request did not claim the key.")
                second_started.set()
                api_client = APIClient.objects.get(pk=self.api_client_id)
                tenant = Tenant.objects.get(pk=self.tenant_id)
                with transaction.atomic():
                    result = begin_idempotent_request(
                        request=self._request(api_client),
                        tenant=tenant,
                        operation="verification.create",
                    )
                    results["second"] = (
                        result.is_replay,
                        result.response_data,
                        result.response_status,
                    )
            except Exception as exc:  # pragma: no cover - asserted in parent thread
                errors.append(exc)
            finally:
                close_old_connections()

        threads = [Thread(target=first_request), Thread(target=second_request)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertFalse(results["first"])
        self.assertEqual(results["second"], (True, {"id": "ver_original"}, 201))
