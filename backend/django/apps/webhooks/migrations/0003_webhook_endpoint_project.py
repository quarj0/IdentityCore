import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("projects","0001_initial"),("webhooks","0002_webhookendpoint_signing_key")]
    operations=[migrations.AddField(model_name="webhookendpoint",name="project",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="webhook_endpoints",to="projects.project"))]
