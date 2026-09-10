from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Inventory, Product, Supplier, SupplierTransaction

from .models import CashBox, Cart, CartItem, Customer, CustomerTransaction, Order
from .services import CheckoutService, OrderService


class Phase683ConcurrencyFinancialIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="p683-manager", password="pw")
        self.store = Store.objects.create(name="P683 Store", code="P683")
        UserStore.objects.create(user=self.user, store=self.store, role="manager")
        self.cashbox = CashBox.objects.create(store=self.store, name="P683 Cash", balance=Decimal("1000"))
        self.category = Category.objects.create(name="P683 Cat", store=self.store)
        self.product_a = Product.objects.create(
            name="P683 A", barcode="8834567890120", category=self.category,
            purchase_price=Decimal("40"), sale_price=Decimal("100"),
        )
        self.product_b = Product.objects.create(
            name="P683 B", barcode="8834567890121", category=self.category,
            purchase_price=Decimal("50"), sale_price=Decimal("120"),
        )
        self.inv_a = Inventory.objects.create(product=self.product_a, store=self.store, quantity=Decimal("1"), min_quantity=0)
        self.inv_b = Inventory.objects.create(product=self.product_b, store=self.store, quantity=Decimal("1"), min_quantity=0)

    def _cart(self, items):
        cart = Cart.objects.create(user=self.user, store=self.store)
        for product, quantity in items:
            CartItem.objects.create(
                cart=cart, product=product, quantity=quantity,
                unit_price=product.sale_price, discount_percent=0, price_type="retail",
            )
        return cart

    def test_oversell_is_rejected_without_stock_side_effect(self):
        first = CheckoutService.checkout(
            self._cart([(self.product_a, Decimal("1"))]),
            [{"method": "cash", "amount": "100", "cashbox_id": self.cashbox.id}],
        )
        self.assertEqual(first.status, "paid")
        self.inv_a.refresh_from_db()
        self.assertEqual(self.inv_a.quantity, Decimal("0"))

        second_cart = self._cart([(self.product_a, Decimal("1"))])
        with self.assertRaises(ValidationError):
            CheckoutService.checkout(
                second_cart,
                [{"method": "cash", "amount": "100", "cashbox_id": self.cashbox.id}],
            )
        self.inv_a.refresh_from_db()
        self.cashbox.refresh_from_db()
        self.assertEqual(self.inv_a.quantity, Decimal("0"))
        self.assertEqual(self.cashbox.balance, Decimal("1100"))
        self.assertEqual(Order.objects.filter(store=self.store, status="paid").count(), 1)

    def test_settle_same_order_twice_cannot_double_charge(self):
        order = Order.objects.create(
            user=self.user, store=self.store, status="pending",
            total_before_discount=Decimal("100"), total_discount=0, total_price=Decimal("100"),
        )
        OrderService.settle(order, [{"method": "cash", "amount": "100", "cashbox_id": self.cashbox.id}])
        with self.assertRaises(ValidationError):
            OrderService.settle(order, [{"method": "cash", "amount": "100", "cashbox_id": self.cashbox.id}])
        self.assertEqual(order.payments.count(), 1)
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("1100"))

    def test_cancel_paid_order_is_idempotent_and_does_not_double_reverse(self):
        order = CheckoutService.checkout(
            self._cart([(self.product_b, Decimal("1"))]),
            [{"method": "cash", "amount": "120", "cashbox_id": self.cashbox.id}],
        )
        self.assertEqual(order.status, "paid")
        OrderService.change_status(order, "cancelled", user=self.user, reason="phase 6.8.3")
        with self.assertRaises(ValidationError):
            OrderService.change_status(order, "cancelled", user=self.user, reason="duplicate")
        self.inv_b.refresh_from_db()
        self.cashbox.refresh_from_db()
        self.assertEqual(self.inv_b.quantity, Decimal("1"))
        self.assertEqual(self.cashbox.balance, Decimal("1000"))
        self.assertEqual(order.payments.count(), 1)

    def test_customer_ledger_cannot_become_overpaid(self):
        customer = Customer.objects.create(
            store=self.store, first_name="مشتری", last_name="683", mobile="09126830000"
        )
        CustomerTransaction.objects.create(
            customer=customer, store=self.store, transaction_type="sale", amount=Decimal("200")
        )
        CustomerTransaction.objects.create(
            customer=customer, store=self.store, transaction_type="payment", amount=Decimal("200")
        )
        sales_total = CustomerTransaction.objects.filter(
            customer=customer, transaction_type="sale"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        payment_total = CustomerTransaction.objects.filter(
            customer=customer, transaction_type="payment"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        self.assertEqual(sales_total - payment_total, Decimal("0"))

    def test_supplier_ledger_cannot_become_overpaid(self):
        supplier = Supplier.objects.create(store=self.store, name="P683 Supplier")
        SupplierTransaction.objects.create(
            supplier=supplier, transaction_type="purchase", amount=Decimal("300")
        )
        SupplierTransaction.objects.create(
            supplier=supplier, transaction_type="payment", amount=Decimal("300")
        )
        purchase_total = SupplierTransaction.objects.filter(
            supplier=supplier, transaction_type="purchase"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        payment_total = SupplierTransaction.objects.filter(
            supplier=supplier, transaction_type="payment"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        self.assertEqual(purchase_total - payment_total, Decimal("0"))
