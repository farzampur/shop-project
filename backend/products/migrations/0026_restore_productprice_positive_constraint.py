from django.db import migrations, models


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


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0025_merge_20260918_0006"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=SQL_ADD,
                    reverse_sql="ALTER TABLE products_productprice DROP CONSTRAINT IF EXISTS product_price_amount_gt_zero;",
                ),
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="productprice",
                    constraint=models.CheckConstraint(
                        condition=models.Q(amount__gt=0),
                        name="product_price_amount_gt_zero",
                    ),
                ),
            ],
        ),
    ]
