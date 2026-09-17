from decimal import Decimal
from django.db import IntegrityError, transaction
from django.test import TestCase
from core.models import Store
from django.contrib.auth.models import User
from .models import Category, Product, Supplier, Purchase, PurchaseItem, ProductBatch, ProductPrice


class PurchasePricingIntegrity610Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="610 Store", code="610-SRC")
        self.user = User.objects.create_user(username="610", password="x")
        self.category = Category.objects.create(store=self.store, name="610 Cat")
        self.product = Product.objects.create(
            category=self.category,
            name="610 Product",
            barcode="61001",
        )
        self.supplier = Supplier.objects.create(store=self.store, name="610 Supplier")
        self.purchase = Purchase.objects.create(
            store=self.store,
            user=self.user,
            supplier=self.supplier,
        )

    def assert_db_rejects(self, model, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                model.objects.create(**kwargs)

    def test_purchase_item_quantity_must_be_positive(self):
        self.assert_db_rejects(
            PurchaseItem,
            purchase=self.purchase,
            product=self.product,
            quantity=0,
            unit_price=10,
        )

    def test_product_batch_prices_cannot_be_negative(self):
        item = PurchaseItem.objects.create(
            purchase=self.purchase,
            product=self.product,
            quantity=1,
            unit_price=10,
        )
        self.assert_db_rejects(
            ProductBatch,
            purchase_item=item,
            product=self.product,
            store=self.store,
            quantity=1,
            remaining_quantity=1,
            purchase_price=-1,
            sale_price=10,
        )

    def test_product_price_effective_end_must_be_after_start(self):
        from django.utils import timezone

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
