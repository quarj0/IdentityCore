from __future__ import annotations

from django.db import models

from common.crypto import decrypt_json_value, encrypt_json_value


class EncryptedJSONField(models.JSONField):
    def __init__(self, *args, encryption_purpose: str, **kwargs):
        self.encryption_purpose = encryption_purpose
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["encryption_purpose"] = self.encryption_purpose
        return name, path, args, kwargs

    def get_prep_value(self, value):
        prepared = super().get_prep_value(value)
        if prepared is None:
            return None
        return encrypt_json_value(prepared, purpose=self.encryption_purpose)

    def from_db_value(self, value, expression, connection):
        decoded = super().from_db_value(value, expression, connection)
        return decrypt_json_value(decoded, purpose=self.encryption_purpose)

    def to_python(self, value):
        decoded = super().to_python(value)
        return decrypt_json_value(decoded, purpose=self.encryption_purpose)
