from django.db import migrations, models
from django.db.models import F


class Migration(migrations.Migration):
    dependencies = [("sales", "0019_financial_amount_integrity_constraints")]

    operations = [
        migrations.AddConstraint(
            model_name="cashdayclose",
            constraint=models.CheckConstraint(
                condition=models.Q(opening_balance__gte=0),
                name="cashdayclose_opening_balance_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="cashdayclose",
            constraint=models.CheckConstraint(
                condition=models.Q(expected_balance__gte=0),
                name="cashdayclose_expected_balance_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="cashdayclose",
            constraint=models.CheckConstraint(
                condition=models.Q(counted_balance__gte=0),
                name="cashdayclose_counted_balance_gte_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="cashdayclose",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    difference=F("counted_balance") - F("expected_balance")
                ),
                name="cashdayclose_difference_matches_balances",
            ),
        ),
    ]
