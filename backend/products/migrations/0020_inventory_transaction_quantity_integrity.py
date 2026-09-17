from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0019_ledger_integrity_constraints"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="inventorytransaction",
            constraint=models.CheckConstraint(
                condition=~models.Q(quantity=0),
                name="inventory_transaction_quantity_nonzero",
            ),
        ),
    ]
