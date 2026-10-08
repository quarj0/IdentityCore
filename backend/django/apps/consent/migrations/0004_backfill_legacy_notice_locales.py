from django.db import migrations


def backfill_legacy_notice_locales(apps, schema_editor):
    records = apps.get_model("consent", "ConsentRecord")._base_manager.using(
        schema_editor.connection.alias
    )
    # The locale field was introduced with an English default. Only records
    # without a fingerprint or immutable proof can carry that legacy default.
    legacy = records.filter(
        proof_json__isnull=True,
        consent_content_hash="",
        consent_locale="en",
        consent_template__isnull=False,
    ).select_related("consent_template")
    for record in legacy.iterator(chunk_size=500):
        language = record.consent_template.language
        if language:
            records.filter(pk=record.pk).update(consent_locale=language)


class Migration(migrations.Migration):
    dependencies = [("consent", "0003_consentrecord_proof_json_and_more")]
    operations = [
        migrations.RunPython(backfill_legacy_notice_locales, migrations.RunPython.noop)
    ]
