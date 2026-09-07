from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Product, Inventory
from .models import CashBox, CashBoxTransaction, CashTransfer, Expense, Order, Cart, CartItem, Payment
from .services import CheckoutService
from .views import CashBoxTransactionViewSet, CashTransferViewSet, ExpenseViewSet, DashboardView, SalesReportViewSet


class Phase4CashFinanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="finance-user", password="pw")
        self.other = User.objects.create_user(username="finance-other", password="pw")
        self.store_a = Store.objects.create(name="Finance A", code="F4-A")
        self.store_b = Store.objects.create(name="Finance B", code="F4-B")
        UserStore.objects.create(user=self.user, store=self.store_a, role="cashier")
        UserStore.objects.create(user=self.other, store=self.store_b, role="cashier")
        self.cash_a = CashBox.objects.create(store=self.store_a, name="Main", balance=Decimal("500"))
        self.cash_a2 = CashBox.objects.create(store=self.store_a, name="Secondary", balance=Decimal("100"))
        self.cash_b = CashBox.objects.create(store=self.store_b, name="Main", balance=Decimal("900"))
        self.factory = APIRequestFactory()

    def _auth(self, user, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=user)
        return request

    def test_cashbox_transaction_deposit_updates_balance_and_ledger(self):
        request = self._auth(
            self.user, "post", "/api/sales/cashbox-transactions/",
            {"cashbox": self.cash_a.id, "transaction_type": "deposit", "amount": "150", "description": "واریز تست"},
        )
        response = CashBoxTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        self.cash_a.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("650"))
        self.assertEqual(CashBoxTransaction.objects.filter(cashbox=self.cash_a, transaction_type="deposit", amount=150).count(), 1)

    def test_cashbox_transaction_rejects_withdraw_above_balance(self):
        request = self._auth(
            self.user, "post", "/api/sales/cashbox-transactions/",
            {"cashbox": self.cash_a.id, "transaction_type": "withdraw", "amount": "501"},
        )
        response = CashBoxTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        self.cash_a.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("500"))
        self.assertFalse(CashBoxTransaction.objects.filter(cashbox=self.cash_a).exists())

    def test_cash_transfer_moves_money_only_within_same_store(self):
        request = self._auth(
            self.user, "post", "/api/sales/cash-transfers/",
            {"from_cashbox": self.cash_a.id, "to_cashbox": self.cash_a2.id, "amount": "200", "description": "انتقال تست"},
        )
        response = CashTransferViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        self.cash_a.refresh_from_db(); self.cash_a2.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("300"))
        self.assertEqual(self.cash_a2.balance, Decimal("300"))
        transfer = CashTransfer.objects.get()
        self.assertEqual(CashBoxTransaction.objects.filter(reference_id=transfer.id).count(), 2)

    def test_cash_transfer_rejects_cross_store(self):
        request = self._auth(
            self.user, "post", "/api/sales/cash-transfers/",
            {"from_cashbox": self.cash_a.id, "to_cashbox": self.cash_b.id, "amount": "50"},
        )
        response = CashTransferViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        self.cash_a.refresh_from_db(); self.cash_b.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("500"))
        self.assertEqual(self.cash_b.balance, Decimal("900"))
        self.assertFalse(CashTransfer.objects.exists())

    def test_expense_reduces_cashbox_and_creates_cash_transaction(self):
        from datetime import date
        request = self._auth(
            self.user, "post", "/api/sales/expenses/",
            {"store": self.store_a.id, "cashbox": self.cash_a.id, "expense_type": "other", "title": "هزینه تست", "amount": "125", "expense_date": date.today().isoformat(), "description": "تست"},
        )
        response = ExpenseViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        self.cash_a.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("375"))
        expense = Expense.objects.get(title="هزینه تست")
        self.assertEqual(CashBoxTransaction.objects.get(reference_id=expense.id).transaction_type, "payment")

    def test_expense_rejects_cross_store_cashbox(self):
        from datetime import date
        request = self._auth(
            self.user, "post", "/api/sales/expenses/",
            {"store": self.store_a.id, "cashbox": self.cash_b.id, "expense_type": "other", "title": "غیرمجاز", "amount": "50", "expense_date": date.today().isoformat()},
        )
        response = ExpenseViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Expense.objects.filter(title="غیرمجاز").exists())


class Phase4ReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="report-user", password="pw")
        self.store = Store.objects.create(name="Report Store", code="R4-A")
        UserStore.objects.create(user=self.user, store=self.store, role="manager")
        cat = Category.objects.create(name="Report Cat", store=self.store)
        self.product = Product.objects.create(
            name="Report Product", barcode="4234567890129", category=cat,
            purchase_price=Decimal("50"), sale_price=Decimal("100"),
        )
        Inventory.objects.create(product=self.product, store=self.store, quantity=Decimal("20"))
        self.cash = CashBox.objects.create(store=self.store, name="Main", balance=Decimal("0"))
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(cart=cart, product=self.product, quantity=Decimal("2"), unit_price=Decimal("100"))
        self.order = CheckoutService.checkout(cart, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash.id}])
        self.factory = APIRequestFactory()

    def test_sales_report_summary_returns_sales_cost_profit_and_payment_breakdown(self):
        request = self.factory.get("/api/sales/sales-report/summary/", {"store": self.store.id})
        force_authenticate(request, user=self.user)
        response = SalesReportViewSet.as_view({"get": "summary"})(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["order_count"], 1)
        self.assertEqual(response.data["sales"], Decimal("200"))
        self.assertEqual(response.data["cost"], Decimal("100"))
        self.assertEqual(response.data["gross_profit"], Decimal("100"))
        self.assertEqual(response.data["cash"], Decimal("200"))
        self.assertEqual(response.data["card"], Decimal("0"))
        self.assertEqual(response.data["credit"], Decimal("0"))

    def test_dashboard_reflects_today_sales_inventory_and_profit(self):
        request = self.factory.get("/api/sales/dashboard/")
        force_authenticate(request, user=self.user)
        response = DashboardView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["today_orders"], 1)
        self.assertEqual(response.data["today_sales"], Decimal("200"))
        self.assertEqual(response.data["total_inventory"], Decimal("18"))
        self.assertEqual(response.data["total_profit"], Decimal("100"))

    def test_sales_report_rejects_inaccessible_store(self):
        other_store = Store.objects.create(name="Other", code="R4-B")
        request = self.factory.get("/api/sales/sales-report/summary/", {"store": other_store.id})
        force_authenticate(request, user=self.user)
        response = SalesReportViewSet.as_view({"get": "summary"})(request)
        self.assertEqual(response.status_code, 403)
