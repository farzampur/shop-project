from decimal import Decimal
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Store
from .models import Category, Product, Inventory, ProductPrice, Supplier, Purchase


class FinalIntegritySweep612Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="612 Store", code="612")
        self.user = User.objects.create_user(username="612", password="x")
        self.category = Category.objects.create(store=self.store, name="612 Cat")
        self.product = Product.objects.create(category=self.category, name="612 Product", barcode="61201")
        self.supplier = Supplier.objects.create(store=self.store, name="612 Supplier")
        self.purchase = Purchase.objects.create(store=self.store, user=self.user, supplier=self.supplier)

    def reject(self, model, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                model.objects.create(**kwargs)

    def test_inventory_min_quantity_cannot_be_negative(self):
        self.reject(Inventory, product=self.product, store=self.store, quantity=0, min_quantity=-1)

    def test_product_price_end_must_be_after_start(self):
        start = timezone.now()
        self.reject(ProductPrice, product=self.product, store=self.store, price_type="retail", amount=Decimal("10"), effective_from=start, effective_to=start, created_by=self.user)

    def test_product_price_open_ended_interval_is_allowed(self):
        price = ProductPrice.objects.create(product=self.product, store=self.store, price_type="retail", amount=Decimal("10"), effective_from=timezone.now(), effective_to=None, created_by=self.user)
        self.assertIsNone(price.effective_to)
