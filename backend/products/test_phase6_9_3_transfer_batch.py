from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Category,
    Inventory,
    Product,
    ProductBatch,
    Purchase,
    PurchaseItem,
    StockTransfer,
    StockTransferBatchAllocation,
    Supplier,
)
from products.services import PurchaseService
from products.views import StockTransferViewSet


class Phase693BatchTransferTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="p693-manager", password="pw")
        self.warehouse = User.objects.create_user(username="p693-warehouse", password="pw")
        self.source = Store.objects.create(name="P693 Source", code="P693-S")
        self.dest = Store.objects.create(name="P693 Dest", code="P693-D")
        self.supplier = Supplier.objects.create(
            store=self.source,
            name="P693 Supplier",
        )
        UserStore.objects.create(user=self.user, store=self.source, role="manager")
        UserStore.objects.create(user=self.user, store=self.dest, role="manager")
        UserStore.objects.create(user=self.warehouse, store=self.source, role="warehouse")
        UserStore.objects.create(user=self.warehouse, store=self.dest, role="warehouse")
        self.cat = Category.objects.create(name="P693 Cat", store=self.source)
        self.product = Product.objects.create(
            name="P693 Product",
            barcode="9234567890123",
            category=self.cat,
        )
        self.inventory = Inventory.objects.create(
            product=self.product,
            store=self.source,
            quantity=Decimal("10"),
            min_quantity=Decimal("2"),
        )
        self.factory = APIRequestFactory()

    def _request(self, user, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=user)
        return request

    def _transfer(self, quantity="4"):
        request = self._request(self.user, "post", "/api/products/stock-transfers/", {
            "source_store": self.source.id,
            "destination_store": self.dest.id,
            "items": [{"product": self.product.id, "quantity": quantity}],
        })
        response = StockTransferViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        return StockTransfer.objects.get(pk=response.data["id"])

    def _receive_transfer(self, transfer):
        for action, user in (("approve", self.user), ("ship", self.warehouse), ("receive", self.warehouse)):
            request = self._request(user, "post", f"/api/products/stock-transfers/{transfer.id}/{action}/")
            response = StockTransferViewSet.as_view({"post": action})(request, pk=transfer.id)
            self.assertEqual(response.status_code, 200, response.data)

    def test_transfer_preserves_batch_cost_and_sale_price_at_destination(self):
        purchase = Purchase.objects.create(
            store=self.source,
            supplier=self.supplier,
            received=True,
            user=self.user,
        )
        item = PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=Decimal("10"),
            unit_price=Decimal("50"),
            sale_price=Decimal("80"),
        )
        ProductBatch.objects.create(
            purchase_item=item,
            product=self.product,
            store=self.source,
            quantity=Decimal("10"),
            remaining_quantity=Decimal("10"),
            purchase_price=Decimal("50"),
            sale_price=Decimal("80"),
        )
        transfer = self._transfer("4")
        self._receive_transfer(transfer)

        source_batch = ProductBatch.objects.get(purchase_item=item)
        self.assertEqual(source_batch.remaining_quantity, Decimal("6"))
        allocation = StockTransferBatchAllocation.objects.get(transfer_item__transfer=transfer)
        self.assertEqual(allocation.quantity, Decimal("4"))

        dest_batch = ProductBatch.objects.get(source_batch=source_batch)
        self.assertEqual(dest_batch.store_id, self.dest.id)
        self.assertEqual(dest_batch.quantity, Decimal("4"))
        self.assertEqual(dest_batch.remaining_quantity, Decimal("4"))
        self.assertEqual(dest_batch.purchase_price, Decimal("50"))
        self.assertEqual(dest_batch.sale_price, Decimal("80"))
        self.assertIsNone(dest_batch.purchase_item_id)

    def test_transfer_allocates_fifo_across_source_batches(self):
        first_purchase = Purchase.objects.create(store=self.source, supplier=self.supplier, received=True, user=self.user)
        first_item = PurchaseItem.objects.create(
            purchase=first_purchase, product=self.product, quantity=Decimal("3"),
            unit_price=Decimal("50"), sale_price=Decimal("80"),
        )
        first_batch = ProductBatch.objects.create(
            purchase_item=first_item, product=self.product, store=self.source,
            quantity=Decimal("3"), remaining_quantity=Decimal("3"),
            purchase_price=Decimal("50"), sale_price=Decimal("80"),
        )
        second_purchase = Purchase.objects.create(store=self.source, supplier=self.supplier, received=True , user=self.user)
        second_item = PurchaseItem.objects.create(
            purchase=second_purchase, product=self.product, quantity=Decimal("5"),
            unit_price=Decimal("60"), sale_price=Decimal("95"),
        )
        second_batch = ProductBatch.objects.create(
            purchase_item=second_item, product=self.product, store=self.source,
            quantity=Decimal("5"), remaining_quantity=Decimal("5"),
            purchase_price=Decimal("60"), sale_price=Decimal("95"),
        )
        transfer = self._transfer("6")
        self._receive_transfer(transfer)

        allocations = list(
            StockTransferBatchAllocation.objects
            .filter(transfer_item__transfer=transfer)
            .order_by("source_batch__received_at", "source_batch_id")
        )
        self.assertEqual([(a.source_batch_id, a.quantity) for a in allocations], [
            (first_batch.id, Decimal("3")),
            (second_batch.id, Decimal("3")),
        ])
        self.assertEqual(ProductBatch.objects.get(pk=first_batch.id).remaining_quantity, Decimal("0"))
        self.assertEqual(ProductBatch.objects.get(pk=second_batch.id).remaining_quantity, Decimal("2"))
        self.assertEqual(
            list(ProductBatch.objects.filter(store=self.dest).order_by("purchase_price").values_list("purchase_price", "sale_price", "quantity")),
            [(Decimal("50"), Decimal("80"), Decimal("3")), (Decimal("60"), Decimal("95"), Decimal("3"))],
        )
