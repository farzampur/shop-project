from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import UserStore
from core.models import Store
from .models import Inventory, Product, Category, Supplier, SupplierTransaction


class ProductLedgerDatabaseIntegrity696Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="696 Products", code="696-P")
        self.user = User.objects.create_user(username="audit696p", password="pw")
        UserStore.objects.create(user=self.user, store=self.store, role="manager", is_active=True)
        category = Category.objects.create(store=self.store, name="696 Category")
        self.product = Product.objects.create(category=category, name="696 Product", purchase_price=Decimal("10"), sale_price=Decimal("20"))
        self.supplier = Supplier.objects.create(store=self.store, name="696 Supplier")

    def _violates(self, create):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create()

    def test_inventory_cannot_be_negative(self):
        self._violates(lambda: Inventory.objects.create(product=self.product, store=self.store, quantity=Decimal("-1")))

    def test_supplier_transaction_amount_must_be_positive(self):
        self._violates(lambda: SupplierTransaction.objects.create(supplier=self.supplier, transaction_type="adjustment", amount=Decimal("0")))
