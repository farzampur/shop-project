from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from core.models import Store
from accounts.models import UserStore
from products.models import Supplier, SupplierTransaction
from .models import CashBox, Expense, Customer, CustomerTransaction, Order
from .views import CustomerTransactionViewSet
from .views import FinancialSummaryView


class Phase67FinanceTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.manager = User.objects.create_user(username="p67-manager", password="pw")
        self.cashier = User.objects.create_user(username="p67-cashier", password="pw")
        self.other = User.objects.create_user(username="p67-other", password="pw")
        self.a = Store.objects.create(name="شعبه 67A", code="67-A")
        self.b = Store.objects.create(name="شعبه 67B", code="67-B")
        UserStore.objects.create(user=self.manager, store=self.a, role="manager")
        UserStore.objects.create(user=self.manager, store=self.b, role="manager")
        UserStore.objects.create(user=self.cashier, store=self.a, role="cashier")
        UserStore.objects.create(user=self.other, store=self.b, role="cashier")
        self.cash = CashBox.objects.create(store=self.a, name="صندوق 67A", balance=1000)
        self.customer = Customer.objects.create(store=self.a, first_name="مشتری", last_name="67A", mobile="09126700001")
        self.supplier = Supplier.objects.create(store=self.a, name="تامین‌کننده 67A")

    def _summary(self, user, params=None):
        request = self.factory.get("/api/sales/financial-summary/", params or {})
        force_authenticate(request, user=user)
        return FinancialSummaryView.as_view()(request)

    def test_summary_is_store_isolated(self):
        SupplierTransaction.objects.create(supplier=self.supplier, transaction_type="purchase", amount=500)
        CustomerTransaction.objects.create(customer=self.customer, store=self.a, transaction_type="sale", amount=300)
        Expense.objects.create(store=self.a, cashbox=self.cash, user=self.cashier, expense_type="other", title="هزینه A", amount=50, expense_date="2026-09-10")
        response = self._summary(self.cashier)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["supplier_payable"], Decimal("500.00"))
        self.assertEqual(response.data["customer_receivable"], Decimal("300.00"))
        self.assertEqual(response.data["cash_balance"], Decimal("1000.000"))

    def test_summary_does_not_count_unpaid_orders(self):
        Order.objects.create(user=self.manager, store=self.a, status="pending", total_price=999)
        response = self._summary(self.manager)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sales"], Decimal("0.00"))
        self.assertEqual(response.data["order_count"], 0)

    def test_customer_payment_cannot_exceed_balance(self):
        CustomerTransaction.objects.create(customer=self.customer, store=self.a, transaction_type="sale", amount=100)
        request = self.factory.post("/api/sales/customer-transactions/", {
            "customer": self.customer.id, "transaction_type": "payment",
            "amount": "150", "cashbox": self.cash.id,
        }, format="json")
        force_authenticate(request, user=self.cashier)
        response = CustomerTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(CustomerTransaction.objects.filter(customer=self.customer, transaction_type="payment").count(), 0)

    def test_supplier_payable_accounts_for_returns_and_payments(self):
        SupplierTransaction.objects.create(supplier=self.supplier, transaction_type="purchase", amount=1000)
        SupplierTransaction.objects.create(supplier=self.supplier, transaction_type="return", amount=200)
        SupplierTransaction.objects.create(supplier=self.supplier, transaction_type="payment", amount=300)
        response = self._summary(self.manager)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["supplier_payable"], Decimal("500.00"))
