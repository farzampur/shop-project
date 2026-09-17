from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Product, Supplier
from .models import CashBox, CashBoxTransaction, CashTransfer, Customer, CustomerTransaction, Expense, Order, Payment


class FinancialDatabaseIntegrity696Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="696 Sales", code="696-S")
        self.user = User.objects.create_user(username="audit696s", password="pw")
        UserStore.objects.create(user=self.user, store=self.store, role="manager", is_active=True)
        self.cashbox = CashBox.objects.create(store=self.store, name="696 Cash", balance=Decimal("100"))
        category = Category.objects.create(store=self.store, name="696 Category")
        self.product = Product.objects.create(category=category, name="696 Product", purchase_price=Decimal("10"), sale_price=Decimal("20"))
        self.supplier = Supplier.objects.create(store=self.store, name="696 Supplier")

    def _violates(self, create):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                create()

    def test_payment_amount_must_be_positive(self):
        order = Order.objects.create(store=self.store, user=self.user, total_before_discount=Decimal("10"), total_discount=Decimal("0"), total_price=Decimal("10"))
        self._violates(lambda: Payment.objects.create(order=order, method="cash", amount=Decimal("0"), cashbox=self.cashbox))

    def test_expense_amount_must_be_positive(self):
        self._violates(lambda: Expense.objects.create(store=self.store, cashbox=self.cashbox, user=self.user, expense_type="other", title="bad", amount=Decimal("0"), expense_date="2026-09-17"))

    def test_customer_transaction_amount_must_be_positive(self):
        customer = Customer.objects.create(store=self.store, first_name="696", last_name="Customer", mobile="09120000696")
        self._violates(lambda: CustomerTransaction.objects.create(customer=customer, store=self.store, transaction_type="sale", amount=Decimal("0")))

    def test_cashbox_balance_cannot_be_negative(self):
        self._violates(lambda: CashBox.objects.create(store=self.store, name="bad", balance=Decimal("-1")))

    def test_cashbox_transaction_amount_must_be_positive(self):
        self._violates(lambda: CashBoxTransaction.objects.create(cashbox=self.cashbox, transaction_type="deposit", amount=Decimal("0"), reference_type="manual"))

    def test_cash_transfer_amount_must_be_positive(self):
        other = CashBox.objects.create(store=self.store, name="696 Cash 2", balance=Decimal("100"))
        self._violates(lambda: CashTransfer.objects.create(from_cashbox=self.cashbox, to_cashbox=other, amount=Decimal("0"), created_by=self.user))
