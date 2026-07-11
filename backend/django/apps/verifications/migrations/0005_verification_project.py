import django.db.models.deletion
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("projects","0001_initial"),("verifications","0004_verificationmobilehandoff")]
    operations=[migrations.AddField(model_name="verification",name="project",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="verifications",to="projects.project"))]
