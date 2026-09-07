from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Category,
    Inventory,
    InventoryTransaction,
    Product,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    Supplier,
    SupplierTransaction,
)
from products.views import (
    InventoryViewSet,
    InventoryTransactionViewSet,
    PurchaseReturnViewSet,
    SupplierPaymentViewSet,
    SupplierViewSet,
    PurchaseViewSet,
)


class Phase4InventoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="inventory-user", password="pw")
        self.other = User.objects.create_user(username="other-user", password="pw")
        self.store_a = Store.objects.create(name="Store A", code="P4-A")
        self.store_b = Store.objects.create(name="Store B", code="P4-B")
        UserStore.objects.create(user=self.user, store=self.store_a, role="warehouse")
        UserStore.objects.create(user=self.other, store=self.store_b, role="warehouse")
        self.cat_a = Category.objects.create(name="Cat A", store=self.store_a)
        self.cat_b = Category.objects.create(name="Cat B", store=self.store_b)
        self.product_a = Product.objects.create(
            name="Product A", barcode="1234567890128", category=self.cat_a,
            purchase_price=Decimal("50"), sale_price=Decimal("100"),
        )
        self.product_b = Product.objects.create(
            name="Product B", barcode="2234567890125", category=self.cat_b,
            purchase_price=Decimal("60"), sale_price=Decimal("120"),
        )
        self.inventory_a = Inventory.objects.create(
            product=self.product_a, store=self.store_a,
            quantity=Decimal("10"), min_quantity=Decimal("5"),
        )
        self.inventory_b = Inventory.objects.create(
            product=self.product_b, store=self.store_b,
            quantity=Decimal("20"), min_quantity=Decimal("5"),
        )
        self.factory = APIRequestFactory()

    def _request(self, user, method, path, data=None):
        request = getattr(self.factory, method)(path, data=data, format="json")
        force_authenticate(request, user=user)
        # These tests call get_queryset() directly, so the raw WSGIRequest
        # needs the authenticated user attribute explicitly.
        request.user = user
        request.query_params = request.GET
        return request

    def test_inventory_queryset_is_store_isolated(self):
        request = self._request(self.user, "get", "/api/products/inventory/")
        view = InventoryViewSet()
        view.request = request
        view.action = "list"
        self.assertEqual(list(view.get_queryset()), [self.inventory_a])

    def test_inventory_adjust_updates_quantity_and_creates_transaction(self):
        request = self._request(
            self.user, "post", f"/api/products/inventory/{self.inventory_a.id}/adjust/",
            {"quantity": "7", "description": "شمارش دوره‌ای"},
        )
        response = InventoryViewSet.as_view({"post": "adjust"})(request, pk=self.inventory_a.id)
        self.assertEqual(response.status_code, 200)
        self.inventory_a.refresh_from_db()
        self.assertEqual(self.inventory_a.quantity, Decimal("7"))
        tx = InventoryTransaction.objects.get(
            product=self.product_a, store=self.store_a,
            transaction_type="adjustment",
        )
        self.assertEqual(tx.quantity, Decimal("-3"))
        self.assertEqual(tx.description, "شمارش دوره‌ای")

    def test_inventory_adjust_rejects_negative_quantity_without_mutation(self):
        request = self._request(
            self.user, "post", f"/api/products/inventory/{self.inventory_a.id}/adjust/",
            {"quantity": "-1"},
        )
        response = InventoryViewSet.as_view({"post": "adjust"})(request, pk=self.inventory_a.id)
        self.assertEqual(response.status_code, 400)
        self.inventory_a.refresh_from_db()
        self.assertEqual(self.inventory_a.quantity, Decimal("10"))
        self.assertFalse(InventoryTransaction.objects.filter(transaction_type="adjustment").exists())

    def test_inventory_adjust_requires_manager_or_warehouse_on_that_store(self):
        seller = User.objects.create_user(username="seller-p4", password="pw")
        UserStore.objects.create(user=seller, store=self.store_a, role="seller")
        request = self._request(
            seller, "post", f"/api/products/inventory/{self.inventory_a.id}/adjust/",
            {"quantity": "8"},
        )
        response = InventoryViewSet.as_view({"post": "adjust"})(request, pk=self.inventory_a.id)
        self.assertEqual(response.status_code, 403)

    def test_inventory_transaction_queryset_is_store_isolated(self):
        InventoryTransaction.objects.create(
            product=self.product_a, store=self.store_a,
            transaction_type="adjustment", quantity=Decimal("1"),
        )
        InventoryTransaction.objects.create(
            product=self.product_b, store=self.store_b,
            transaction_type="adjustment", quantity=Decimal("2"),
        )
        request = self._request(self.user, "get", "/api/products/transactions/")
        view = InventoryTransactionViewSet()
        view.request = request
        view.action = "list"
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().store_id, self.store_a.id)


class Phase4SupplierTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="supplier-user", password="pw")
        self.other = User.objects.create_user(username="supplier-other", password="pw")
        self.store_a = Store.objects.create(name="Supplier Store A", code="S4-A")
        self.store_b = Store.objects.create(name="Supplier Store B", code="S4-B")
        UserStore.objects.create(user=self.user, store=self.store_a, role="manager")
        UserStore.objects.create(user=self.other, store=self.store_b, role="manager")
        self.cat = Category.objects.create(name="Cat", store=self.store_a)
        self.product = Product.objects.create(
            name="Purchased Product", barcode="3234567890122", category=self.cat,
            purchase_price=Decimal("80"), sale_price=Decimal("120"),
        )
        self.supplier = Supplier.objects.create(name="Supplier A", store=self.store_a)
        self.other_supplier = Supplier.objects.create(name="Supplier B", store=self.store_b)

    def test_supplier_queryset_is_store_isolated(self):
        request = APIRequestFactory().get("/api/products/suppliers/")
        force_authenticate(request, user=self.user)
        request.user = self.user
        request.query_params = request.GET
        view = SupplierViewSet()
        view.request = request
        view.action = "list"
        self.assertEqual(list(view.get_queryset()), [self.supplier])

    def test_received_purchase_creates_supplier_debt_once_and_receives_stock(self):
        purchase = Purchase.objects.create(
            supplier=self.supplier, store=self.store_a, user=self.user,
            invoice_number="P4-1", received=False,
        )
        PurchaseItem.objects.create(
            purchase=purchase, product=self.product,
            quantity=Decimal("6"), unit_price=Decimal("80"),
        )
        request = APIRequestFactory().post(
            f"/api/products/purchases/{purchase.id}/receive/", {}, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PurchaseViewSet.as_view({"post": "receive_purchase"})(request, pk=purchase.id)
        self.assertEqual(response.status_code, 200)
        purchase.refresh_from_db()
        self.assertTrue(purchase.received)
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store_a).quantity, Decimal("6"))
        self.assertEqual(
            SupplierTransaction.objects.filter(
                supplier=self.supplier, transaction_type="purchase", reference_id=purchase.id
            ).count(), 1,
        )
        self.assertEqual(
            SupplierTransaction.objects.get(
                supplier=self.supplier, transaction_type="purchase", reference_id=purchase.id
            ).amount,
            Decimal("480"),
        )
        request = APIRequestFactory().post(
            f"/api/products/purchases/{purchase.id}/receive/", {}, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PurchaseViewSet.as_view({"post": "receive_purchase"})(request, pk=purchase.id)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store_a).quantity, Decimal("6"))

    def test_supplier_payment_reduces_cashbox_and_supplier_debt(self):
        from sales.models import CashBox, CashBoxTransaction
        cashbox = CashBox.objects.create(store=self.store_a, name="Main", balance=Decimal("1000"))
        SupplierTransaction.objects.create(
            supplier=self.supplier, transaction_type="purchase", amount=Decimal("600"), reference_id=99
        )
        request = APIRequestFactory().post(
            "/api/products/supplier-payments/",
            {"supplier": self.supplier.id, "amount": "250", "description": "پرداخت تست", "cashbox": cashbox.id},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = SupplierPaymentViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        cashbox.refresh_from_db()
        self.assertEqual(cashbox.balance, Decimal("750"))
        payment = SupplierTransaction.objects.get(supplier=self.supplier, transaction_type="payment")
        self.assertEqual(payment.amount, Decimal("250"))
        self.assertEqual(CashBoxTransaction.objects.get(reference_id=payment.id).amount, Decimal("250"))

    def test_supplier_payment_cannot_exceed_debt_or_cash(self):
        from sales.models import CashBox
        cashbox = CashBox.objects.create(store=self.store_a, name="Main", balance=Decimal("100"))
        SupplierTransaction.objects.create(supplier=self.supplier, transaction_type="purchase", amount=Decimal("80"))
        request = APIRequestFactory().post(
            "/api/products/supplier-payments/",
            {"supplier": self.supplier.id, "amount": "90", "cashbox": cashbox.id}, format="json",
        )
        force_authenticate(request, user=self.user)
        response = SupplierPaymentViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        cashbox.refresh_from_db()
        self.assertEqual(cashbox.balance, Decimal("100"))
        self.assertFalse(SupplierTransaction.objects.filter(transaction_type="payment").exists())

    def test_purchase_return_reduces_inventory_and_supplier_debt(self):
        inventory = Inventory.objects.create(product=self.product, store=self.store_a, quantity=Decimal("10"))
        purchase = Purchase.objects.create(
            supplier=self.supplier, store=self.store_a, user=self.user,
            invoice_number="P4-R", received=True,
        )
        PurchaseItem.objects.create(purchase=purchase, product=self.product, quantity=Decimal("8"), unit_price=Decimal("80"))
        request = APIRequestFactory().post(
            "/api/products/purchase-returns/",
            {"purchase": purchase.id, "product": self.product.id, "quantity": "3", "unit_price": "80", "description": "برگشت تست"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = PurchaseReturnViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 201)
        inventory.refresh_from_db()
        self.assertEqual(inventory.quantity, Decimal("7"))
        ret = PurchaseReturn.objects.get(purchase=purchase)
        self.assertEqual(ret.total_amount, Decimal("240"))
        tx = SupplierTransaction.objects.get(transaction_type="return", reference_id=ret.id)
        self.assertEqual(tx.amount, Decimal("240"))

    def test_purchase_return_cannot_exceed_available_quantity(self):
        Inventory.objects.create(product=self.product, store=self.store_a, quantity=Decimal("10"))
        purchase = Purchase.objects.create(supplier=self.supplier, store=self.store_a, user=self.user, received=True)
        PurchaseItem.objects.create(purchase=purchase, product=self.product, quantity=Decimal("2"), unit_price=Decimal("80"))
        request = APIRequestFactory().post(
            "/api/products/purchase-returns/",
            {"purchase": purchase.id, "product": self.product.id, "quantity": "3", "unit_price": "80"}, format="json",
        )
        force_authenticate(request, user=self.user)
        response = PurchaseReturnViewSet.as_view({"post": "create"})(request)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(PurchaseReturn.objects.filter(purchase=purchase).exists())
