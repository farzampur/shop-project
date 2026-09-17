from django.db import migrations, models
from django.db.models import F


class Migration(migrations.Migration):
    dependencies = [("products", "0021_purchase_pricing_integrity_constraints")]

    operations = [
        migrations.AddConstraint(
            model_name="purchase",
            constraint=models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="purchase_total_amount_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="purchasereturn",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="purchase_return_quantity_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="purchasereturn",
            constraint=models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="purchase_return_unit_price_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="purchasereturn",
            constraint=models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="purchase_return_total_amount_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="stocktransfer",
            constraint=models.CheckConstraint(
                condition=~models.Q(source_store=F("destination_store")),
                name="stock_transfer_source_destination_different",
            ),
        ),
        migrations.AddConstraint(
            model_name="stocktransferitem",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="stock_transfer_item_quantity_gt_zero",
            ),
        ),
    ]
