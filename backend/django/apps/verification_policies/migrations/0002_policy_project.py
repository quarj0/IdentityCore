import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("projects","0001_initial"),("verification_policies","0001_initial")]
    operations=[migrations.AddField(model_name="verificationpolicy",name="project",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="verification_policies",to="projects.project"))]
