from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0016_productbatch_purchaseitem_sale_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productbatch",
            name="purchase_item",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="batch",
                to="products.purchaseitem",
                verbose_name="قلم خرید",
            ),
        ),
        migrations.AddField(
            model_name="productbatch",
            name="source_batch",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transferred_batches",
                to="products.productbatch",
                verbose_name="بچ مبدأ انتقال",
            ),
        ),
        migrations.CreateModel(
            name="StockTransferBatchAllocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(decimal_places=3, max_digits=15)),
                ("source_batch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transfer_allocations", to="products.productbatch")),
                ("transfer_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="batch_allocations", to="products.stocktransferitem")),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("transfer_item", "source_batch"),
                        name="unique_transfer_item_source_batch",
                    ),
                ],
            },
        ),
    ]
