import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("api_clients","0001_initial"),("projects","0001_initial")]
    operations=[migrations.AddField(model_name="apiclient",name="project",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="api_clients",to="projects.project"))]
