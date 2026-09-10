from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Inventory, InventoryTransaction, Product, StockTransfer
from products.views import StockTransferViewSet


class StockTransferPhase65Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="p65-manager", password="pw")
        self.warehouse = User.objects.create_user(username="p65-warehouse", password="pw")
        self.other = User.objects.create_user(username="p65-other", password="pw")
        self.source = Store.objects.create(name="P65 Source", code="P65-S")
        self.dest = Store.objects.create(name="P65 Dest", code="P65-D")
        UserStore.objects.create(user=self.user, store=self.source, role="manager")
        UserStore.objects.create(user=self.user, store=self.dest, role="manager")
        UserStore.objects.create(user=self.warehouse, store=self.source, role="warehouse")
        UserStore.objects.create(user=self.warehouse, store=self.dest, role="warehouse")
        self.cat = Category.objects.create(name="P65 Cat", store=self.source)
        self.product = Product.objects.create(
            name="P65 Product", barcode="8234567890120", category=self.cat,
            purchase_price=Decimal("50"), sale_price=Decimal("100"),
        )
        self.inventory = Inventory.objects.create(
            product=self.product, store=self.source, quantity=Decimal("10"), min_quantity=Decimal("2")
        )
        self.factory = APIRequestFactory()

    def _request(self, user, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=user)
        return request

    def _create(self):
        request = self._request(self.user, "post", "/api/products/stock-transfers/", {
            "source_store": self.source.id,
            "destination_store": self.dest.id,
            "notes": "phase 6.5",
            "items": [{"product": self.product.id, "quantity": "3"}],
        })
        response = StockTransferViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        return StockTransfer.objects.get(pk=response.data["id"])

    def test_transfer_lifecycle_moves_stock_and_records_distinct_transactions(self):
        transfer = self._create()
        self.assertEqual(transfer.status, StockTransfer.STATUS_DRAFT)
        req = self._request(self.user, "post", f"/api/products/stock-transfers/{transfer.id}/approve/")
        self.assertEqual(StockTransferViewSet.as_view({"post": "approve"})(req, pk=transfer.id).status_code, 200)
        req = self._request(self.warehouse, "post", f"/api/products/stock-transfers/{transfer.id}/ship/")
        self.assertEqual(StockTransferViewSet.as_view({"post": "ship"})(req, pk=transfer.id).status_code, 200)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, Decimal("7"))
        self.assertTrue(InventoryTransaction.objects.filter(
            product=self.product, store=self.source,
            transaction_type=InventoryTransaction.TYPE_TRANSFER_OUT,
            quantity=Decimal("-3"), reference_id=transfer.id,
        ).exists())
        req = self._request(self.warehouse, "post", f"/api/products/stock-transfers/{transfer.id}/receive/")
        self.assertEqual(StockTransferViewSet.as_view({"post": "receive"})(req, pk=transfer.id).status_code, 200)
        dest_inventory = Inventory.objects.get(product=self.product, store=self.dest)
        self.assertEqual(dest_inventory.quantity, Decimal("3"))
        self.assertTrue(InventoryTransaction.objects.filter(
            product=self.product, store=self.dest,
            transaction_type=InventoryTransaction.TYPE_TRANSFER_IN,
            quantity=Decimal("3"), reference_id=transfer.id,
        ).exists())

    def test_duplicate_product_in_one_transfer_is_rejected(self):
        request = self._request(self.user, "post", "/api/products/stock-transfers/", {
            "source_store": self.source.id,
            "destination_store": self.dest.id,
            "items": [
                {"product": self.product.id, "quantity": "1"},
                {"product": self.product.id, "quantity": "2"},
            ],
        })
        response = StockTransferViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(StockTransfer.objects.filter(source_store=self.source, destination_store=self.dest).exists())

    def test_received_transfer_cannot_be_received_twice(self):
        transfer = self._create()
        for action, user in (("approve", self.user), ("ship", self.warehouse), ("receive", self.warehouse)):
            req = self._request(user, "post", f"/api/products/stock-transfers/{transfer.id}/{action}/")
            self.assertEqual(StockTransferViewSet.as_view({"post": action})(req, pk=transfer.id).status_code, 200)
        req = self._request(self.warehouse, "post", f"/api/products/stock-transfers/{transfer.id}/receive/")
        response = StockTransferViewSet.as_view({"post": "receive"})(req, pk=transfer.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.dest).quantity, Decimal("3"))

    def test_source_cannot_cancel_after_shipping(self):
        transfer = self._create()
        req = self._request(self.user, "post", f"/api/products/stock-transfers/{transfer.id}/approve/")
        StockTransferViewSet.as_view({"post": "approve"})(req, pk=transfer.id)
        req = self._request(self.warehouse, "post", f"/api/products/stock-transfers/{transfer.id}/ship/")
        StockTransferViewSet.as_view({"post": "ship"})(req, pk=transfer.id)
        req = self._request(self.user, "post", f"/api/products/stock-transfers/{transfer.id}/cancel/")
        response = StockTransferViewSet.as_view({"post": "cancel"})(req, pk=transfer.id)
        self.assertEqual(response.status_code, 400)
