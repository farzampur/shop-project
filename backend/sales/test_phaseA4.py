from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store

from .models import CashBox, CashBoxTransaction, Customer, CustomerTransaction
from .views import CustomerTransactionViewSet, CustomerBalanceView


class PhaseA4CustomerPaymentIntegrityTests(TestCase):
    """A4: Customer -> Payment -> CashBox -> Ledger integrity."""

    def setUp(self):
        self.store = Store.objects.create(name="A4 Store", code="A4-STORE")
        self.other_store = Store.objects.create(name="A4 Other", code="A4-OTHER")
        self.user = User.objects.create_user(username="a4-user", password="test123")
        UserStore.objects.create(
            user=self.user, store=self.store, role="cashier", is_active=True
        )

        self.customer = Customer.objects.create(
            store=self.store,
            first_name="A4",
            last_name="Customer",
            mobile="09120000401",
        )
        self.other_customer = Customer.objects.create(
            store=self.other_store,
            first_name="Other",
            last_name="Customer",
            mobile="09120000402",
        )
        self.cashbox = CashBox.objects.create(
            store=self.store, name="A4 Cashbox", balance=Decimal("1000")
        )
        self.other_cashbox = CashBox.objects.create(
            store=self.other_store, name="A4 Other Cashbox", balance=Decimal("500")
        )
        self.factory = APIRequestFactory()

    def _post(self, data):
        request = self.factory.post(
            "/api/sales/customer-transactions/", data=data, format="json"
        )
        force_authenticate(request, user=self.user)
        return CustomerTransactionViewSet.as_view({"post": "create"})(request)

    def _seed_debt(self, amount="300"):
        return CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal(amount),
            reference_id=7001,
        )

    def test_customer_payment_updates_customer_ledger_and_exact_cashbox_entry(self):
        self._seed_debt("300")

        response = self._post(
            {
                "customer": self.customer.id,
                "transaction_type": "payment",
                "amount": "120",
                "cashbox": self.cashbox.id,
            }
        )

        self.assertEqual(response.status_code, 201, response.data)
        payment_tx = CustomerTransaction.objects.get(
            customer=self.customer, transaction_type="payment"
        )
        cash_tx = CashBoxTransaction.objects.get(
            reference_type="customer_transaction", reference_id=payment_tx.id
        )

        self.cashbox.refresh_from_db()
        self.assertEqual(payment_tx.amount, Decimal("120"))
        self.assertEqual(payment_tx.store_id, self.store.id)
        self.assertEqual(cash_tx.transaction_type, "receive")
        self.assertEqual(cash_tx.amount, Decimal("120"))
        self.assertEqual(self.cashbox.balance, Decimal("1120"))
        self.assertEqual(
            CashBoxTransaction.objects.filter(
                cashbox=self.cashbox, reference_type="customer_transaction"
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("120"),
        )

    def test_partial_payment_leaves_exact_customer_balance(self):
        self._seed_debt("300")
        self.assertEqual(self._post({
            "customer": self.customer.id,
            "transaction_type": "payment",
            "amount": "120",
            "cashbox": self.cashbox.id,
        }).status_code, 201)

        request = self.factory.get("/api/sales/customer-balance/1/")
        force_authenticate(request, user=self.user)
        response = CustomerBalanceView.as_view()(request, customer_id=self.customer.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sales"], Decimal("300"))
        self.assertEqual(response.data["payments"], Decimal("120"))
        self.assertEqual(response.data["balance"], Decimal("180"))

    def test_payment_cannot_exceed_customer_debt_and_is_atomic(self):
        self._seed_debt("100")
        response = self._post({
            "customer": self.customer.id,
            "transaction_type": "payment",
            "amount": "101",
            "cashbox": self.cashbox.id,
        })

        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(
            CustomerTransaction.objects.filter(
                customer=self.customer, transaction_type="payment"
            ).exists()
        )
        self.assertFalse(
            CashBoxTransaction.objects.filter(
                cashbox=self.cashbox, reference_type="customer_transaction"
            ).exists()
        )
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("1000"))

    def test_payment_cannot_cross_customer_or_cashbox_store_boundary(self):
        self._seed_debt("300")

        response = self._post({
            "customer": self.customer.id,
            "transaction_type": "payment",
            "amount": "100",
            "cashbox": self.other_cashbox.id,
        })
        self.assertEqual(response.status_code, 400, response.data)

        response = self._post({
            "customer": self.other_customer.id,
            "transaction_type": "payment",
            "amount": "100",
            "cashbox": self.cashbox.id,
        })
        self.assertIn(response.status_code, {400, 403})

        self.other_cashbox.refresh_from_db()
        self.cashbox.refresh_from_db()
        self.assertEqual(self.other_cashbox.balance, Decimal("500"))
        self.assertEqual(self.cashbox.balance, Decimal("1000"))
        self.assertFalse(
            CustomerTransaction.objects.filter(
                customer=self.other_customer, transaction_type="payment"
            ).exists()
        )

    def test_payment_cannot_inject_reference_and_financial_documents_are_immutable(self):
        self._seed_debt("300")
        response = self._post({
            "customer": self.customer.id,
            "transaction_type": "payment",
            "amount": "100",
            "cashbox": self.cashbox.id,
            "reference_id": 999999,
        })
        self.assertEqual(response.status_code, 400, response.data)

        tx = CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal("50"),
        )
        patch = self.factory.patch(
            f"/api/sales/customer-transactions/{tx.id}/",
            {"amount": "1"},
            format="json",
        )
        force_authenticate(patch, user=self.user)
        patch_response = CustomerTransactionViewSet.as_view({"patch": "partial_update"})(
            patch, pk=tx.id
        )
        self.assertEqual(patch_response.status_code, 400, patch_response.data)
        tx.refresh_from_db()
        self.assertEqual(tx.amount, Decimal("50"))
