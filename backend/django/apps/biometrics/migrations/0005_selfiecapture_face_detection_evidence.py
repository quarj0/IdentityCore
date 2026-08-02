from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("biometrics", "0004_livenesschallenge_and_check_challenge"),
    ]

    operations = [
        migrations.AlterField(
            model_name="selfiecapture",
            name="face_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="selfiecapture",
            name="face_detection_confidence",
            field=models.DecimalField(
                blank=True, decimal_places=4, max_digits=5, null=True
            ),
        ),
        migrations.AddField(
            model_name="selfiecapture",
            name="face_detection_model_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="selfiecapture",
            name="face_detection_model_version",
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
