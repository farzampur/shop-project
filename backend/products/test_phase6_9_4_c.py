from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Category,
    Inventory,
    InventoryTransaction,
    Product,
    ProductBatch,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    Supplier,
    SupplierTransaction,
)
from products.views import PurchaseReturnViewSet


class PurchaseReturnMutationIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase694c", password="pw")
        self.store = Store.objects.create(name="Store 6.9.4 C", code="P694C")
        UserStore.objects.create(
            user=self.user,
            store=self.store,
            role="manager",
            is_active=True,
        )
        category = Category.objects.create(name="Cat 6.9.4 C", store=self.store)
        self.product = Product.objects.create(
            name="Product 6.9.4 C",
            barcode="6940002",
            category=category,
            purchase_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        self.supplier = Supplier.objects.create(
            name="Supplier 6.9.4 C",
            store=self.store,
        )
        self.purchase = Purchase.objects.create(
            supplier=self.supplier,
            store=self.store,
            user=self.user,
            received=True,
        )
        self.item = PurchaseItem.objects.create(
            purchase=self.purchase,
            product=self.product,
            quantity=Decimal("10"),
            unit_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("10"),
        )
        self.batch = ProductBatch.objects.create(
            purchase_item=self.item,
            product=self.product,
            store=self.store,
            quantity=Decimal("10"),
            remaining_quantity=Decimal("10"),
            purchase_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        self.factory = APIRequestFactory()

        request = self.factory.post(
            "/api/products/purchase-returns/",
            {
                "purchase": self.purchase.id,
                "product": self.product.id,
                "quantity": "2",
                "unit_price": "50",
                "description": "return integrity",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        request.user = self.user
        request.query_params = request.GET
        response = PurchaseReturnViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201, getattr(response, "data", None))
        self.return_id = response.data["id"]

    def _request(self, method, data=None):
        request = getattr(self.factory, method)(
            f"/api/products/purchase-returns/{self.return_id}/",
            data=data or {},
            format="json",
        )
        force_authenticate(request, user=self.user)
        request.user = self.user
        request.query_params = request.GET
        return request

    def _snapshot(self):
        self.inventory.refresh_from_db()
        self.batch.refresh_from_db()
        return {
            "inventory": self.inventory.quantity,
            "batch": self.batch.remaining_quantity,
            "inventory_tx": InventoryTransaction.objects.filter(
                reference_id=self.return_id,
                transaction_type=InventoryTransaction.TYPE_RETURN,
            ).count(),
            "supplier_tx": SupplierTransaction.objects.filter(
                reference_id=self.return_id,
                transaction_type="return",
            ).count(),
            "return_exists": PurchaseReturn.objects.filter(pk=self.return_id).exists(),
            "return_qty": PurchaseReturn.objects.get(pk=self.return_id).quantity,
        }

    def test_cannot_edit_registered_purchase_return(self):
        before = self._snapshot()
        response = PurchaseReturnViewSet.as_view({"patch": "partial_update"})(
            self._request("patch", {"quantity": "1"}),
            pk=self.return_id,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self._snapshot(), before)

    def test_cannot_delete_registered_purchase_return(self):
        before = self._snapshot()
        response = PurchaseReturnViewSet.as_view({"delete": "destroy"})(
            self._request("delete"),
            pk=self.return_id,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self._snapshot(), before)
