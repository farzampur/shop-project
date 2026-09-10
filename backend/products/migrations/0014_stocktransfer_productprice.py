from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0013_barcode_validation"),
        ("core", "0002_auditlog"),
    ]
    operations = [
        migrations.CreateModel(
            name="StockTransfer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("draft", "پیش‌نویس"), ("approved", "تأیید شده"), ("shipped", "ارسال شده"), ("received", "دریافت شده"), ("cancelled", "لغو شده")], default="draft", max_length=20)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
                ("received_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_stock_transfers", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_stock_transfers", to=settings.AUTH_USER_MODEL)),
                ("destination_store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="incoming_transfers", to="core.store")),
                ("source_store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="outgoing_transfers", to="core.store")),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="ProductPrice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("price_type", models.CharField(choices=[("retail", "خرده‌فروشی"), ("wholesale", "عمده‌فروشی"), ("special", "ویژه")], default="retail", max_length=20)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("effective_from", models.DateTimeField(default=django.utils.timezone.now)),
                ("effective_to", models.DateTimeField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_product_prices", to=settings.AUTH_USER_MODEL)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prices", to="products.product")),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="product_prices", to="core.store")),
            ],
            options={"ordering": ["-effective_from", "-id"]},
        ),
        migrations.CreateModel(
            name="StockTransferItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=15)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="stock_transfer_items", to="products.product")),
                ("transfer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="products.stocktransfer")),
            ],
            options={"constraints": [models.UniqueConstraint(fields=("transfer", "product"), name="unique_transfer_product")]},
        ),
    ]
