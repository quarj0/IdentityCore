from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature

from apps.audit.models import AuditEvent
from apps.audit.services import verify_audit_chain
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class AuditAppendConcurrencyTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_concurrent_appends_have_one_authenticated_chain(self):
        organization = Organization.objects.create(name="Audit Race", slug="audit-race")
        tenant = Tenant.objects.create(
            organization=organization,
            name="Audit Race",
            slug="audit-race",
            status="active",
        )
        barrier = Barrier(2)

        def append(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return AuditEvent.objects.create(
                    tenant_id=tenant.pk,
                    actor_type="system",
                    action="race.append",
                    target_type="test",
                    target_id=str(index),
                ).pk
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(append, index) for index in range(2)]
            ids = [future.result(timeout=20) for future in futures]
        self.assertEqual(len(set(ids)), 2)
        events = list(AuditEvent.objects.filter(tenant=tenant).order_by("id"))
        self.assertEqual(events[0].previous_event_hash, "")
        self.assertEqual(events[1].previous_event_hash, events[0].integrity_hash)
        self.assertEqual(verify_audit_chain(tenant_id=tenant.pk), (True, ""))
