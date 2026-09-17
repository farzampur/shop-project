from decimal import Decimal
from django.contrib.auth.models import User
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.utils import timezone

from core.models import Store
from .models import (
    Category,
    Product,
    ProductBatch,
    ProductPrice,
    Purchase,
    PurchaseItem,
    StockTransfer,
)


class Phase613IntegrityReconciliationTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="613 Store", code="613-SRC")
        self.other_store = Store.objects.create(name="613 Other Store", code="613-DST")
        self.user = User.objects.create_user(username="613", password="x")
        self.category = Category.objects.create(store=self.store, name="613 Cat")
        self.product = Product.objects.create(
            category=self.category,
            name="613 Product",
            barcode="61301",
        )
        self.supplier = __import__(
            "products.models", fromlist=["Supplier"]
        ).Supplier.objects.create(
            store=self.store,
            name="613 Supplier",
        )
        self.purchase = Purchase.objects.create(
            store=self.store,
            user=self.user,
            supplier=self.supplier,
        )
        self.purchase_item = PurchaseItem.objects.create(
            purchase=self.purchase,
            product=self.product,
            quantity=5,
            unit_price=10,
            sale_price=15,
        )

    def assert_db_rejects(self, model, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                model.objects.create(**kwargs)

    def test_product_price_invalid_effective_window_rejected(self):
        start = timezone.now()
        self.assert_db_rejects(
            ProductPrice,
            product=self.product,
            store=self.store,
            amount=Decimal("0"),
            effective_from=start,
            effective_to=start,
            created_by=self.user,
        )

    def test_product_batch_remaining_cannot_exceed_quantity(self):
        self.assert_db_rejects(
            ProductBatch,
            purchase_item=self.purchase_item,
            product=self.product,
            store=self.store,
            quantity=5,
            remaining_quantity=6,
            purchase_price=10,
            sale_price=15,
        )

    def test_same_store_stock_transfer_rejected(self):
        self.assert_db_rejects(
            StockTransfer,
            source_store=self.store,
            destination_store=self.store,
            created_by=self.user,
        )

    def test_product_price_effective_window_constraint_exists(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor,
                ProductPrice._meta.db_table,
            )
        self.assertIn("product_price_effective_end_after_start", constraints)
        self.assertTrue(
            constraints["product_price_effective_end_after_start"]["check"]
        )
