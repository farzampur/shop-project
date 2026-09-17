from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from core.models import Store
from .models import CashBox, CashDayClose


class CashDayCloseIntegrity698Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase698", password="x")
        self.store = Store.objects.create(name="698 Store")
        self.cashbox = CashBox.objects.create(
            store=self.store,
            name="698 Cashbox",
            balance=Decimal("100.00"),
        )

    def make_close(self, **overrides):
        data = {
            "store": self.store,
            "cashbox": self.cashbox,
            "close_date": "2026-01-01",
            "opening_balance": Decimal("100.00"),
            "expected_balance": Decimal("100.00"),
            "counted_balance": Decimal("100.00"),
            "difference": Decimal("0.00"),
            "closed_by": self.user,
        }
        data.update(overrides)
        return CashDayClose.objects.create(**data)

    def assert_db_rejects(self, **overrides):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_close(**overrides)

    def test_opening_balance_cannot_be_negative(self):
        self.assert_db_rejects(opening_balance=Decimal("-0.01"))

    def test_expected_balance_cannot_be_negative(self):
        self.assert_db_rejects(expected_balance=Decimal("-0.01"))

    def test_counted_balance_cannot_be_negative(self):
        self.assert_db_rejects(counted_balance=Decimal("-0.01"))

    def test_difference_must_match_counted_minus_expected(self):
        self.assert_db_rejects(difference=Decimal("1.00"))

    def test_valid_day_close_is_accepted(self):
        obj = self.make_close(
            opening_balance=Decimal("120.00"),
            expected_balance=Decimal("100.00"),
            counted_balance=Decimal("95.00"),
            difference=Decimal("-5.00"),
        )
        self.assertEqual(obj.difference, Decimal("-5.00"))
