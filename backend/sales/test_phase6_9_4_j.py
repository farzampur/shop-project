from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Inventory, Product
from .models import CashBox, Customer, CustomerTransaction
from .views import CustomerTransactionViewSet


class CustomerLedgerIntegrityTests(TestCase):
    """6.9.4-J starter audit: Customer Ledger Integrity.

    This starter intentionally changes no production code. The tests define the
    integrity expectations to audit before implementing the J hardening.
    """

    def setUp(self):
        self.store = Store.objects.create(
            name="J Store",
            code="J-STORE-694",
        )
        self.other_store = Store.objects.create(
            name="J Other Store",
            code="J-OTHER-694",
        )
        self.user = User.objects.create_user(username="phase694j", password="test123")
        UserStore.objects.create(user=self.user, store=self.store, role="manager", is_active=True)

        self.customer = Customer.objects.create(
            store=self.store, first_name="J", last_name="Customer", mobile="09120000091"
        )
        self.other_customer = Customer.objects.create(
            store=self.other_store, first_name="Other", last_name="Customer", mobile="09120000092"
        )
        self.cashbox = CashBox.objects.create(store=self.store, name="J Cashbox", balance=Decimal("1000"))
        self.other_cashbox = CashBox.objects.create(
            store=self.other_store, name="J Other Cashbox", balance=Decimal("500")
        )
        self.factory = APIRequestFactory()

    def _request(self, method, data):
        request = getattr(self.factory, method)(
            "/api/sales/customer-transactions/", data=data, format="json"
        )
        force_authenticate(request, user=self.user)
        return request

    def test_customer_transaction_update_is_blocked(self):
        tx = CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal("300"),
        )
        request = self._request("patch", {"amount": "1"})
        response = CustomerTransactionViewSet.as_view({"patch": "partial_update"})(request, pk=tx.id)
        self.assertEqual(response.status_code, 400, response.data)
        tx.refresh_from_db()
        self.assertEqual(tx.amount, Decimal("300"))

    def test_customer_transaction_delete_is_blocked(self):
        tx = CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal("300"),
        )
        request = self._request("delete", {})
        response = CustomerTransactionViewSet.as_view({"delete": "destroy"})(request, pk=tx.id)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(CustomerTransaction.objects.filter(pk=tx.id).exists())

    def test_cross_store_customer_payment_cannot_be_registered(self):
        CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal("300"),
        )
        request = self._request(
            "post",
            {
                "customer": self.other_customer.id,
                "transaction_type": "payment",
                "amount": "100",
                "cashbox": self.cashbox.id,
            },
        )
        response = CustomerTransactionViewSet.as_view({"post": "create"})(request)
        self.assertIn(response.status_code, {400, 403})
        self.assertFalse(
            CustomerTransaction.objects.filter(
                customer=self.other_customer, transaction_type="payment"
            ).exists()
        )

    def test_customer_payment_cannot_use_other_store_cashbox(self):
        CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal("300"),
        )
        request = self._request(
            "post",
            {
                "customer": self.customer.id,
                "transaction_type": "payment",
                "amount": "100",
                "cashbox": self.other_cashbox.id,
            },
        )
        response = CustomerTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400, response.data)
        self.other_cashbox.refresh_from_db()
        self.assertEqual(self.other_cashbox.balance, Decimal("500"))

    def test_customer_payment_without_cashbox_cannot_change_customer_ledger(self):
        CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal("300"),
        )
        request = self._request(
            "post",
            {
                "customer": self.customer.id,
                "transaction_type": "payment",
                "amount": "100",
            },
        )
        response = CustomerTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(
            CustomerTransaction.objects.filter(
                customer=self.customer, transaction_type="payment"
            ).exists()
        )

    def test_customer_payment_with_arbitrary_reference_id_is_rejected(self):
        CustomerTransaction.objects.create(
            customer=self.customer,
            store=self.store,
            transaction_type="sale",
            amount=Decimal("300"),
        )
        request = self._request(
            "post",
            {
                "customer": self.customer.id,
                "transaction_type": "payment",
                "amount": "100",
                "cashbox": self.cashbox.id,
                "reference_id": 999999,
            },
        )
        response = CustomerTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(
            CustomerTransaction.objects.filter(
                customer=self.customer, transaction_type="payment"
            ).exists()
        )
