from django.db import migrations, models
from django.db.models import F


class Migration(migrations.Migration):
    dependencies = [("products", "0022_document_integrity_constraints")]

    operations = [
        migrations.AddConstraint(
            model_name="inventory",
            constraint=models.CheckConstraint(
                condition=models.Q(min_quantity__gte=0),
                name="inventory_min_quantity_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="productprice",
            constraint=models.CheckConstraint(
                condition=models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=F("effective_from")),
                name="product_price_effective_end_after_start",
            ),
        ),
    ]
