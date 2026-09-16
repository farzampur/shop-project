from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import Supplier, SupplierTransaction
from products.views import SupplierTransactionViewSet, SupplierPaymentViewSet
from sales.models import CashBox, CashBoxTransaction


class SupplierTransactionIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase694e", password="pw")
        self.store = Store.objects.create(name="Store 6.9.4 E", code="P694E")
        UserStore.objects.create(
            user=self.user, store=self.store, role="manager", is_active=True
        )
        self.supplier = Supplier.objects.create(
            name="Supplier 6.9.4 E", store=self.store
        )
        self.purchase_tx = SupplierTransaction.objects.create(
            supplier=self.supplier,
            transaction_type="purchase",
            amount=Decimal("500"),
            reference_id=123,
        )
        self.factory = APIRequestFactory()

    def _request(self, method, url, data=None):
        request = getattr(self.factory, method)(url, data=data or {}, format="json")
        force_authenticate(request, user=self.user)
        request.user = self.user
        request.query_params = request.GET
        return request

    def test_direct_supplier_transaction_create_is_blocked(self):
        request = self._request(
            "post",
            "/api/products/supplier-transactions/",
            {
                "supplier": self.supplier.id,
                "transaction_type": "purchase",
                "amount": "999",
            },
        )
        response = SupplierTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 405, response.data)
        self.assertEqual(SupplierTransaction.objects.count(), 1)

    def test_purchase_transaction_cannot_be_deleted_or_edited(self):
        patch = SupplierTransactionViewSet.as_view({"patch": "partial_update"})
        delete = SupplierTransactionViewSet.as_view({"delete": "destroy"})

        response = patch(
            self._request(
                "patch",
                f"/api/products/supplier-transactions/{self.purchase_tx.id}/",
                {"amount": "1"},
            ),
            pk=self.purchase_tx.id,
        )
        self.assertEqual(response.status_code, 405, response.data)

        response = delete(
            self._request(
                "delete",
                f"/api/products/supplier-transactions/{self.purchase_tx.id}/",
            ),
            pk=self.purchase_tx.id,
        )
        self.assertEqual(response.status_code, 405, response.data)
        self.assertTrue(
            SupplierTransaction.objects.filter(pk=self.purchase_tx.id).exists()
        )


class SupplierPaymentMutationIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="phase694e_pay", password="pw")
        self.store = Store.objects.create(name="Store 6.9.4 E Pay", code="P694EP")
        UserStore.objects.create(
            user=self.user, store=self.store, role="manager", is_active=True
        )
        self.supplier = Supplier.objects.create(
            name="Supplier 6.9.4 E Pay", store=self.store
        )
        self.cashbox = CashBox.objects.create(
            name="Main", store=self.store, balance=Decimal("1000")
        )
        SupplierTransaction.objects.create(
            supplier=self.supplier,
            transaction_type="purchase",
            amount=Decimal("500"),
            reference_id=999,
        )
        self.factory = APIRequestFactory()

        request = self._request(
            "post",
            "/api/products/supplier-payments/",
            {
                "supplier": self.supplier.id,
                "amount": "200",
                "cashbox": self.cashbox.id,
                "description": "payment integrity",
            },
        )
        response = SupplierPaymentViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201, getattr(response, "data", None))
        self.payment_id = response.data["id"]

    def _request(self, method, url, data=None):
        request = getattr(self.factory, method)(url, data=data or {}, format="json")
        force_authenticate(request, user=self.user)
        request.user = self.user
        request.query_params = request.GET
        return request

    def _snapshot(self):
        self.cashbox.refresh_from_db()
        payment = SupplierTransaction.objects.get(pk=self.payment_id)
        return {
            "cashbox": self.cashbox.balance,
            "supplier_amount": payment.amount,
            "supplier_tx": SupplierTransaction.objects.filter(
                pk=self.payment_id, transaction_type="payment"
            ).count(),
            "cashbox_tx": CashBoxTransaction.objects.filter(
                reference_id=self.payment_id, transaction_type="payment"
            ).count(),
        }

    def test_registered_payment_cannot_be_edited_or_deleted(self):
        before = self._snapshot()

        response = SupplierPaymentViewSet.as_view({"patch": "partial_update"})(
            self._request(
                "patch",
                f"/api/products/supplier-payments/{self.payment_id}/",
                {"amount": "50"},
            ),
            pk=self.payment_id,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self._snapshot(), before)

        response = SupplierPaymentViewSet.as_view({"delete": "destroy"})(
            self._request(
                "delete",
                f"/api/products/supplier-payments/{self.payment_id}/",
            ),
            pk=self.payment_id,
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self._snapshot(), before)
