from decimal import Decimal
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Store
from products.models import Category, Product, ProductBatch
from .models import Order, OrderItem, OrderItemBatch, CashBox, CashTransfer


class FinalIntegritySweep612Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="612 Sales Store", code="612-S")
        self.user = User.objects.create_user(username="612sales", password="x")
        self.category = Category.objects.create(store=self.store, name="612 Cat")
        self.product = Product.objects.create(category=self.category, name="612 Product", barcode="61211")
        self.order = Order.objects.create(user=self.user, store=self.store)
        self.order_item = OrderItem.objects.create(order=self.order, product=self.product, product_name=self.product.name, quantity=1, unit_price=10)
        self.cashbox = CashBox.objects.create(name="612 Cash", store=self.store, balance=100)

    def reject(self, model, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                model.objects.create(**kwargs)

    def test_order_item_batch_quantity_must_be_positive(self):
        batch = ProductBatch.objects.create(product=self.product, store=self.store, quantity=5, remaining_quantity=5, purchase_price=5, sale_price=10)
        self.reject(OrderItemBatch, order_item=self.order_item, batch=batch, quantity=0)

    def test_cash_transfer_cannot_use_same_cashbox(self):
        self.reject(CashTransfer, from_cashbox=self.cashbox, to_cashbox=self.cashbox, amount=1, created_by=self.user)
