from django.db import models
from django.utils import timezone
from ulid import ULID


def generate_public_id(prefix: str) -> str:
    if not prefix:
        raise ValueError("Public ID prefix must be defined.")
    return f"{prefix}_{ULID()}"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at", "updated_at"])


class BaseModel(TimestampedModel, SoftDeleteModel):
    class Meta:
        abstract = True


class PublicIdModel(models.Model):
    public_id = models.CharField(max_length=64, unique=True, editable=False)
    public_id_prefix = ""

    class Meta:
        abstract = True

    def ensure_public_id(self) -> None:
        if not self.public_id:
            self.public_id = generate_public_id(self.public_id_prefix)

    def save(self, *args, **kwargs):
        self.ensure_public_id()
        return super().save(*args, **kwargs)
