from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0012_supplier_unique_supplier_name_per_store"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="barcode",
            field=models.CharField(max_length=50, verbose_name="بارکد"),
        ),
    ]
