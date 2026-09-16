from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0016_cartitem_unique_product_price_type"),
        ("products", "0016_productbatch_purchaseitem_sale_price"),
    ]
    operations = [
        migrations.CreateModel(
            name="OrderItemBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=15)),
                ("batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_allocations", to="products.productbatch")),
                ("order_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batch_allocations", to="sales.orderitem")),
            ],
        ),
        migrations.AddConstraint(
            model_name="orderitembatch",
            constraint=models.UniqueConstraint(fields=("order_item", "batch"), name="unique_order_item_batch"),
        ),
    ]
