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
    Supplier,
    SupplierTransaction,
)
from products.views import PurchaseViewSet


class PurchaseReceivedIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase694d", password="pw")
        self.store = Store.objects.create(name="Store 6.9.4 D", code="P694D")
        UserStore.objects.create(
            user=self.user,
            store=self.store,
            role="manager",
            is_active=True,
        )
        category = Category.objects.create(name="Cat 6.9.4 D", store=self.store)
        self.product = Product.objects.create(
            name="Product 6.9.4 D",
            barcode="6940003",
            category=category,
        )
        self.supplier = Supplier.objects.create(
            name="Supplier 6.9.4 D",
            store=self.store,
        )
        self.purchase = Purchase.objects.create(
            supplier=self.supplier,
            store=self.store,
            user=self.user,
            received=False,
        )
        self.item = PurchaseItem.objects.create(
            purchase=self.purchase,
            product=self.product,
            quantity=Decimal("5"),
            unit_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        self.factory = APIRequestFactory()

    def _request(self, method, data):
        request = getattr(self.factory, method)(
            f"/api/products/purchases/{self.purchase.id}/",
            data=data,
            format="json",
        )
        force_authenticate(request, user=self.user)
        request.user = self.user
        request.query_params = request.GET
        return request

    def test_normal_update_cannot_mark_purchase_received(self):
        response = PurchaseViewSet.as_view({"patch": "partial_update"})(
            self._request("patch", {"received": True}),
            pk=self.purchase.id,
        )

        self.assertEqual(response.status_code, 400, response.data)

        self.purchase.refresh_from_db()
        self.assertFalse(self.purchase.received)

        self.assertFalse(
            Inventory.objects.filter(
                product=self.product,
                store=self.store,
            ).exists()
        )
        self.assertFalse(
            ProductBatch.objects.filter(
                purchase_item=self.item,
            ).exists()
        )
        self.assertFalse(
            InventoryTransaction.objects.filter(
                transaction_type=InventoryTransaction.TYPE_PURCHASE,
                reference_id=self.purchase.id,
            ).exists()
        )
        self.assertFalse(
            SupplierTransaction.objects.filter(
                transaction_type="purchase",
                reference_id=self.purchase.id,
            ).exists()
        )

    def test_receive_endpoint_is_the_only_transition_to_received(self):
        response = PurchaseViewSet.as_view({"post": "receive_purchase"})(
            self._request("post", {}),
            pk=self.purchase.id,
        )

        self.assertEqual(response.status_code, 200, response.data)

        self.purchase.refresh_from_db()
        self.assertTrue(self.purchase.received)

        inventory = Inventory.objects.get(
            product=self.product,
            store=self.store,
        )
        self.assertEqual(inventory.quantity, Decimal("5"))

        batch = ProductBatch.objects.get(purchase_item=self.item)
        self.assertEqual(batch.quantity, Decimal("5"))
        self.assertEqual(batch.remaining_quantity, Decimal("5"))

        self.assertEqual(
            InventoryTransaction.objects.filter(
                transaction_type=InventoryTransaction.TYPE_PURCHASE,
                reference_id=self.purchase.id,
            ).count(),
            1,
        )
        self.assertEqual(
            SupplierTransaction.objects.filter(
                transaction_type="purchase",
                reference_id=self.purchase.id,
            ).count(),
            1,
        )
