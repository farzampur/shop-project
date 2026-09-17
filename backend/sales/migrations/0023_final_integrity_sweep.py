from django.db import migrations, models
from django.db.models import F


class Migration(migrations.Migration):
    dependencies = [("sales", "0022_order_document_integrity_constraints")]

    operations = [
        migrations.AddConstraint(
            model_name="orderitembatch",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="order_item_batch_quantity_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="cashtransfer",
            constraint=models.CheckConstraint(
                condition=~models.Q(from_cashbox=F("to_cashbox")),
                name="cash_transfer_cashboxes_different",
            ),
        ),
    ]
