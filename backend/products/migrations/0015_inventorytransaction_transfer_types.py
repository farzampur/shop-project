from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0014_stocktransfer_productprice"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventorytransaction",
            name="transaction_type",
            field=models.CharField(
                choices=[
                    ("purchase", "Purchase"),
                    ("sale", "Sale"),
                    ("return", "Return"),
                    ("adjustment", "Adjustment"),
                    ("transfer_out", "Transfer Out"),
                    ("transfer_in", "Transfer In"),
                ],
                max_length=20,
            ),
        ),
    ]
