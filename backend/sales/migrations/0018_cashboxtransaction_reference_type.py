from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0017_orderitembatch"),
    ]

    operations = [
        migrations.AddField(
            model_name="cashboxtransaction",
            name="reference_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("manual", "تعدیل دستی"),
                    ("order", "سفارش/فروش"),
                    ("expense", "هزینه"),
                    ("customer_transaction", "تراکنش مشتری"),
                    ("supplier_transaction", "تراکنش تأمین‌کننده"),
                    ("cash_transfer", "انتقال صندوق"),
                ],
                max_length=30,
                null=True,
            ),
        ),
    ]
