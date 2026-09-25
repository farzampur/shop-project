from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from .models import Product, Category, Inventory, StockTransfer
from .views import StockTransferViewSet


class BusinessLogicIntegrityAudit695Tests(TestCase):
    def setUp(self):
        self.store_a = Store.objects.create(name="695 A", code="695-A")
        self.store_b = Store.objects.create(name="695 B", code="695-B")
        self.store_c = Store.objects.create(name="695 C", code="695-C")
        self.user = User.objects.create_user(username="audit695", password="test123")
        for store in (self.store_a, self.store_b):
            UserStore.objects.create(user=self.user, store=store, role="manager", is_active=True)

        category = Category.objects.create(store=self.store_a, name="695 Category")
        self.product = Product.objects.create(category=category, name="695 Product")
        Inventory.objects.create(product=self.product, store=self.store_a, quantity=Decimal("10"), min_quantity=0)
        self.factory = APIRequestFactory()

    def _request(self, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data or {}, format="json")
        force_authenticate(request, user=self.user)
        return request

    def _create_transfer(self):
        request = self._request("post", "/api/products/stock-transfers/", {
            "source_store": self.store_a.id,
            "destination_store": self.store_b.id,
            "notes": "draft",
            "items": [{"product": self.product.id, "quantity": "2"}],
        })
        response = StockTransferViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201, response.data)
        return StockTransfer.objects.get(pk=response.data["id"])

    def test_approved_transfer_cannot_be_edited(self):
        transfer = self._create_transfer()
        request = self._request("post", f"/api/products/stock-transfers/{transfer.id}/approve/")
        response = StockTransferViewSet.as_view({"post": "approve"})(request, pk=transfer.id)
        self.assertEqual(response.status_code, 200, response.data)

        request = self._request("patch", f"/api/products/stock-transfers/{transfer.id}/", {"notes": "tampered"})
        response = StockTransferViewSet.as_view({"patch": "partial_update"})(request, pk=transfer.id)
        self.assertEqual(response.status_code, 400, response.data)
        transfer.refresh_from_db()
        self.assertEqual(transfer.notes, "draft")

    def test_shipped_transfer_cannot_be_deleted(self):
        transfer = self._create_transfer()
        for action in ("approve", "ship"):
            request = self._request("post", f"/api/products/stock-transfers/{transfer.id}/{action}/")
            response = StockTransferViewSet.as_view({"post": action})(request, pk=transfer.id)
            self.assertEqual(response.status_code, 200, response.data)

        request = self._request("delete", f"/api/products/stock-transfers/{transfer.id}/")
        response = StockTransferViewSet.as_view({"delete": "destroy"})(request, pk=transfer.id)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(StockTransfer.objects.filter(pk=transfer.id).exists())

    def test_draft_transfer_cannot_change_source_after_items_exist(self):
        transfer = self._create_transfer()
        request = self._request("patch", f"/api/products/stock-transfers/{transfer.id}/", {
            "source_store": self.store_b.id,
        })
        response = StockTransferViewSet.as_view({"patch": "partial_update"})(request, pk=transfer.id)
        self.assertEqual(response.status_code, 400, response.data)
        transfer.refresh_from_db()
        self.assertEqual(transfer.source_store_id, self.store_a.id)

    def test_draft_transfer_can_be_deleted_by_source_manager(self):
        transfer = self._create_transfer()
        request = self._request("delete", f"/api/products/stock-transfers/{transfer.id}/")
        response = StockTransferViewSet.as_view({"delete": "destroy"})(request, pk=transfer.id)
        self.assertEqual(response.status_code, 204, response.data)
        self.assertFalse(StockTransfer.objects.filter(pk=transfer.id).exists())
