from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("create", "ایجاد"), ("update", "ویرایش"), ("delete", "حذف"), ("adjust", "تعدیل"), ("payment", "پرداخت"), ("cancel", "لغو"), ("close", "بستن صندوق"), ("login", "ورود"), ("other", "سایر")], max_length=20)),
                ("model_name", models.CharField(max_length=100)),
                ("object_id", models.PositiveIntegerField(blank=True, null=True)),
                ("description", models.CharField(max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("store", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_logs", to="core.store")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"], "verbose_name": "گزارش فعالیت", "verbose_name_plural": "گزارش فعالیت‌ها"},
        )
    ]
