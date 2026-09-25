from django.db import migrations


def forwards_migrate_legacy_prices(apps, schema_editor):
    """Preserve legacy Product pricing for existing unbatched stock.

    New sales valuation is batch-controlled. When an old product still has
    positive stock but no batch, carry its legacy prices into one synthetic
    opening batch so the migration does not silently discard usable pricing.
    Products that are already batch-valued are left untouched. Unpriced legacy
    stock (zero legacy sale price) is intentionally left without a batch and is
    therefore visible as unvalued stock until a real batch is introduced.
    """
    Product = apps.get_model("products", "Product")
    Inventory = apps.get_model("products", "Inventory")
    ProductBatch = apps.get_model("products", "ProductBatch")

    for inventory in Inventory.objects.select_related("product").filter(quantity__gt=0).iterator():
        product = inventory.product
        if ProductBatch.objects.filter(product_id=product.id, store_id=inventory.store_id).exists():
            continue
        legacy_sale = product.sale_price
        legacy_purchase = product.purchase_price
        if legacy_sale is None or legacy_sale <= 0:
            continue

        ProductBatch.objects.create(
            purchase_item=None,
            source_batch=None,
            product_id=product.id,
            store_id=inventory.store_id,
            quantity=inventory.quantity,
            remaining_quantity=inventory.quantity,
            purchase_price=legacy_purchase or 0,
            sale_price=legacy_sale,
            received_at=product.created_at,
        )


def backwards_restore_legacy_prices(apps, schema_editor):
    """Best-effort restore of Product prices from the oldest remaining batch."""
    Product = apps.get_model("products", "Product")
    ProductBatch = apps.get_model("products", "ProductBatch")

    for product in Product.objects.all().iterator():
        batch = (ProductBatch.objects
                 .filter(product_id=product.id, remaining_quantity__gt=0)
                 .order_by("received_at", "id")
                 .first())
        if batch is None:
            continue
        product.purchase_price = batch.purchase_price
        product.sale_price = batch.sale_price
        product.save(update_fields=["purchase_price", "sale_price"])


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0026_restore_productprice_positive_constraint"),
    ]

    operations = [
        migrations.RunPython(
            forwards_migrate_legacy_prices,
            backwards_restore_legacy_prices,
        ),
        migrations.RemoveField(
            model_name="product",
            name="purchase_price",
        ),
        migrations.RemoveField(
            model_name="product",
            name="sale_price",
        ),
    ]
