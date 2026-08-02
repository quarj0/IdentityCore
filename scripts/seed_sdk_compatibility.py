#!/usr/bin/env python3
"""Create the deterministic tenant used by the live SDK compatibility tests."""

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "django"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")

import django  # noqa: E402

django.setup()

from apps.accounts.models import PlatformUser, PlatformUserStatus  # noqa: E402
from apps.api_clients.models import APIClient  # noqa: E402
from apps.organizations.models import Organization  # noqa: E402
from apps.tenants.models import Tenant  # noqa: E402
from apps.verification_policies.models import VerificationPolicy  # noqa: E402


secret = "sdk-compatibility-secret"
organization, _ = Organization.objects.get_or_create(
    slug="sdk-compatibility", defaults={"name": "SDK Compatibility"}
)
tenant, _ = Tenant.objects.get_or_create(
    organization=organization,
    slug="sdk-compatibility",
    defaults={"name": "SDK Compatibility", "status": "active"},
)
user = PlatformUser.objects.filter(email="sdk-compatibility@example.com").first()
if user is None:
    user = PlatformUser.objects.create_user(
        email="sdk-compatibility@example.com",
        password="SdkCompatibilityPassword123!",
        tenant=tenant,
        status=PlatformUserStatus.ACTIVE,
    )
client, created = APIClient.objects.get_or_create(
    tenant=tenant,
    name="SDK compatibility tests",
    defaults={
        "created_by": user,
        "scopes_json": ["policies:read", "verifications:create", "verifications:read"],
        "client_secret_hash": "unused",
    },
)
if created or not client.verify_client_secret(secret):
    client.set_client_secret(secret)
    client.save()
policy, _ = VerificationPolicy.objects.get_or_create(
    tenant=tenant,
    name="SDK compatibility policy",
    version=1,
    defaults={
        "status": "active",
        "required_document_types_json": ["national_id"],
        "created_by": user,
    },
)

print(json.dumps({"client_id": client.client_id, "client_secret": secret, "policy_id": policy.public_id}))
