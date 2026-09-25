from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Product, Inventory, ProductBatch
from .models import Cart, CartItem, CashBox
from .services import CheckoutService, OrderService


class OrderSettlementIntegrity695Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="695 Sales", code="695-S")
        self.user = User.objects.create_user(username="sales695", password="test123")
        UserStore.objects.create(user=self.user, store=self.store, role="seller", is_active=True)
        self.category = Category.objects.create(store=self.store, name="695 Sales Category")
        self.product = Product.objects.create(category=self.category, name="695 Sales Product")
        Inventory.objects.create(product=self.product, store=self.store, quantity=Decimal("5"), min_quantity=0)
        ProductBatch.objects.create(product=self.product, store=self.store, quantity=Decimal("5"), remaining_quantity=Decimal("5"), purchase_price=Decimal("10"), sale_price=Decimal("20"))

    def test_explicit_order_settlement_rejects_empty_payment(self):
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(cart=cart, product=self.product, quantity=Decimal("1"), unit_price=Decimal("20"), price_type="retail")
        order = CheckoutService.checkout(cart, [])
        self.assertEqual(order.status, "pending")
        with self.assertRaises(ValidationError):
            OrderService.settle(order, [])
        order.refresh_from_db()
        self.assertEqual(order.status, "pending")
        self.assertFalse(order.payments.exists())
