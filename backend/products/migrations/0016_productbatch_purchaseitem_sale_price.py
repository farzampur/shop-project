from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [("products", "0015_inventorytransaction_transfer_types")]

    operations = [
        migrations.AddField(
            model_name="purchaseitem",
            name="sale_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name="قیمت فروش این بچ"),
        ),
        migrations.CreateModel(
            name="ProductBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=15, verbose_name="مقدار بچ")),
                ("remaining_quantity", models.DecimalField(decimal_places=3, max_digits=15, verbose_name="باقی‌مانده بچ")),
                ("purchase_price", models.DecimalField(decimal_places=2, max_digits=15, verbose_name="قیمت خرید")),
                ("sale_price", models.DecimalField(decimal_places=2, max_digits=15, verbose_name="قیمت فروش")),
                ("received_at", models.DateTimeField(default=timezone.now, verbose_name="تاریخ دریافت")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="batches", to="products.product", verbose_name="کالا")),
                ("purchase_item", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="batch", to="products.purchaseitem", verbose_name="قلم خرید")),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="product_batches", to="core.store", verbose_name="فروشگاه")),
            ],
            options={"ordering": ["received_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="productbatch",
            constraint=models.CheckConstraint(condition=models.Q(quantity__gt=0), name="product_batch_quantity_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="productbatch",
            constraint=models.CheckConstraint(condition=models.Q(remaining_quantity__gte=0), name="product_batch_remaining_gte_zero"),
        ),
    ]
