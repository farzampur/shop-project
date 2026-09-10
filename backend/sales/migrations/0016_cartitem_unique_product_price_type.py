from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0015_cartitem_orderitem_price_type"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="cartitem",
            name="unique_cart_product",
        ),
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=("cart", "product", "price_type"),
                name="unique_cart_product_price_type",
            ),
        ),
    ]
