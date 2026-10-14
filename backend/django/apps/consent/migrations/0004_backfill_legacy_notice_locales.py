from django.db import migrations


class Migration(migrations.Migration):
    # The original locale was not retained before 0002. Mutable templates cannot
    # establish it, even when their content still matches the acceptance snapshot.
    # Preserve existing metadata; any repair needs independently reviewed evidence.
    dependencies = [("consent", "0003_consentrecord_proof_json_and_more")]
    operations = []
