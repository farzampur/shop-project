from django.db import migrations


SQL_ADD = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'product_price_amount_gt_zero'
          AND conrelid = 'products_productprice'::regclass
    ) THEN
        ALTER TABLE products_productprice
        ADD CONSTRAINT product_price_amount_gt_zero
        CHECK (amount > 0);
    END IF;
END
$$;
"""

SQL_REMOVE = """
ALTER TABLE products_productprice
DROP CONSTRAINT IF EXISTS product_price_amount_gt_zero;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0021_purchase_pricing_integrity_constraints"),
    ]

    operations = [
        migrations.RunSQL(
            sql=SQL_ADD,
            reverse_sql=SQL_REMOVE,
        ),
    ]
