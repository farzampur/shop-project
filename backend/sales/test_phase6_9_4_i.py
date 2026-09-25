from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Sum
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Inventory, Product, ProductBatch, Supplier, SupplierTransaction
from products.views import SupplierPaymentViewSet, SupplierTransactionViewSet

from .models import (
    Cart,
    CartItem,
    CashBox,
    CashBoxTransaction,
    Customer,
    CustomerTransaction,
    Order,
    Payment,
)
from .services import CheckoutService, OrderService
from .views import CustomerTransactionViewSet


class FinancialTransactionIntegrityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fin-i", password="pw")
        self.store = Store.objects.create(name="I Store", code="I-01")
        UserStore.objects.create(user=self.user, store=self.store, role="manager")
        self.cashbox = CashBox.objects.create(
            store=self.store, name="I Cash", balance=Decimal("1000")
        )
        self.customer = Customer.objects.create(
            store=self.store, first_name="I", last_name="Customer", mobile="09120000001"
        )
        self.supplier = Supplier.objects.create(store=self.store, name="I Supplier")
        self.category = Category.objects.create(name="I Cat", store=self.store)
        self.product = Product.objects.create(
            name="I Product", barcode="9900000000001", category=self.category,
        )
        Inventory.objects.create(product=self.product, store=self.store, quantity=Decimal("10"))
        ProductBatch.objects.create(product=self.product, store=self.store, quantity=10, remaining_quantity=10, purchase_price=40, sale_price=100)
        self.factory = APIRequestFactory()

    def _request(self, method, path, data):
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=self.user)
        return request

    def _cash_ledger_net(self):
        receipts = CashBoxTransaction.objects.filter(
            cashbox=self.cashbox, transaction_type__in={"receive", "deposit"}
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        payments = CashBoxTransaction.objects.filter(
            cashbox=self.cashbox, transaction_type__in={"payment", "withdraw"}
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return receipts - payments

    def test_sale_cash_ledger_matches_cashbox_and_payment(self):
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("2"),
            unit_price=Decimal("100"), price_type="retail",
        )
        order = CheckoutService.checkout(
            cart, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cashbox.id}]
        )

        self.cashbox.refresh_from_db()
        tx = CashBoxTransaction.objects.filter(
            cashbox=self.cashbox, reference_type="order", reference_id=order.id
        )
        self.assertEqual(tx.count(), 1)
        self.assertEqual(tx.first().transaction_type, "receive")
        self.assertEqual(tx.aggregate(total=Sum("amount"))["total"], Decimal("200"))
        self.assertEqual(Payment.objects.filter(order=order).count(), 1)
        self.assertEqual(self.cashbox.balance, Decimal("1200"))
        self.assertEqual(self.cashbox.balance, Decimal("1000") + self._cash_ledger_net())

    def test_mixed_cash_credit_reconciles_both_ledgers_without_duplicate_entries(self):
        cart = Cart.objects.create(user=self.user, store=self.store, customer=self.customer)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("2"),
            unit_price=Decimal("100"), price_type="retail",
        )
        order = CheckoutService.checkout(
            cart,
            [
                {"method": "cash", "amount": Decimal("50"), "cashbox_id": self.cashbox.id},
                {"method": "credit", "amount": Decimal("150")},
            ],
        )

        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("1050"))
        self.assertEqual(
            CashBoxTransaction.objects.filter(reference_type="order", reference_id=order.id).count(),
            1,
        )
        self.assertEqual(
            CashBoxTransaction.objects.filter(reference_type="order", reference_id=order.id)
            .aggregate(total=Sum("amount"))["total"],
            Decimal("50"),
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(
                customer=self.customer, reference_id=order.id, transaction_type="sale"
            ).count(),
            1,
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(
                customer=self.customer, reference_id=order.id, transaction_type="sale"
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("150"),
        )

        with self.assertRaises(ValidationError):
            OrderService.settle(
                order, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cashbox.id}]
            )
        self.assertEqual(Payment.objects.filter(order=order).count(), 2)
        self.assertEqual(
            CashBoxTransaction.objects.filter(reference_type="order", reference_id=order.id).count(), 1
        )

    def test_customer_payment_creates_matching_customer_and_cashbox_entries(self):
        CustomerTransaction.objects.create(
            customer=self.customer, store=self.store, transaction_type="sale",
            amount=Decimal("300"), reference_id=700,
        )
        request = self._request(
            "post",
            "/api/sales/customer-transactions/",
            {
                "customer": self.customer.id,
                "transaction_type": "payment",
                "amount": "120",
                "cashbox": self.cashbox.id,
            },
        )
        response = CustomerTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)

        payment_tx = CustomerTransaction.objects.get(
            customer=self.customer, transaction_type="payment"
        )
        cash_tx = CashBoxTransaction.objects.get(
            reference_type="customer_transaction", reference_id=payment_tx.id
        )
        self.cashbox.refresh_from_db()
        self.assertEqual(payment_tx.amount, Decimal("120"))
        self.assertEqual(cash_tx.transaction_type, "receive")
        self.assertEqual(cash_tx.amount, Decimal("120"))
        self.assertEqual(self.cashbox.balance, Decimal("1120"))

    def test_supplier_payment_creates_matching_supplier_and_cashbox_entries(self):
        SupplierTransaction.objects.create(
            supplier=self.supplier, transaction_type="purchase", amount=Decimal("400"), reference_id=701
        )
        request = self._request(
            "post",
            "/api/products/supplier-payments/",
            {
                "supplier": self.supplier.id,
                "amount": "175",
                "cashbox": self.cashbox.id,
            },
        )
        response = SupplierPaymentViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)

        payment_tx = SupplierTransaction.objects.get(
            supplier=self.supplier, transaction_type="payment"
        )
        cash_tx = CashBoxTransaction.objects.get(
            reference_type="supplier_transaction", reference_id=payment_tx.id
        )
        self.cashbox.refresh_from_db()
        self.assertEqual(payment_tx.amount, Decimal("175"))
        self.assertEqual(cash_tx.transaction_type, "payment")
        self.assertEqual(cash_tx.amount, Decimal("175"))
        self.assertEqual(self.cashbox.balance, Decimal("825"))

    def test_direct_supplier_payment_cannot_bypass_cashbox_ledger(self):
        request = self._request(
            "post",
            "/api/products/supplier-transactions/",
            {
                "supplier": self.supplier.id,
                "transaction_type": "payment",
                "amount": "100",
            },
        )
        response = SupplierTransactionViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            SupplierTransaction.objects.filter(supplier=self.supplier, transaction_type="payment").exists()
        )
        self.assertFalse(CashBoxTransaction.objects.filter(cashbox=self.cashbox).exists())
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("1000"))

    def test_cancellation_reverses_cashbox_ledger_and_customer_ledger_exactly_once(self):
        cart = Cart.objects.create(user=self.user, store=self.store, customer=self.customer)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("2"),
            unit_price=Decimal("100"), price_type="retail",
        )
        order = CheckoutService.checkout(
            cart,
            [
                {"method": "cash", "amount": Decimal("80"), "cashbox_id": self.cashbox.id},
                {"method": "credit", "amount": Decimal("120")},
            ],
        )
        OrderService.change_status(order, "cancelled", user=self.user, reason="I test")

        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("1000"))
        self.assertEqual(
            CashBoxTransaction.objects.filter(reference_type="order", reference_id=order.id).count(),
            2,
        )
        self.assertEqual(
            CashBoxTransaction.objects.filter(
                reference_type="order", reference_id=order.id,
                transaction_type="receive",
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("80"),
        )
        self.assertEqual(
            CashBoxTransaction.objects.filter(
                reference_type="order", reference_id=order.id,
                transaction_type="payment",
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("80"),
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(
                customer=self.customer, reference_id=order.id, transaction_type="sale"
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("120"),
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(
                customer=self.customer, reference_id=order.id, transaction_type="payment"
            ).aggregate(total=Sum("amount"))["total"],
            Decimal("120"),
        )

        with self.assertRaises(ValidationError):
            OrderService.change_status(order, "cancelled", user=self.user, reason="duplicate")
        self.assertEqual(
            CashBoxTransaction.objects.filter(reference_type="order", reference_id=order.id).count(),
            2,
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(reference_id=order.id).count(),
            2,
        )
