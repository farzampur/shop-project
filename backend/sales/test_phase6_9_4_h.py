from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from sales.models import CashBox, CashBoxTransaction
from sales.views import CashBoxViewSet, CashBoxTransactionViewSet


class CashBoxLedgerIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="cash-h", password="pw")
        self.store = Store.objects.create(name="H Store", code="H-01")
        self.other_store = Store.objects.create(name="H Other", code="H-02")
        UserStore.objects.create(user=self.user, store=self.store, role="manager")
        self.cashbox = CashBox.objects.create(
            store=self.store, name="H Cash", balance=Decimal("500")
        )
        self.other_cashbox = CashBox.objects.create(
            store=self.other_store, name="Other Cash", balance=Decimal("900")
        )
        self.factory = APIRequestFactory()

    def _request(self, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=self.user)
        return request

    def test_cashbox_balance_cannot_be_changed_directly(self):
        response = CashBoxViewSet.as_view({"patch": "partial_update"})(
            self._request("patch", f"/api/sales/cashboxes/{self.cashbox.id}/", {"balance": "9999"}),
            pk=self.cashbox.id,
        )
        self.assertEqual(response.status_code, 400)
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("500"))
        self.assertEqual(CashBoxTransaction.objects.count(), 0)

    def test_registered_cashbox_transaction_cannot_be_mutated_or_deleted(self):
        tx = CashBoxTransaction.objects.create(
            cashbox=self.cashbox,
            transaction_type="deposit",
            amount=Decimal("50"),
            reference_type="manual",
        )
        response = CashBoxTransactionViewSet.as_view({"patch": "partial_update"})(
            self._request("patch", f"/api/sales/cashbox-transactions/{tx.id}/", {"amount": "5000"}),
            pk=tx.id,
        )
        self.assertEqual(response.status_code, 405)
        response = CashBoxTransactionViewSet.as_view({"delete": "destroy"})(
            self._request("delete", f"/api/sales/cashbox-transactions/{tx.id}/"),
            pk=tx.id,
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(CashBoxTransaction.objects.filter(pk=tx.id).exists())

    def test_direct_receive_transaction_is_blocked(self):
        response = CashBoxTransactionViewSet.as_view({"post": "create"})(
            self._request("post", "/api/sales/cashbox-transactions/", {
                "cashbox": self.cashbox.id,
                "transaction_type": "receive",
                "amount": "100",
                "reference_id": 999999,
            })
        )
        self.assertEqual(response.status_code, 400)
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("500"))
        self.assertEqual(CashBoxTransaction.objects.count(), 0)

    def test_direct_payment_transaction_is_blocked(self):
        response = CashBoxTransactionViewSet.as_view({"post": "create"})(
            self._request("post", "/api/sales/cashbox-transactions/", {
                "cashbox": self.cashbox.id,
                "transaction_type": "payment",
                "amount": "100",
                "reference_id": 999999,
            })
        )
        self.assertEqual(response.status_code, 400)
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("500"))
        self.assertEqual(CashBoxTransaction.objects.count(), 0)

    def test_manual_deposit_is_ledger_backed(self):
        response = CashBoxTransactionViewSet.as_view({"post": "create"})(
            self._request("post", "/api/sales/cashbox-transactions/", {
                "cashbox": self.cashbox.id,
                "transaction_type": "deposit",
                "amount": "100",
                "description": "H manual deposit",
            })
        )
        self.assertEqual(response.status_code, 201)
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("600"))
        tx = CashBoxTransaction.objects.get()
        self.assertEqual(tx.reference_type, "manual")
        self.assertIsNone(tx.reference_id)

    def test_cashbox_queryset_is_store_isolated(self):
        response = CashBoxViewSet.as_view({"get": "list"})(
            self._request("get", "/api/sales/cashboxes/")
        )
        self.assertEqual(response.status_code, 200)
        ids = {row["id"] for row in response.data}
        self.assertEqual(ids, {self.cashbox.id})
