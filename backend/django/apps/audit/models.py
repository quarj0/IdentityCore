from django.utils.ipv6 import clean_ipv6_address

from django.utils import timezone

from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.core.models import PublicIdModel


class AuditActorType(models.TextChoices):
    PLATFORM_USER = "platform_user", "Platform User"
    API_CLIENT = "api_client", "API Client"
    VERIFICATION_SUBJECT = "verification_subject", "Verification Subject"
    SYSTEM = "system", "System"
    PROVIDER = "provider", "Provider"


class AuditEventQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Audit events are append-only and may not be updated.")

    def delete(self):
        raise ValidationError("Audit events are append-only and may not be deleted.")

    def bulk_create(self, objs, **kwargs):
        raise ValidationError("Audit events must be appended individually.")

    def bulk_update(self, objs, fields, **kwargs):
        raise ValidationError("Audit events are append-only and may not be updated.")


class AuditEvent(PublicIdModel):
    public_id_prefix = "aud"

    objects = AuditEventQuerySet.as_manager()

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor_type = models.CharField(
        max_length=32, choices=AuditActorType.choices, db_index=True
    )
    actor_id = models.CharField(max_length=64, blank=True, db_index=True)
    action = models.CharField(max_length=120, db_index=True)
    target_type = models.CharField(max_length=64, db_index=True)
    target_id = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    sensitive_metadata_hash = models.CharField(max_length=64, blank=True)
    previous_event_hash = models.CharField(max_length=64, blank=True, editable=False)
    integrity_hash = models.CharField(
        max_length=64, blank=True, editable=False, db_index=True
    )
    integrity_version = models.PositiveSmallIntegerField(default=2, editable=False)
    integrity_key_id = models.CharField(max_length=255, default="", editable=False)
    authentication_tag = models.CharField(max_length=64, default="", editable=False)
    created_at = models.DateTimeField(
        default=timezone.now, db_index=True, editable=False
    )

    class Meta:
        ordering = ["-created_at"]
        base_manager_name = "objects"

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError(
                "Audit events are append-only and may not be updated."
            )
        from apps.audit.services import lock_audit_chain

        if self.tenant_id is None:
            from apps.accounts.models import PlatformUser

            if (
                self.actor_type != AuditActorType.PLATFORM_USER
                or not PlatformUser.objects.filter(
                    public_id=self.actor_id,
                    is_platform_admin=True,
                    tenant__isnull=True,
                ).exists()
            ):
                raise ValidationError(
                    "Platform audit events require a tenantless administrator actor."
                )

        lock_audit_chain(self.tenant_id)
        previous = (
            type(self).objects.filter(tenant_id=self.tenant_id).order_by("-id").first()
        )
        self.previous_event_hash = previous.integrity_hash if previous else ""
        from apps.audit.integrity import event_authentication, event_hash
        from common.crypto import get_active_key

        self.ensure_public_id()
        self.created_at = timezone.now()
        if self.ip_address and ":" in self.ip_address:
            self.ip_address = clean_ipv6_address(self.ip_address)
        self.integrity_version = 2
        self.integrity_key_id = get_active_key().key_id
        self.integrity_hash = event_hash(self)
        self.authentication_tag = event_authentication(self)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit events are append-only and may not be deleted.")

    def __str__(self) -> str:
        return self.public_id
