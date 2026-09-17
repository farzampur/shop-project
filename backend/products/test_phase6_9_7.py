from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from core.models import Store
from .models import InventoryTransaction, Product


class InventoryTransactionIntegrity697Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="697 Store", code="697-S")
        self.product = Product.objects.create(
            name="697 Product",
            barcode="697-BAR",
            category=self._category(),
            purchase_price=Decimal("10"),
        )

    def _category(self):
        from .models import Category
        return Category.objects.create(name="697 Category", store=self.store)

    def _violates(self, fn):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                fn()

    def test_zero_quantity_rejected(self):
        self._violates(lambda: InventoryTransaction.objects.create(
            product=self.product, store=self.store,
            transaction_type=InventoryTransaction.TYPE_SALE,
            quantity=Decimal("0"),
        ))

    def test_negative_quantity_allowed_for_transfer_out(self):
        tx = InventoryTransaction.objects.create(
            product=self.product, store=self.store,
            transaction_type=InventoryTransaction.TYPE_TRANSFER_OUT,
            quantity=Decimal("-2"),
        )
        self.assertEqual(tx.quantity, Decimal("-2"))

    def test_positive_quantity_allowed_for_adjustment(self):
        tx = InventoryTransaction.objects.create(
            product=self.product, store=self.store,
            transaction_type=InventoryTransaction.TYPE_ADJUSTMENT,
            quantity=Decimal("2"),
        )
        self.assertEqual(tx.quantity, Decimal("2"))
