from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("sales", "0014_cashdayclose")]
    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="price_type",
            field=models.CharField(
                choices=[("retail", "خرده‌فروشی"), ("wholesale", "عمده‌فروشی"), ("special", "ویژه")],
                default="retail",
                max_length=20,
                verbose_name="نوع قیمت",
            ),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="price_type",
            field=models.CharField(
                choices=[("retail", "خرده‌فروشی"), ("wholesale", "عمده‌فروشی"), ("special", "ویژه")],
                default="retail",
                max_length=20,
                verbose_name="نوع قیمت",
            ),
        ),
    ]
