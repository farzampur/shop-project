from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("sales", "0018_cashboxtransaction_reference_type")]

    operations = [
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payment_amount_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="expense",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="expense_amount_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="customertransaction",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="customer_transaction_amount_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="cashbox",
            constraint=models.CheckConstraint(
                condition=models.Q(balance__gte=0),
                name="cashbox_balance_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="cashboxtransaction",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="cashbox_transaction_amount_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="cashtransfer",
            constraint=models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="cash_transfer_amount_gt_zero",
            ),
        ),
    ]
