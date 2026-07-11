from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[("accounts","0004_preferences_and_invitations")]
    operations=[migrations.AlterField(model_name="teaminvitation",name="deleted_at",field=models.DateTimeField(blank=True,null=True)),migrations.AlterField(model_name="teaminvitation",name="public_id",field=models.CharField(editable=False,max_length=64,unique=True))]
