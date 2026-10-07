"""Bind only operator-reviewed legacy context; never manufacture original history."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.audit.services import lock_audit_chain, record_audit_event
from apps.consent.models import ConsentRecord
from apps.consent.services import build_proof
from apps.tenants.models import Tenant
from common.tenant_crypto import key_operation


class Command(BaseCommand):
    help = "Bind a bounded batch of reviewed legacy consent records to archived notice version and evidence scope."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True)
        parser.add_argument("--notice-version", type=int, required=True)
        parser.add_argument(
            "--evidence-scope",
            nargs="+",
            choices=["document", "biometrics"],
            required=True,
        )
        parser.add_argument("--after-pk", type=int, default=0)
        parser.add_argument("--batch-size", type=int, default=100)

    def handle(self, *args, **options):
        if (
            not 1 <= options["batch_size"] <= 1000
            or options["after_pk"] < 0
            or options["notice_version"] < 1
        ):
            raise CommandError("Use valid bounded legacy consent parameters.")
        try:
            with transaction.atomic(), key_operation():
                tenant = Tenant.objects.get(
                    public_id=options["tenant"], deleted_at__isnull=True
                )
                lock_audit_chain(tenant.pk)
                rows = list(
                    ConsentRecord.objects.filter(
                        tenant=tenant,
                        proof_json__isnull=True,
                        pk__gt=options["after_pk"],
                        accepted=True,
                        withdrawn_at__isnull=True,
                        deleted_at__isnull=True,
                    ).order_by("pk")[: options["batch_size"]]
                )
                for record in rows:
                    from apps.verifications.models import Verification

                    Verification.objects.select_for_update(no_key=True).get(
                        pk=record.verification_id, tenant=tenant
                    )
                    record = ConsentRecord.objects.select_for_update(no_key=True).get(
                        pk=record.pk
                    )
                    if record.proof_json is not None or record.withdrawn_at is not None:
                        continue
                    proof = build_proof(
                        record,
                        notice_version=options["notice_version"],
                        source="legacy-reviewed",
                        evidence_scope_override=options["evidence_scope"],
                    )
                    if (
                        record.consent_content_hash
                        and record.consent_content_hash != proof["content_hash"]
                    ):
                        raise ValueError("Legacy notice hash mismatch")
                    record.proof_json = proof
                    record.consent_content_hash = proof["content_hash"]
                    record._legacy_binding_authorized = True
                    record.save(
                        update_fields=[
                            "proof_json",
                            "consent_content_hash",
                            "updated_at",
                        ]
                    )
                last_pk = rows[-1].pk if rows else options["after_pk"]
                record_audit_event(
                    tenant=tenant,
                    action="consent.legacy_proof_bound",
                    target_type="tenant",
                    target_id=tenant.public_id,
                    metadata={
                        "bound_count": len(rows),
                        "last_pk": last_pk,
                        "notice_version": options["notice_version"],
                        "evidence_scope": options["evidence_scope"],
                    },
                )
        except Exception:
            raise CommandError(
                "Legacy consent binding failed; review the archived context."
            ) from None
        self.stdout.write(f"bound={len(rows)} next_after_pk={last_pk}")
