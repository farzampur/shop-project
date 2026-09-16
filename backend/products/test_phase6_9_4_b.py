from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Product, Purchase, PurchaseItem, Supplier
from products.views import PurchaseItemViewSet


class ReceivedPurchaseItemMutationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase694b", password="pw")
        self.store = Store.objects.create(name="Store 6.9.4 B", code="P694B")
        UserStore.objects.create(
            user=self.user,
            store=self.store,
            role="manager",
            is_active=True,
        )
        category = Category.objects.create(name="Cat 6.9.4 B", store=self.store)
        self.product = Product.objects.create(
            name="Product 6.9.4 B",
            barcode="6940001",
            category=category,
            purchase_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        supplier = Supplier.objects.create(name="Supplier 6.9.4 B", store=self.store)
        self.purchase = Purchase.objects.create(
            supplier=supplier,
            store=self.store,
            user=self.user,
            received=True,
        )
        self.item = PurchaseItem.objects.create(
            purchase=self.purchase,
            product=self.product,
            quantity=Decimal("5"),
            unit_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        self.factory = APIRequestFactory()

    def _request(self, method, data=None):
        request = getattr(self.factory, method)(
            f"/api/products/purchases/{self.purchase.id}/items/",
            data=data or {},
            format="json",
        )
        force_authenticate(request, user=self.user)
        request.user = self.user
        request.query_params = request.GET
        return request

    def test_cannot_add_item_to_received_purchase(self):
        request = self._request(
            "post",
            {
                "product": self.product.id,
                "quantity": "2",
                "unit_price": "50",
                "sale_price": "100",
            },
        )
        response = PurchaseItemViewSet.as_view({"post": "create"})(
            request,
            purchase_pk=self.purchase.id,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self.purchase.items.count(), 1)

    def test_cannot_edit_item_of_received_purchase(self):
        request = self._request(
            "patch",
            {"quantity": "9"},
        )
        response = PurchaseItemViewSet.as_view({"patch": "partial_update"})(
            request,
            purchase_pk=self.purchase.id,
            pk=self.item.id,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("5"))

    def test_cannot_delete_item_of_received_purchase(self):
        request = self._request("delete")
        response = PurchaseItemViewSet.as_view({"delete": "destroy"})(
            request,
            purchase_pk=self.purchase.id,
            pk=self.item.id,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(PurchaseItem.objects.filter(pk=self.item.id).exists())
