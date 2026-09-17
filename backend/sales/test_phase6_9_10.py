from decimal import Decimal
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Store
from products.models import Category, Product
from .models import Cart, CartItem, Order, OrderItem

class SalesLineIntegrity610Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="610 Sales Store")
        self.user = User.objects.create_user(username="610sales", password="x")
        self.category = Category.objects.create(store=self.store, name="610 Sales Cat")
        self.product = Product.objects.create(category=self.category, name="610 Sales Product", barcode="61002")
        self.cart = Cart.objects.create(user=self.user, store=self.store)
        self.order = Order.objects.create(user=self.user, store=self.store)

    def assert_db_rejects(self, model, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                model.objects.create(**kwargs)

    def test_cart_item_quantity_must_be_positive(self):
        self.assert_db_rejects(CartItem, cart=self.cart, product=self.product, quantity=0, unit_price=10)

    def test_cart_discount_percent_must_be_between_zero_and_hundred(self):
        self.assert_db_rejects(CartItem, cart=self.cart, product=self.product, quantity=1, unit_price=10, discount_percent=101)
        self.assert_db_rejects(CartItem, cart=self.cart, product=self.product, quantity=1, unit_price=10, discount_percent=-1)

    def test_order_item_quantity_must_be_positive(self):
        self.assert_db_rejects(OrderItem, order=self.order, product=self.product, product_name="610", quantity=0, unit_price=10)
