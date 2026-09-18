from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0025_merge_20260918_0006"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="productprice",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="product_price_amount_gt_zero",
            ),
        ),
    ]
