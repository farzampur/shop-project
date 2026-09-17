from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("sales", "0020_cashdayclose_integrity_constraints")]
    operations = [
        migrations.AddConstraint(model_name="cartitem", constraint=models.CheckConstraint(condition=models.Q(quantity__gt=0), name="cart_item_quantity_gt_zero")),
        migrations.AddConstraint(model_name="cartitem", constraint=models.CheckConstraint(condition=models.Q(unit_price__gte=0), name="cart_item_unit_price_gte_zero")),
        migrations.AddConstraint(model_name="cartitem", constraint=models.CheckConstraint(condition=models.Q(discount_percent__gte=0), name="cart_item_discount_percent_gte_zero")),
        migrations.AddConstraint(model_name="cartitem", constraint=models.CheckConstraint(condition=models.Q(discount_percent__lte=100), name="cart_item_discount_percent_lte_100")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(quantity__gt=0), name="order_item_quantity_gt_zero")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(unit_price__gte=0), name="order_item_unit_price_gte_zero")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(purchase_price__gte=0), name="order_item_purchase_price_gte_zero")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(discount_percent__gte=0), name="order_item_discount_percent_gte_zero")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(discount_percent__lte=100), name="order_item_discount_percent_lte_100")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(discount_amount__gte=0), name="order_item_discount_amount_gte_zero")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(total_price_before_discount__gte=0), name="order_item_total_before_discount_gte_zero")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(total_discount_amount__gte=0), name="order_item_total_discount_gte_zero")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.CheckConstraint(condition=models.Q(total_price__gte=0), name="order_item_total_price_gte_zero")),
    ]
