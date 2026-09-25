from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Inventory, InventoryTransaction, Product
from products.views import InventoryViewSet


class InventoryLedgerIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="inventory-g", password="pw")
        self.store = Store.objects.create(name="G Store", code="G-01")
        UserStore.objects.create(user=self.user, store=self.store, role="manager")
        category = Category.objects.create(name="G Category", store=self.store)
        self.product = Product.objects.create(
            name="G Product",
            barcode="4234567890121",
            category=category,
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("10"),
            min_quantity=Decimal("2"),
        )
        self.factory = APIRequestFactory()

    def _request(self, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=self.user)
        return request

    def test_direct_inventory_create_is_blocked(self):
        response = InventoryViewSet.as_view({"post": "create"})(
            self._request("post", "/api/products/inventory/", {
                "product": self.product.id,
                "store": self.store.id,
                "quantity": "99",
                "min_quantity": "2",
            })
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Inventory.objects.count(), 1)
        self.assertEqual(Inventory.objects.get(pk=self.inventory.pk).quantity, Decimal("10"))
        self.assertEqual(InventoryTransaction.objects.count(), 0)

    def test_direct_inventory_update_is_blocked(self):
        response = InventoryViewSet.as_view({"patch": "partial_update"})(
            self._request("patch", f"/api/products/inventory/{self.inventory.id}/", {
                "quantity": "99",
            }),
            pk=self.inventory.id,
        )
        self.assertEqual(response.status_code, 405)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, Decimal("10"))
        self.assertEqual(InventoryTransaction.objects.count(), 0)

    def test_direct_inventory_delete_is_blocked(self):
        response = InventoryViewSet.as_view({"delete": "destroy"})(
            self._request("delete", f"/api/products/inventory/{self.inventory.id}/"),
            pk=self.inventory.id,
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())
        self.assertEqual(InventoryTransaction.objects.count(), 0)

    def test_adjustment_is_the_authorized_inventory_mutation_and_creates_ledger(self):
        response = InventoryViewSet.as_view({"post": "adjust"})(
            self._request("post", f"/api/products/inventory/{self.inventory.id}/adjust/", {
                "quantity": "7",
                "description": "G audit adjustment",
            }),
            pk=self.inventory.id,
        )
        self.assertEqual(response.status_code, 200)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, Decimal("7"))
        tx = InventoryTransaction.objects.get()
        self.assertEqual(tx.product_id, self.product.id)
        self.assertEqual(tx.store_id, self.store.id)
        self.assertEqual(tx.transaction_type, InventoryTransaction.TYPE_ADJUSTMENT)
        self.assertEqual(tx.quantity, Decimal("-3"))
