from django.db import migrations, models
from django.db.models import F


class Migration(migrations.Migration):
    dependencies = [("products", "0017_batch_aware_stock_transfer")]

    operations = [
        migrations.AddConstraint(
            model_name="productbatch",
            constraint=models.CheckConstraint(
                condition=models.Q(remaining_quantity__lte=F("quantity")),
                name="product_batch_remaining_lte_quantity",
            ),
        ),
        migrations.AddConstraint(
            model_name="stocktransferbatchallocation",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="transfer_batch_allocation_quantity_gt_zero",
            ),
        ),
    ]
