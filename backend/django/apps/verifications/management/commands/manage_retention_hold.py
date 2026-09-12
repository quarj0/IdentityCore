from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.audit.services import record_audit_event
from apps.tenants.models import Tenant
from apps.verifications.models import RetentionLegalHold, Verification


class Command(BaseCommand):
    help = "Place or release an audited tenant-scoped retention legal hold."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Tenant slug")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--place", action="store_true")
        action.add_argument("--release", metavar="HOLD_ID")
        parser.add_argument("--verification", help="Optional verification public ID")
        parser.add_argument(
            "--reason", help="Required authorization or incident reason"
        )
        parser.add_argument(
            "--expires-at", help="Optional timezone-aware ISO-8601 expiration"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        tenant = (
            Tenant.objects.select_for_update().filter(slug=options["tenant"]).first()
        )
        if tenant is None:
            raise CommandError("Tenant was not found.")

        if options["place"]:
            hold = self._place(tenant=tenant, options=options)
            self.stdout.write(
                self.style.SUCCESS(f"Placed retention hold {hold.public_id}.")
            )
            return

        hold = (
            RetentionLegalHold.objects.select_for_update()
            .filter(tenant=tenant, public_id=options["release"])
            .first()
        )
        if hold is None:
            raise CommandError("Retention hold was not found for this tenant.")
        if hold.released_at is not None:
            raise CommandError("Retention hold is already released.")
        reason = (options["reason"] or "").strip()
        if not reason:
            raise CommandError("--reason is required to release a hold.")
        hold.released_at = timezone.now()
        hold.save(update_fields=["released_at", "updated_at"])
        record_audit_event(
            tenant=tenant,
            action="retention.legal_hold_released",
            target_type="retention_legal_hold",
            target_id=hold.public_id,
            sensitive_metadata={"reason": reason},
        )
        self.stdout.write(
            self.style.SUCCESS(f"Released retention hold {hold.public_id}.")
        )

    def _place(self, *, tenant: Tenant, options) -> RetentionLegalHold:
        reason = (options["reason"] or "").strip()
        if not reason:
            raise CommandError("--reason is required to place a hold.")

        verification = None
        if options["verification"]:
            verification = Verification.objects.filter(
                tenant=tenant,
                public_id=options["verification"],
            ).first()
            if verification is None:
                raise CommandError("Verification was not found for this tenant.")

        expires_at = None
        if options["expires_at"]:
            expires_at = parse_datetime(options["expires_at"])
            if expires_at is None or timezone.is_naive(expires_at):
                raise CommandError(
                    "--expires-at must be a timezone-aware ISO-8601 value."
                )
            if expires_at <= timezone.now():
                raise CommandError("--expires-at must be in the future.")

        hold = RetentionLegalHold.objects.create(
            tenant=tenant,
            verification=verification,
            reason=reason,
            expires_at=expires_at,
        )
        record_audit_event(
            tenant=tenant,
            action="retention.legal_hold_placed",
            target_type="retention_legal_hold",
            target_id=hold.public_id,
            metadata={
                "scope": "verification" if verification else "tenant",
                "verification_id": verification.public_id if verification else "",
                "expires_at": expires_at.isoformat() if expires_at else "",
            },
            sensitive_metadata={"reason": reason},
        )
        return hold
