from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("sales", "0012_financial_core")]
    operations = [migrations.CreateModel(name="OrderCancellation", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("cancelled_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان لغو")),
        ("reason", models.CharField(blank=True, max_length=500, verbose_name="علت لغو")),
        ("cancelled_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_cancellations", to=settings.AUTH_USER_MODEL, verbose_name="لغوکننده")),
        ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="cancellation", to="sales.order", verbose_name="سفارش")),
    ], options={"verbose_name":"تاریخچه لغو فروش","verbose_name_plural":"تاریخچه لغو فروش‌ها","ordering":["-cancelled_at","-id"]})]
