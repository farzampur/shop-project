from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("products", "0018_batch_integrity_constraints")]

    operations = [
        migrations.AddConstraint(
            model_name="inventory",
            constraint=models.CheckConstraint(
                condition=models.Q(quantity__gte=0),
                name="inventory_quantity_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="suppliertransaction",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="supplier_transaction_amount_gt_zero",
            ),
        ),
    ]
