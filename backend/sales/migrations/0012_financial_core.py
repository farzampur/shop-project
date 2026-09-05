from django.db import migrations, models
import django.db.models.deletion


def backfill_order_item_purchase_price(apps, schema_editor):
    OrderItem = apps.get_model("sales", "OrderItem")
    for item in OrderItem.objects.select_related("product").all().iterator():
        item.purchase_price = item.product.purchase_price
        item.save(update_fields=["purchase_price"])


def backfill_customer_transaction_store(apps, schema_editor):
    CustomerTransaction = apps.get_model("sales", "CustomerTransaction")
    for tx in CustomerTransaction.objects.select_related("customer").all().iterator():
        tx.store_id = tx.customer.store_id
        tx.save(update_fields=["store"])


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0011_cashtransfer"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="purchase_price",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name="قیمت خرید هنگام فروش"),
        ),
        migrations.RunPython(backfill_order_item_purchase_price, migrations.RunPython.noop),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("method", models.CharField(choices=[("cash", "نقدی"), ("card", "کارتخوان"), ("credit", "حسابی")], max_length=10)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=15)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("cashbox", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="sales.cashbox")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="sales.order")),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AlterField(
            model_name="customer",
            name="mobile",
            field=models.CharField(max_length=20),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(fields=("store", "mobile"), name="unique_customer_mobile_per_store"),
        ),
        migrations.AddField(
            model_name="customertransaction",
            name="store",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="customer_transactions", to="core.store"),
        ),
        migrations.RunPython(backfill_customer_transaction_store, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="customertransaction",
            name="store",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="customer_transactions", to="core.store"),
        ),
    ]
