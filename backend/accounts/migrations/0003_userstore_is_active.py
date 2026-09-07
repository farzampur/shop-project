from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_userstore_role")]
    operations = [
        migrations.AddField(
            model_name="userstore",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="فعال"),
        ),
    ]
