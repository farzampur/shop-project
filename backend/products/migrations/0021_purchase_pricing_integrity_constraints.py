from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("products", "0020_inventory_transaction_quantity_integrity")]
    operations = [
        migrations.AddConstraint(model_name="purchaseitem", constraint=models.CheckConstraint(condition=models.Q(quantity__gt=0), name="purchase_item_quantity_gt_zero")),
        migrations.AddConstraint(model_name="purchaseitem", constraint=models.CheckConstraint(condition=models.Q(unit_price__gte=0), name="purchase_item_unit_price_gte_zero")),
        migrations.AddConstraint(model_name="purchaseitem", constraint=models.CheckConstraint(condition=models.Q(sale_price__gte=0), name="purchase_item_sale_price_gte_zero")),
        migrations.AddConstraint(model_name="purchaseitem", constraint=models.CheckConstraint(condition=models.Q(total_price__gte=0), name="purchase_item_total_price_gte_zero")),
        migrations.AddConstraint(model_name="productbatch", constraint=models.CheckConstraint(condition=models.Q(purchase_price__gte=0), name="product_batch_purchase_price_gte_zero")),
        migrations.AddConstraint(model_name="productbatch", constraint=models.CheckConstraint(condition=models.Q(sale_price__gte=0), name="product_batch_sale_price_gte_zero")),
        migrations.AddConstraint(model_name="productprice", constraint=models.CheckConstraint(condition=models.Q(amount__gt=0), name="product_price_amount_gt_zero")),
    ]
