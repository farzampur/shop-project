from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Inventory, Product, ProductBatch

from .models import Cart, CartItem, CashBox, CashBoxTransaction, Customer, CustomerTransaction, OrderCancellation, Payment
from .services import CheckoutService, OrderService


class PhaseA3SaleReturnFinancialIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a3_user", password="pw")
        self.store = Store.objects.create(name="A3 Store", code="A3")
        UserStore.objects.create(user=self.user, store=self.store, role="cashier", is_active=True)
        self.category = Category.objects.create(name="A3 Category", store=self.store)
        self.product = Product.objects.create(
            name="A3 Product", barcode="A3-0001", category=self.category,
            purchase_price=Decimal("50"), sale_price=Decimal("100"),
        )
        self.inventory = Inventory.objects.create(product=self.product, store=self.store, quantity=Decimal("10"))
        self.batch1 = ProductBatch.objects.create(
            product=self.product, store=self.store, quantity=Decimal("5"),
            remaining_quantity=Decimal("5"), purchase_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        self.batch2 = ProductBatch.objects.create(
            product=self.product, store=self.store, quantity=Decimal("5"),
            remaining_quantity=Decimal("5"), purchase_price=Decimal("60"),
            sale_price=Decimal("120"),
        )
        self.cashbox = CashBox.objects.create(store=self.store, name="A3 Cash")
        self.customer = Customer.objects.create(store=self.store, first_name="A3 Customer", mobile="09120000003")

    def _checkout(self, quantity="7", payments=None, price_type="retail"):
        cart = Cart.objects.create(user=self.user, store=self.store, customer=self.customer)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal(quantity),
            unit_price=Decimal("100"), price_type=price_type,
        )
        return CheckoutService.checkout(cart, payments or [])

    def test_cancel_batch_split_sale_restores_inventory_and_each_batch(self):
        order = self._checkout(
            quantity="7",
            payments=[{"method": "cash", "amount": Decimal("740"), "cashbox_id": self.cashbox.id}],
        )

        self.inventory.refresh_from_db()
        self.batch1.refresh_from_db()
        self.batch2.refresh_from_db()
        self.assertEqual(self.inventory.quantity, Decimal("3"))
        self.assertEqual(self.batch1.remaining_quantity, Decimal("0"))
        self.assertEqual(self.batch2.remaining_quantity, Decimal("3"))
        self.assertEqual(order.items.count(), 2)

        OrderService.change_status(order, "cancelled", user=self.user, reason="A3 return")

        self.inventory.refresh_from_db()
        self.batch1.refresh_from_db()
        self.batch2.refresh_from_db()
        self.cashbox.refresh_from_db()
        self.assertEqual(self.inventory.quantity, Decimal("10"))
        self.assertEqual(self.batch1.remaining_quantity, Decimal("5"))
        self.assertEqual(self.batch2.remaining_quantity, Decimal("5"))
        self.assertEqual(self.cashbox.balance, Decimal("0"))
        self.assertEqual(OrderCancellation.objects.filter(order=order).count(), 1)

    def test_cancel_mixed_cash_credit_sale_reverses_only_matching_ledgers(self):
        order = self._checkout(
            quantity="2",
            payments=[
                {"method": "cash", "amount": Decimal("180"), "cashbox_id": self.cashbox.id},
                {"method": "credit", "amount": Decimal("20")},
            ],
        )

        OrderService.change_status(order, "cancelled", user=self.user)
        self.cashbox.refresh_from_db()

        self.assertEqual(self.cashbox.balance, Decimal("0"))
        self.assertEqual(
            CashBoxTransaction.objects.filter(
                cashbox=self.cashbox, reference_type="order", reference_id=order.id,
                transaction_type="receive",
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("180"),
        )
        self.assertEqual(
            CashBoxTransaction.objects.filter(
                cashbox=self.cashbox, reference_type="order", reference_id=order.id,
                transaction_type="payment",
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("180"),
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(
                customer=self.customer, reference_id=order.id, transaction_type="sale",
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("20"),
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(
                customer=self.customer, reference_id=order.id, transaction_type="payment",
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("20"),
        )
        self.assertEqual(Payment.objects.filter(order=order).count(), 2)

    def test_cancelled_sale_cannot_be_reversed_twice(self):
        order = self._checkout(
            quantity="1",
            payments=[{"method": "cash", "amount": Decimal("100"), "cashbox_id": self.cashbox.id}],
        )
        OrderService.change_status(order, "cancelled", user=self.user)

        with self.assertRaises(Exception):
            OrderService.change_status(order, "cancelled", user=self.user)

        self.cashbox.refresh_from_db()
        self.inventory.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("0"))
        self.assertEqual(self.inventory.quantity, Decimal("10"))
        self.assertEqual(OrderCancellation.objects.filter(order=order).count(), 1)
