from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("sales", "0021_sales_line_integrity_constraints")]

    operations = [
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=models.Q(total_before_discount__gte=0),
                name="order_total_before_discount_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=models.Q(total_discount__gte=0),
                name="order_total_discount_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="order",
            constraint=models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name="order_total_price_gte_zero",
            ),
        ),
    ]
