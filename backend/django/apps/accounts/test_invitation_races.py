from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import override_settings
from rest_framework.test import APIClient, APITransactionTestCase

from apps.accounts.models import PlatformUser, TeamInvitation
from apps.accounts.test_invitations import InvitationLifecycleTests
from apps.access_control.models import UserRole
from apps.notifications.models import Notification


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
@override_settings(
    TEAM_INVITATION_BASE_URL="https://dashboard.example.test/accept-invitation"
)
class InvitationRaceTests(APITransactionTestCase):
    password = InvitationLifecycleTests.password
    url = InvitationLifecycleTests.url

    def setUp(self):
        InvitationLifecycleTests.setUp(self)

    def parallel(self, function):
        barrier = Barrier(2)

        def run(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return function(index)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, range(2)))

    @patch("apps.accounts.invitations.enqueue_notification_delivery")
    def test_concurrent_acceptance_consumes_invitation_once(self, enqueue):
        invitation, token, _ = InvitationLifecycleTests.create(self)
        results = self.parallel(
            lambda _: APIClient()
            .post(
                self.url + "/accept",
                {"token": token, "password": self.password},
                format="json",
            )
            .status_code
        )
        self.assertEqual(sorted(results), [200, 400])
        self.assertEqual(PlatformUser.objects.filter(email=invitation.email).count(), 1)
        self.assertEqual(UserRole.objects.filter(role=self.role).count(), 1)

    @patch("apps.accounts.invitations.enqueue_notification_delivery")
    def test_concurrent_creation_has_one_capability_and_one_delivery(self, enqueue):
        def create(_):
            client = APIClient()
            client.force_authenticate(PlatformUser.objects.get(pk=self.actor.pk))
            return client.post(
                self.url,
                {"email": "new@example.test", "role_id": self.role.public_id},
                format="json",
            ).status_code

        self.assertEqual(sorted(self.parallel(create)), [201, 400])
        self.assertEqual(TeamInvitation.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 1)
