from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event, Lock, local
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from apps.providers.models import Provider, ProviderCheckType
from apps.providers.services import get_or_create_system_provider


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL commits")
class SystemProviderCreationRaceTests(TransactionTestCase):
    def test_commit_between_lookup_and_unique_validation_returns_existing_provider(
        self,
    ):
        ready = Barrier(2)
        first_committed = Event()
        lock = Lock()
        thread_state = local()
        calls = 0
        original = Provider.full_clean

        def full_clean(provider, *args, **kwargs):
            nonlocal calls
            with lock:
                calls += 1
                thread_state.order = calls
            ready.wait(timeout=15)
            if thread_state.order == 2:
                self.assertTrue(first_committed.wait(timeout=15))
            return original(provider, *args, **kwargs)

        def create(_):
            close_old_connections()
            try:
                return get_or_create_system_provider(
                    ProviderCheckType.DOCUMENT_QUALITY
                ).pk
            finally:
                if getattr(thread_state, "order", None) == 1:
                    first_committed.set()
                close_old_connections()

        with patch.object(Provider, "full_clean", full_clean), ThreadPoolExecutor(
            max_workers=2
        ) as pool:
            results = list(pool.map(create, range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(Provider.objects.count(), 1)
