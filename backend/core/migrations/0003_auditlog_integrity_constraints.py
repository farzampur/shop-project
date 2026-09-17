from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_auditlog")]

    operations = [
        migrations.AddConstraint(
            model_name="auditlog",
            constraint=models.CheckConstraint(
                condition=models.Q(object_id__isnull=True) | models.Q(object_id__gt=0),
                name="auditlog_object_id_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="auditlog",
            constraint=models.CheckConstraint(
                condition=~models.Q(model_name=""),
                name="auditlog_model_name_nonempty",
            ),
        ),
        migrations.AddConstraint(
            model_name="auditlog",
            constraint=models.CheckConstraint(
                condition=~models.Q(description=""),
                name="auditlog_description_nonempty",
            ),
        ),
    ]
