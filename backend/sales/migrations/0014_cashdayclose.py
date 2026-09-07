from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("sales", "0013_ordercancellation"), ("core", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(
        name="CashDayClose",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("close_date", models.DateField(verbose_name="تاریخ کاری")),
            ("opening_balance", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
            ("expected_balance", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
            ("counted_balance", models.DecimalField(decimal_places=2, max_digits=15)),
            ("difference", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
            ("note", models.CharField(blank=True, max_length=500)),
            ("closed_at", models.DateTimeField(auto_now_add=True)),
            ("cashbox", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="day_closes", to="sales.cashbox", verbose_name="صندوق")),
            ("closed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cash_day_closes", to=settings.AUTH_USER_MODEL)),
            ("store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="cash_day_closes", to="core.store", verbose_name="فروشگاه")),
        ],
        options={"ordering": ["-close_date", "-id"], "verbose_name": "بستن روزانه صندوق", "verbose_name_plural": "بستن روزانه صندوق‌ها"},
    ), migrations.AddConstraint(model_name="cashdayclose", constraint=models.UniqueConstraint(fields=("cashbox", "close_date"), name="unique_cashbox_day_close"))]
