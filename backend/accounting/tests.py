from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import UserStore
from core.models import Store
from products.models import Product, Supplier, Purchase, PurchaseItem, SupplierTransaction
from sales.models import Customer, CustomerTransaction, Order, OrderItem, Payment, CashBox, CashBoxTransaction, Expense, CashTransfer

from .models import Account, AccountingPeriod, JournalEntry, JournalLine
from .services import (
    balance_sheet,
    create_entry,
    ensure_store_setup,
    general_ledger,
    post_customer_transaction,
    post_expense,
    post_purchase,
    post_sale,
    post_supplier_transaction,
    profit_loss,
    reverse_entry,
    sync_store,
    trial_balance,
)


class AccountingBaseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(username="manager", password="pass12345")
        self.other_manager = User.objects.create_user(username="other", password="pass12345")
        self.seller = User.objects.create_user(username="seller", password="pass12345")
        self.superuser = User.objects.create_superuser(username="root", password="pass12345")
        self.store = Store.objects.create(name="Store A", code="A1")
        self.other_store = Store.objects.create(name="Store B", code="B1")
        UserStore.objects.create(user=self.manager, store=self.store, role="manager")
        UserStore.objects.create(user=self.seller, store=self.store, role="seller")
        UserStore.objects.create(user=self.other_manager, store=self.other_store, role="manager")
        ensure_store_setup(self.store)
        ensure_store_setup(self.other_store)
        self.test_asset_account = Account.objects.create(
            store=self.store,
            code="1199",
            name="صندوق آزمون",
            account_type=Account.TYPE_ASSET,
            parent=Account.objects.get(store=self.store, code="1100"),
            is_group=False,
            is_system=False,
            is_active=True,
        )

    def auth(self, user):
        self.client.force_authenticate(user=user)


class AccountingSetupTests(AccountingBaseTests):
    def test_default_chart_is_complete_and_idempotent(self):
        before = Account.objects.filter(store=self.store).count()
        ensure_store_setup(self.store)
        self.assertEqual(Account.objects.filter(store=self.store).count(), before)
        self.assertTrue(Account.objects.filter(store=self.store, code="1100", is_group=True).exists())
        self.assertTrue(Account.objects.filter(store=self.store, code="4100", is_group=False).exists())

    def test_accounts_are_store_isolated(self):
        self.assertFalse(Account.objects.filter(store=self.other_store, code="1100").count() == 0)
        a = Account.objects.get(store=self.store, code="4100")
        b = Account.objects.get(store=self.other_store, code="4100")
        self.assertNotEqual(a.id, b.id)


class JournalIntegrityTests(AccountingBaseTests):
    def _lines(self):
        return [
            {"account": self.test_asset_account.id, "debit": Decimal("100"), "credit": Decimal("0")},
            {"account": Account.objects.get(store=self.store, code="3100").id, "debit": Decimal("0"), "credit": Decimal("100")},
        ]

    def test_balanced_entry_is_created_and_numbered(self):
        entry, created = create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="افتتاح صندوق", lines=self._lines())
        self.assertTrue(created)
        self.assertEqual(entry.entry_number, 1)
        self.assertEqual(entry.lines.count(), 2)

    def test_unbalanced_entry_is_rejected(self):
        lines = self._lines()
        lines[0]["debit"] = Decimal("90")
        with self.assertRaises(Exception):
            create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="نامتوازن", lines=lines)
        self.assertEqual(JournalEntry.objects.filter(store=self.store).count(), 0)

    def test_cross_store_account_is_rejected(self):
        lines = [
            {"account": Account.objects.get(store=self.store, code="1100").id, "debit": 100, "credit": 0},
            {"account": Account.objects.get(store=self.other_store, code="3100").id, "debit": 0, "credit": 100},
        ]
        with self.assertRaises(Exception):
            create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="ایزولاسیون", lines=lines)

    def test_duplicate_source_key_is_idempotent(self):
        first, created1 = create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="A", lines=self._lines(), source_key="x")
        second, created2 = create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="B", lines=self._lines(), source_key="x")
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(first.id, second.id)

    def test_only_manager_can_post_manual_entries(self):
        with self.assertRaises(Exception):
            create_entry(user=self.seller, store=self.store, entry_date=date(2026, 9, 22), description="غیرمجاز", lines=self._lines())

    def test_reversal_creates_opposite_balanced_entry(self):
        entry, _ = create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="A", lines=self._lines())
        reversal = reverse_entry(user=self.manager, entry=entry)
        self.assertEqual(entry.status, JournalEntry.STATUS_REVERSED)
        self.assertEqual(reversal.reversal_of_id, entry.id)
        self.assertEqual(reversal.lines.get(debit__gt=0).debit, Decimal("100.00"))

    def test_closed_period_rejects_new_entry(self):
        period = AccountingPeriod.objects.create(store=self.store, name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), is_closed=True, closed_by=self.manager)
        with self.assertRaises(Exception):
            create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="بسته", lines=self._lines(), period=period)

    def test_store_isolation_api_for_entries(self):
        self.auth(self.manager)
        response = self.client.get("/api/accounting/entries/?store=%s" % self.other_store.id)
        self.assertIn(response.status_code, {403, 404})


class ReportingTests(AccountingBaseTests):
    def setUp(self):
        super().setUp()
        lines = [
            {"account": self.test_asset_account.id, "debit": 1000, "credit": 0},
            {"account": Account.objects.get(store=self.store, code="4100").id, "debit": 0, "credit": 1000},
            {"account": Account.objects.get(store=self.store, code="5100").id, "debit": 600, "credit": 0},
            {"account": Account.objects.get(store=self.store, code="1400").id, "debit": 0, "credit": 600},
        ]
        create_entry(user=self.manager, store=self.store, entry_date=date(2026, 9, 22), description="فروش نمونه", lines=lines)

    def test_trial_balance_is_balanced(self):
        rows = trial_balance(self.store)
        self.assertEqual(sum((r["debit"] for r in rows), Decimal("0")), sum((r["credit"] for r in rows), Decimal("0")))

    def test_profit_loss(self):
        result = profit_loss(self.store)
        self.assertEqual(result["revenue"], Decimal("1000"))
        self.assertEqual(result["expense"], Decimal("600"))
        self.assertEqual(result["net_profit"], Decimal("400"))

    def test_balance_sheet_balances(self):
        result = balance_sheet(self.store, date(2026, 9, 22))
        self.assertTrue(result["balanced"])
        self.assertEqual(result["assets"], result["liabilities_plus_equity"])

    def test_general_ledger_running_balance(self):
        account = Account.objects.get(store=self.store, code="4100")
        rows = general_ledger(self.store, account=account)
        self.assertEqual(rows[-1]["balance"], Decimal("1000.00"))

    def test_reporting_store_isolation(self):
        other = trial_balance(self.other_store)
        self.assertEqual(other, [])


class IntegrationTests(AccountingBaseTests):
    def test_sale_creates_revenue_and_cogs_entries(self):
        cash = CashBox.objects.create(store=self.store, name="صندوق اصلی", balance=0)
        product = Product.objects.create(name="کالا", barcode="1111111111111", category=__import__("products.models", fromlist=["Category"]).Category.objects.create(name="Cat", store=self.store))
        order = Order.objects.create(user=self.manager, store=self.store, status="paid", total_before_discount=100, total_discount=0, total_price=100)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, quantity=1, unit_price=100, purchase_price=60, discount_percent=0, discount_amount=0, total_price_before_discount=100, total_discount_amount=0, total_price=100)
        Payment.objects.create(order=order, method="cash", amount=100, cashbox=cash)
        post_sale(order)
        self.assertTrue(JournalEntry.objects.filter(source_key="sale-revenue:%s" % order.id).exists())
        self.assertTrue(JournalEntry.objects.filter(source_key="sale-cogs:%s" % order.id).exists())

    def test_purchase_creates_inventory_and_payable_entry(self):
        supplier = Supplier.objects.create(store=self.store, name="S")
        purchase = Purchase.objects.create(store=self.store, supplier=supplier, user=self.manager, total_amount=500, received=True)
        post_purchase(purchase)
        entry = JournalEntry.objects.get(source_key="purchase:%s" % purchase.id)
        self.assertEqual(sum(entry.lines.values_list("debit", flat=True)), Decimal("500.00"))

    def test_supplier_payment_requires_cashbox_transaction(self):
        supplier = Supplier.objects.create(store=self.store, name="S2")
        tx = SupplierTransaction.objects.create(supplier=supplier, transaction_type="payment", amount=100)
        post_supplier_transaction(tx)
        self.assertFalse(JournalEntry.objects.filter(source_key="supplier-payment:%s" % tx.id).exists())

    def test_supplier_payment_posts_with_cashbox_transaction(self):
        supplier = Supplier.objects.create(store=self.store, name="S3")
        cash = CashBox.objects.create(store=self.store, name="C", balance=500)
        tx = SupplierTransaction.objects.create(supplier=supplier, transaction_type="payment", amount=100)
        CashBoxTransaction.objects.create(cashbox=cash, transaction_type="payment", amount=100, reference_id=tx.id, reference_type="supplier_transaction")
        post_supplier_transaction(tx)
        self.assertTrue(JournalEntry.objects.filter(source_key="supplier-payment:%s" % tx.id).exists())

    def test_customer_payment_posts_with_cashbox_transaction(self):
        customer = Customer.objects.create(store=self.store, first_name="C", last_name="", mobile="1")
        cash = CashBox.objects.create(store=self.store, name="CC", balance=0)
        tx = CustomerTransaction.objects.create(customer=customer, store=self.store, transaction_type="payment", amount=100)
        CashBoxTransaction.objects.create(cashbox=cash, transaction_type="receive", amount=100, reference_id=tx.id, reference_type="customer_transaction")
        post_customer_transaction(tx)
        self.assertTrue(JournalEntry.objects.filter(source_key="customer-payment:%s" % tx.id).exists())

    def test_expense_posts(self):
        cash = CashBox.objects.create(store=self.store, name="E", balance=1000)
        expense = Expense.objects.create(store=self.store, cashbox=cash, user=self.manager, expense_type="other", title="هزینه", amount=100, expense_date=date(2026, 9, 22))
        post_expense(expense)
        self.assertTrue(JournalEntry.objects.filter(source_key="expense:%s" % expense.id).exists())

@override_settings(ACCOUNTING_AUTO_POSTING=True)
class AccountingSignalIntegrationTests(AccountingBaseTests):
    def test_paid_order_auto_posts(self):
        cash = CashBox.objects.create(store=self.store, name="سیگنال صندوق", balance=0)
        category = __import__("products.models", fromlist=["Category"]).Category.objects.create(name="سیگنال", store=self.store)
        product = Product.objects.create(name="سیگنال کالا", barcode="2222222222222", category=category)
        order = Order.objects.create(user=self.manager, store=self.store, status="pending", total_before_discount=70, total_discount=0, total_price=70)
        OrderItem.objects.create(order=order, product=product, product_name=product.name, quantity=1, unit_price=70, purchase_price=40, discount_percent=0, discount_amount=0, total_price_before_discount=70, total_discount_amount=0, total_price=70)
        Payment.objects.create(order=order, method="cash", amount=70, cashbox=cash)
        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])
        self.assertTrue(JournalEntry.objects.filter(source_key=f"sale-revenue:{order.id}").exists())
        self.assertTrue(JournalEntry.objects.filter(source_key=f"sale-cogs:{order.id}").exists())

    def test_received_purchase_auto_posts(self):
        supplier = Supplier.objects.create(store=self.store, name="سیگنال تأمین‌کننده")
        purchase = Purchase.objects.create(store=self.store, supplier=supplier, user=self.manager, total_amount=500, received=False)
        purchase.received = True
        purchase.save(update_fields=["received", "updated_at"])
        self.assertTrue(JournalEntry.objects.filter(source_key=f"purchase:{purchase.id}").exists())

    def test_customer_payment_auto_posts_after_cashbox_transaction(self):
        customer = Customer.objects.create(store=self.store, first_name="مشتری", mobile="900")
        cash = CashBox.objects.create(store=self.store, name="دریافت", balance=0)
        tx = CustomerTransaction.objects.create(customer=customer, store=self.store, transaction_type="payment", amount=100)
        CashBoxTransaction.objects.create(cashbox=cash, transaction_type="receive", amount=100, reference_id=tx.id, reference_type="customer_transaction")
        self.assertTrue(JournalEntry.objects.filter(source_key=f"customer-payment:{tx.id}").exists())

    def test_supplier_payment_auto_posts_after_cashbox_transaction(self):
        supplier = Supplier.objects.create(store=self.store, name="تأمین‌کننده پرداخت")
        cash = CashBox.objects.create(store=self.store, name="پرداخت", balance=500)
        tx = SupplierTransaction.objects.create(supplier=supplier, transaction_type="payment", amount=100)
        CashBoxTransaction.objects.create(cashbox=cash, transaction_type="payment", amount=100, reference_id=tx.id, reference_type="supplier_transaction")
        self.assertTrue(JournalEntry.objects.filter(source_key=f"supplier-payment:{tx.id}").exists())

    def test_expense_auto_posts(self):
        cash = CashBox.objects.create(store=self.store, name="هزینه", balance=500)
        expense = Expense.objects.create(store=self.store, cashbox=cash, user=self.manager, expense_type="other", title="هزینه سیگنال", amount=100, expense_date=date(2026, 9, 22))
        self.assertTrue(JournalEntry.objects.filter(source_key=f"expense:{expense.id}").exists())


@override_settings(ACCOUNTING_AUTO_POSTING=False)
class AccountingIsolationFlagTests(AccountingBaseTests):
    def test_auto_posting_is_disabled_by_default(self):
        order = Order.objects.create(user=self.manager, store=self.store, status="paid", total_before_discount=100, total_discount=0, total_price=100)
        self.assertFalse(JournalEntry.objects.filter(source_id=order.id).exists())


class AccountingAPITests(AccountingBaseTests):
    def test_setup_endpoint(self):
        self.auth(self.manager)
        response = self.client.post("/api/accounting/setup/", {"store": self.store.id}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_accounts_endpoint_is_store_scoped(self):
        self.auth(self.manager)
        response = self.client.get(f"/api/accounting/accounts/?store={self.store.id}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["store"] == self.store.id for item in response.data))

    def test_seller_is_denied_accounting(self):
        self.auth(self.seller)
        response = self.client.get(f"/api/accounting/accounts/?store={self.store.id}")
        self.assertEqual(response.status_code, 403)

    def test_manual_entry_api_creates_balanced_document(self):
        self.auth(self.manager)
        debit = self.test_asset_account
        credit = Account.objects.get(store=self.store, code="3100")
        response = self.client.post("/api/accounting/entries/create/", {"store": self.store.id, "entry_date": "2026-09-22", "description": "آزمون API", "lines": [{"account": debit.id, "debit": "50", "credit": "0"}, {"account": credit.id, "debit": "0", "credit": "50"}]}, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["description"], "آزمون API")

    def test_profit_loss_api_requires_store(self):
        self.auth(self.manager)
        response = self.client.get("/api/accounting/profit-loss/")
        self.assertEqual(response.status_code, 400)
