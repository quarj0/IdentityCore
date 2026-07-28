from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("consent", "0001_initial"),
        ("verification_policies", "0002_policy_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="verificationpolicy",
            name="consent_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="verification_policies",
                to="consent.consenttemplate",
            ),
        ),
        migrations.AddField(
            model_name="verificationpolicy",
            name="default_locale",
            field=models.CharField(default="en", max_length=16),
        ),
        migrations.AddField(
            model_name="verificationpolicy",
            name="supported_locales_json",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
