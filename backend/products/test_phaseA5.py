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
    StockTransfer,
    StockTransferBatchAllocation,
    Supplier,
)
from products.views import InventoryReportViewSet, StockTransferViewSet


class PhaseA5TransferReportsE2ETests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a5-manager", password="pw")
        self.warehouse = User.objects.create_user(username="a5-warehouse", password="pw")
        self.other = User.objects.create_user(username="a5-other", password="pw")
        self.source = Store.objects.create(name="A5 Source", code="A5-S")
        self.dest = Store.objects.create(name="A5 Dest", code="A5-D")
        self.other_store = Store.objects.create(name="A5 Other", code="A5-O")
        UserStore.objects.create(user=self.user, store=self.source, role="manager")
        UserStore.objects.create(user=self.user, store=self.dest, role="manager")
        UserStore.objects.create(user=self.warehouse, store=self.source, role="warehouse")
        UserStore.objects.create(user=self.warehouse, store=self.dest, role="warehouse")
        UserStore.objects.create(user=self.other, store=self.other_store, role="warehouse")
        self.supplier = Supplier.objects.create(store=self.source, name="A5 Supplier")
        self.category = Category.objects.create(name="A5 Category", store=self.source)
        self.product = Product.objects.create(
            name="A5 Product", barcode="A5000000001", category=self.category,
        )
        Inventory.objects.create(product=self.product, store=self.source, quantity=Decimal("10"), min_quantity=Decimal("2"))
        self.factory = APIRequestFactory()

    def _request(self, user, method, path, data=None, query=None):
        if query:
            path = f"{path}?{query}"
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=user)
        return request

    def _create_batch(self, quantity, purchase_price, sale_price):
        purchase = Purchase.objects.create(
            store=self.source, supplier=self.supplier, received=True, user=self.user
        )
        item = PurchaseItem.objects.create(
            purchase=purchase, product=self.product, quantity=quantity,
            unit_price=purchase_price, sale_price=sale_price,
        )
        return ProductBatch.objects.create(
            purchase_item=item, product=self.product, store=self.source,
            quantity=quantity, remaining_quantity=quantity,
            purchase_price=purchase_price, sale_price=sale_price,
        )

    def _create_transfer(self, quantity):
        request = self._request(self.user, "post", "/api/products/stock-transfers/", {
            "source_store": self.source.id,
            "destination_store": self.dest.id,
            "items": [{"product": self.product.id, "quantity": str(quantity)}],
        })
        response = StockTransferViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201, response.data)
        return StockTransfer.objects.get(pk=response.data["id"])

    def _receive(self, transfer):
        for action, user in (("approve", self.user), ("ship", self.warehouse), ("receive", self.warehouse)):
            request = self._request(user, "post", f"/api/products/stock-transfers/{transfer.id}/{action}/")
            response = StockTransferViewSet.as_view({"post": action})(request, pk=transfer.id)
            self.assertEqual(response.status_code, 200, response.data)

    def test_transfer_fifo_updates_source_destination_and_ledger(self):
        first = self._create_batch(Decimal("3"), Decimal("50"), Decimal("80"))
        second = self._create_batch(Decimal("5"), Decimal("60"), Decimal("95"))
        transfer = self._create_transfer(Decimal("6"))
        self._receive(transfer)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.remaining_quantity, Decimal("0"))
        self.assertEqual(second.remaining_quantity, Decimal("2"))
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.source).quantity, Decimal("4"))
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.dest).quantity, Decimal("6"))

        allocations = list(
            StockTransferBatchAllocation.objects.filter(transfer_item__transfer=transfer)
            .order_by("source_batch__received_at", "source_batch_id")
        )
        self.assertEqual([(a.source_batch_id, a.quantity) for a in allocations], [
            (first.id, Decimal("3")), (second.id, Decimal("3"))
        ])
        self.assertEqual(
            list(ProductBatch.objects.filter(store=self.dest).order_by("purchase_price").values_list("purchase_price", "sale_price", "quantity")),
            [(Decimal("50"), Decimal("80"), Decimal("3")), (Decimal("60"), Decimal("95"), Decimal("3"))],
        )
        self.assertEqual(
            list(InventoryTransaction.objects.filter(reference_id=transfer.id).order_by("transaction_type").values_list("store_id", "transaction_type", "quantity")),
            [(self.dest.id, "transfer_in", Decimal("6")), (self.source.id, "transfer_out", Decimal("-6"))],
        )

    def test_inventory_report_after_transfer_reflects_destination_stock(self):
        self._create_batch(Decimal("5"), Decimal("50"), Decimal("80"))
        transfer = self._create_transfer(Decimal("4"))
        self._receive(transfer)

        request = self._request(self.user, "get", "/api/products/inventory-report/", query=f"store={self.dest.id}")
        response = InventoryReportViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(Decimal(str(response.data[0]["quantity"])), Decimal("4"))

    def test_inventory_report_cannot_expose_unrelated_store(self):
        request = self._request(self.other, "get", "/api/products/inventory-report/", query=f"store={self.source.id}")
        response = InventoryReportViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, [])

    def test_end_to_end_transfer_preserves_batch_prices_and_inventory_totals(self):
        batch = self._create_batch(Decimal("10"), Decimal("70"), Decimal("110"))
        transfer = self._create_transfer(Decimal("4"))
        self._receive(transfer)

        destination_batch = ProductBatch.objects.get(source_batch=batch)
        self.assertEqual(destination_batch.purchase_price, Decimal("70"))
        self.assertEqual(destination_batch.sale_price, Decimal("110"))
        self.assertEqual(destination_batch.remaining_quantity, Decimal("4"))

        source_qty = Inventory.objects.get(product=self.product, store=self.source).quantity
        dest_qty = Inventory.objects.get(product=self.product, store=self.dest).quantity
        self.assertEqual(source_qty + dest_qty, Decimal("10"))
        self.assertEqual(StockTransfer.objects.get(pk=transfer.id).status, StockTransfer.STATUS_RECEIVED)
