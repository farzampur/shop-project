from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Supplier,
    SupplierTransaction,
)


class CrossStoreSupplierReportTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="phase692-user",
            password="password",
        )

        self.store_a = Store.objects.create(
            name="Store 6.9.2 A",
            code="P692-A",
        )

        self.store_b = Store.objects.create(
            name="Store 6.9.2 B",
            code="P692-B",
        )

        UserStore.objects.create(
            user=self.user,
            store=self.store_a,
            role="manager",
            is_active=True,
        )

        self.supplier_a = Supplier.objects.create(
            store=self.store_a,
            name="Supplier A 6.9.2",
        )

        self.supplier_b = Supplier.objects.create(
            store=self.store_b,
            name="Supplier B 6.9.2",
        )

        SupplierTransaction.objects.create(
            supplier=self.supplier_a,
            transaction_type="purchase",
            amount=Decimal("1000.00"),
        )

        SupplierTransaction.objects.create(
            supplier=self.supplier_b,
            transaction_type="purchase",
            amount=Decimal("9000.00"),
        )

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _assert_only_store_a_supplier(self, response):
        self.assertEqual(response.status_code, 200, response.data)

        items = response.data["items"] if isinstance(
            response.data,
            dict
        ) else response.data

        supplier_ids = {
            item["supplier_id"]
            for item in items
        }

        self.assertIn(
            self.supplier_a.id,
            supplier_ids,
        )

        self.assertNotIn(
            self.supplier_b.id,
            supplier_ids,
        )

    def test_debtor_report_is_store_isolated(self):
        response = self.client.get(
            "/api/products/suppliers/debtors/"
        )

        self._assert_only_store_a_supplier(response)

    def test_balance_report_is_store_isolated(self):
        response = self.client.get(
            "/api/products/suppliers/balance-report/"
        )

        self._assert_only_store_a_supplier(response)

    def test_comprehensive_report_is_store_isolated(self):
        response = self.client.get(
            "/api/products/suppliers/comprehensive-report/"
        )

        self._assert_only_store_a_supplier(response)

    def test_inventory_ledger_is_store_isolated(self):
        from products.models import (
            Category,
            Product,
            Inventory,
            InventoryTransaction,
        )

        category = Category.objects.create(
            store=self.store_a,
            name="Category 6.9.2",
        )

        product = Product.objects.create(
            category=category,
            name="Product 6.9.2",
            barcode="6920001",
            purchase_price=Decimal("100"),
            sale_price=Decimal("150"),
        )

        Inventory.objects.create(
            product=product,
            store=self.store_a,
            quantity=Decimal("10"),
        )

        Inventory.objects.create(
            product=product,
            store=self.store_b,
            quantity=Decimal("20"),
        )

        InventoryTransaction.objects.create(
            product=product,
            store=self.store_a,
            transaction_type="purchase",
            quantity=Decimal("10"),
        )

        InventoryTransaction.objects.create(
            product=product,
            store=self.store_b,
            transaction_type="purchase",
            quantity=Decimal("20"),
        )

        response = self.client.get(
            f"/api/products/inventory-ledger/{product.id}/"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        store_ids = {
            item["store_id"]
            for item in response.data
        }

        self.assertEqual(
            store_ids,
            {self.store_a.id},
        )