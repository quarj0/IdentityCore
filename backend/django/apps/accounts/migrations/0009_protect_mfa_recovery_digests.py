from django.conf import settings
from django.db import migrations
from django.utils.crypto import salted_hmac


def protect_legacy_digests(apps, schema_editor):
    recovery = apps.get_model("accounts", "MFARecoveryCode")
    rows = recovery.objects.using(schema_editor.connection.alias)
    for row in (
        rows.exclude(code_hash__startswith="v2$")
        .only("pk", "user_id", "code_hash")
        .iterator(chunk_size=500)
    ):
        digest = salted_hmac(
            "identitycore.mfa.recovery-digest.v2",
            f"{row.user_id}|{row.code_hash}",
            secret=settings.MFA_RECOVERY_PEPPER,
            algorithm="sha256",
        ).hexdigest()
        rows.filter(pk=row.pk, code_hash=row.code_hash).update(
            code_hash="v2$" + digest[:61]
        )


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("accounts", "0008_platformuser_auth_valid_after_and_more")]
    operations = [migrations.RunPython(protect_legacy_digests, atomic=False)]
