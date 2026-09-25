from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import UserStore
from core.models import Store
from products.models import (Category, Product, ProductBatch, Purchase, PurchaseItem, StockTransfer, StockTransferBatchAllocation, StockTransferItem, Supplier)


class BatchInvariantTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase694f", password="pw")
        self.store = Store.objects.create(name="Store 6.9.4 F", code="P694F")
        self.destination_store = Store.objects.create(name="Store 6.9.4 F Destination", code="P694FD")
        UserStore.objects.create(user=self.user, store=self.destination_store, role="manager", is_active=True)
        UserStore.objects.create(user=self.user, store=self.store, role="manager", is_active=True)
        category = Category.objects.create(name="Cat 6.9.4 F", store=self.store)
        self.product = Product.objects.create(name="Product 6.9.4 F", barcode="6940002", category=category)
        supplier = Supplier.objects.create(name="Supplier 6.9.4 F", store=self.store)
        purchase = Purchase.objects.create(supplier=supplier, store=self.store, user=self.user, received=True)
        self.item = PurchaseItem.objects.create(purchase=purchase, product=self.product, quantity=Decimal("10"), unit_price=Decimal("50"), sale_price=Decimal("80"))
        self.batch = ProductBatch.objects.create(purchase_item=self.item, product=self.product, store=self.store, quantity=Decimal("10"), remaining_quantity=Decimal("10"), purchase_price=Decimal("50"), sale_price=Decimal("80"))
        transfer = StockTransfer.objects.create(source_store=self.store, destination_store=self.destination_store, created_by=self.user)
        self.transfer_item = StockTransferItem.objects.create(transfer=transfer, product=self.product, quantity=Decimal("2"))

    def test_product_batch_remaining_cannot_exceed_quantity(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductBatch.objects.create(purchase_item=None, product=self.product, store=self.store, quantity=Decimal("5"), remaining_quantity=Decimal("6"), purchase_price=Decimal("50"), sale_price=Decimal("80"))

    def test_transfer_batch_allocation_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                StockTransferBatchAllocation.objects.create(transfer_item=self.transfer_item, source_batch=self.batch, quantity=Decimal("0"))

    def test_valid_batch_allocation_remains_allowed(self):
        allocation = StockTransferBatchAllocation.objects.create(transfer_item=self.transfer_item, source_batch=self.batch, quantity=Decimal("2"))
        self.assertEqual(allocation.quantity, Decimal("2"))
