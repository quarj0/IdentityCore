from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("verifications","0005_verification_project")]
    operations=[migrations.AlterField(model_name="verificationmobilehandoff",name="public_id",field=models.CharField(editable=False,max_length=64,unique=True))]
