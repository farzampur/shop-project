from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.db import models, close_old_connections, connection
from rest_framework.test import APIRequestFactory, force_authenticate
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from accounts.models import UserStore
from core.models import Store
from products.models import Category, Product, Inventory
from .models import Cart, CartItem, Order, Customer, CashBox, CashBoxTransaction, CustomerTransaction, Payment
from .services import CheckoutService, OrderService
from .views import CustomerViewSet, CashBoxViewSet


class FinancialCoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller", password="pw")
        self.other_user = User.objects.create_user(username="other", password="pw")
        self.store_a = Store.objects.create(name="A", code="A")
        self.store_b = Store.objects.create(name="B", code="B")
        UserStore.objects.create(user=self.user, store=self.store_a, role="cashier")
        UserStore.objects.create(user=self.other_user, store=self.store_b, role="cashier")
        self.cat_a = Category.objects.create(name="Cat A", store=self.store_a)
        self.cat_b = Category.objects.create(name="Cat B", store=self.store_b)
        self.product_a = Product.objects.create(
            name="Product A", barcode="1234567890123", category=self.cat_a,
            purchase_price=Decimal("50"), sale_price=Decimal("100"),
        )
        self.product_b = Product.objects.create(
            name="Product B", barcode="2234567890123", category=self.cat_b,
            purchase_price=Decimal("60"), sale_price=Decimal("120"),
        )
        Inventory.objects.create(product=self.product_a, store=self.store_a, quantity=10)
        Inventory.objects.create(product=self.product_b, store=self.store_b, quantity=10)
        self.customer_a = Customer.objects.create(store=self.store_a, first_name="Ali", mobile="09120000001")
        self.customer_b = Customer.objects.create(store=self.store_b, first_name="Reza", mobile="09120000002")
        self.cash_a = CashBox.objects.create(store=self.store_a, name="Main")
        self.cash_b = CashBox.objects.create(store=self.store_b, name="Main")

    def make_cart(self, customer=None):
        cart = Cart.objects.create(user=self.user, store=self.store_a, customer=customer)
        CartItem.objects.create(cart=cart, product=self.product_a, quantity=2, unit_price=Decimal("100"))
        return cart

    def test_customer_queryset_is_store_isolated(self):
        request = APIRequestFactory().get("/customers/")
        force_authenticate(request, user=self.user)
        view = CustomerViewSet()
        view.action_map = {"get": "list"}
        view.request = view.initialize_request(request)
        self.assertQuerySetEqual(view.get_queryset(), [self.customer_a], transform=lambda x: x)

    def test_cashbox_queryset_is_store_isolated(self):
        request = APIRequestFactory().get("/cashboxes/")
        force_authenticate(request, user=self.user)
        view = CashBoxViewSet()
        view.action_map = {"get": "list"}
        view.request = view.initialize_request(request)
        self.assertQuerySetEqual(view.get_queryset(), [self.cash_a], transform=lambda x: x)

    def test_checkout_cash_posts_to_selected_store_cashbox(self):
        cart = self.make_cart()
        order = CheckoutService.checkout(cart, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash_a.id}])
        self.cash_a.refresh_from_db()
        self.cash_b.refresh_from_db()
        self.assertEqual(order.status, "paid")
        self.assertEqual(self.cash_a.balance, Decimal("200"))
        self.assertEqual(self.cash_b.balance, Decimal("0"))
        self.assertEqual(Payment.objects.get(order=order).cashbox_id, self.cash_a.id)
        self.assertEqual(CashBoxTransaction.objects.filter(cashbox=self.cash_a, reference_id=order.id).count(), 1)

    def test_cross_store_cashbox_is_rejected(self):
        cart = self.make_cart()
        with self.assertRaises(Exception):
            CheckoutService.checkout(cart, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash_b.id}])
        self.assertFalse(Order.objects.filter(store=self.store_a).exists())

    def test_credit_sale_updates_customer_ledger(self):
        cart = self.make_cart(customer=self.customer_a)
        order = CheckoutService.checkout(cart, [{"method": "credit", "amount": Decimal("200")}])
        tx = CustomerTransaction.objects.get(reference_id=order.id, transaction_type="sale")
        self.assertEqual(tx.store_id, self.store_a.id)
        self.assertEqual(tx.amount, Decimal("200"))
        self.assertEqual(order.status, "paid")

    def test_cross_store_customer_cannot_be_attached_to_cart(self):
        cart = Cart.objects.create(user=self.user, store=self.store_a, customer=self.customer_b)
        CartItem.objects.create(cart=cart, product=self.product_a, quantity=1, unit_price=Decimal("100"))
        with self.assertRaises(Exception):
            CheckoutService.checkout(cart, [{"method": "credit", "amount": Decimal("100")}])

    def test_cancel_paid_sale_restores_stock_and_reverses_cash(self):
        cart = self.make_cart()
        order = CheckoutService.checkout(cart, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash_a.id}])
        OrderService.change_status(order, "cancelled")
        inv = Inventory.objects.get(product=self.product_a, store=self.store_a)
        self.cash_a.refresh_from_db()
        self.assertEqual(inv.quantity, Decimal("10"))
        self.assertEqual(self.cash_a.balance, Decimal("0"))
        self.assertEqual(order.status, "cancelled")

    def test_invalid_state_transition_is_rejected(self):
        order = CheckoutService.checkout(self.make_cart())
        with self.assertRaises(Exception):
            OrderService.change_status(order, "paid")

    def test_mixed_cash_and_card_settlement(self):
        cart = self.make_cart()
        order = CheckoutService.checkout(cart, [
            {"method": "cash", "amount": Decimal("80"), "cashbox_id": self.cash_a.id},
            {"method": "card", "amount": Decimal("120"), "cashbox_id": self.cash_a.id},
        ])
        self.cash_a.refresh_from_db()
        self.assertEqual(order.status, "paid")
        self.assertEqual(Payment.objects.filter(order=order).count(), 2)
        self.assertEqual(self.cash_a.balance, Decimal("200"))
        self.assertEqual(
            list(Payment.objects.filter(order=order).values_list("method", "amount")),
            [("cash", Decimal("80")), ("card", Decimal("120"))],
        )

    def test_mixed_credit_and_cash_settlement_updates_both_ledgers(self):
        cart = self.make_cart(customer=self.customer_a)
        order = CheckoutService.checkout(cart, [
            {"method": "cash", "amount": Decimal("50"), "cashbox_id": self.cash_a.id},
            {"method": "credit", "amount": Decimal("150")},
        ])
        self.cash_a.refresh_from_db()
        self.assertEqual(order.status, "paid")
        self.assertEqual(self.cash_a.balance, Decimal("50"))
        tx = CustomerTransaction.objects.get(reference_id=order.id, transaction_type="sale")
        self.assertEqual(tx.amount, Decimal("150"))

    def test_incomplete_payment_rolls_back_order_stock_and_cash(self):
        cart = self.make_cart()
        with self.assertRaises(Exception):
            CheckoutService.checkout(cart, [
                {"method": "cash", "amount": Decimal("199"), "cashbox_id": self.cash_a.id},
            ])
        self.assertFalse(Order.objects.filter(store=self.store_a).exists())
        self.assertEqual(Inventory.objects.get(product=self.product_a, store=self.store_a).quantity, Decimal("10"))
        self.cash_a.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("0"))
        self.assertFalse(Payment.objects.exists())

    def test_zero_or_negative_payment_is_rejected_without_side_effects(self):
        cart = self.make_cart()
        for amount in (Decimal("0"), Decimal("-1")):
            with self.subTest(amount=amount), self.assertRaises(Exception):
                CheckoutService.checkout(cart, [{"method": "cash", "amount": amount, "cashbox_id": self.cash_a.id}])
        self.assertFalse(Order.objects.filter(store=self.store_a).exists())
        self.assertEqual(Inventory.objects.get(product=self.product_a, store=self.store_a).quantity, Decimal("10"))

    def test_second_payment_attempt_for_paid_order_is_rejected(self):
        cart = self.make_cart()
        order = CheckoutService.checkout(cart, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash_a.id}])
        with self.assertRaises(Exception):
            OrderService.settle(order, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash_a.id}])
        self.cash_a.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("200"))
        self.assertEqual(Payment.objects.filter(order=order).count(), 1)

    def test_cancelling_mixed_sale_reverses_cash_and_customer_balance(self):
        cart = self.make_cart(customer=self.customer_a)
        order = CheckoutService.checkout(cart, [
            {"method": "cash", "amount": Decimal("50"), "cashbox_id": self.cash_a.id},
            {"method": "credit", "amount": Decimal("150")},
        ])
        OrderService.change_status(order, "cancelled")
        self.cash_a.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("0"))
        self.assertEqual(
            CustomerTransaction.objects.filter(customer=self.customer_a, reference_id=order.id, transaction_type="sale").count(),
            1,
        )
        self.assertEqual(
            CustomerTransaction.objects.filter(customer=self.customer_a, reference_id=order.id, transaction_type="payment").aggregate(total=models.Sum("amount"))["total"],
            Decimal("150"),
        )

    def test_purchase_price_is_snapshotted_on_sale(self):
        cart = self.make_cart()
        order = CheckoutService.checkout(cart, [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash_a.id}])
        item = order.items.get()
        self.assertEqual(item.purchase_price, Decimal("50"))
        self.product_a.purchase_price = Decimal("70")
        self.product_a.save(update_fields=["purchase_price"])
        item.refresh_from_db()
        self.assertEqual(item.purchase_price, Decimal("50"))

    def test_seller_cannot_create_manual_customer_debt(self):
        from rest_framework.test import APIRequestFactory
        from .views import CustomerTransactionViewSet

        seller = User.objects.create_user(username="seller2", password="pw")
        UserStore.objects.create(user=seller, store=self.store_a, role="seller")
        request = APIRequestFactory().post("/customer-transactions/", {
            "customer": self.customer_a.id,
            "transaction_type": "sale",
            "amount": "100",
        }, format="json")
        force_authenticate(request, user=seller)
        view = CustomerTransactionViewSet()
        view.action_map = {"post": "create"}
        view.format_kwarg = None
        view.request = view.initialize_request(request)
        serializer = view.get_serializer(data=view.request.data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(Exception):
            view.perform_create(serializer)
        self.assertFalse(CustomerTransaction.objects.filter(customer=self.customer_a).exists())


@skipUnlessDBFeature("supports_transactions")
class ConcurrencyHardeningTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(username="concurrent", password="pw")
        self.store = Store.objects.create(name="Concurrency", code="CON")
        UserStore.objects.create(user=self.user, store=self.store, role="cashier")
        self.category = Category.objects.create(name="Concurrent Cat", store=self.store)
        self.product = Product.objects.create(
            name="Concurrent Product", barcode="9999999999999", category=self.category,
            purchase_price=Decimal("50"), sale_price=Decimal("100"),
        )
        Inventory.objects.create(product=self.product, store=self.store, quantity=1)
        self.cashbox = CashBox.objects.create(store=self.store, name="Concurrent Cash")

    def _make_cart(self):
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, unit_price=Decimal("100"))
        return cart

    def test_concurrent_checkouts_cannot_oversell_inventory(self):
        cart1 = self._make_cart()
        cart2 = self._make_cart()
        barrier = Barrier(2)

        def run(cart_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                cart = Cart.objects.get(pk=cart_id)
                return CheckoutService.checkout(
                    cart, [{"method": "cash", "amount": Decimal("100"), "cashbox_id": self.cashbox.id}]
                ).id
            except Exception as exc:
                return exc
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, [cart1.id, cart2.id]))

        successes = [r for r in results if isinstance(r, int)]
        failures = [r for r in results if isinstance(r, Exception)]
        self.assertEqual(len(successes), 1, results)
        self.assertEqual(len(failures), 1, results)
        self.assertEqual(Order.objects.filter(store=self.store, status="paid").count(), 1)
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, Decimal("0"))
        self.assertEqual(Payment.objects.filter(order_id=successes[0]).count(), 1)
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("100"))

    def test_concurrent_settlement_of_same_order_only_pays_once(self):
        cart = self._make_cart()
        order = CheckoutService.checkout(cart)
        barrier = Barrier(2)

        def run():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                fresh_order = Order.objects.get(pk=order.id)
                return OrderService.settle(
                    fresh_order,
                    [{"method": "cash", "amount": Decimal("100"), "cashbox_id": self.cashbox.id}],
                ).id
            except Exception as exc:
                return exc
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: run(), [1, 2]))

        successes = [r for r in results if isinstance(r, int)]
        failures = [r for r in results if isinstance(r, Exception)]
        self.assertEqual(len(successes), 1, results)
        self.assertEqual(len(failures), 1, results)
        self.assertEqual(Order.objects.get(pk=order.id).status, "paid")
        self.assertEqual(Payment.objects.filter(order=order).count(), 1)
        self.cashbox.refresh_from_db()
        self.assertEqual(self.cashbox.balance, Decimal("100"))

class PermissionsMatrixTests(TestCase):
    """Lock the intended per-store role matrix at the permission boundary."""

    def setUp(self):
        self.store = Store.objects.create(name="Permissions", code="PERM")
        self.category = Category.objects.create(name="Category", store=self.store)
        self.product = Product.objects.create(
            name="Product", barcode="5555555555555", category=self.category,
            purchase_price=Decimal("10"), sale_price=Decimal("20"),
        )
        Inventory.objects.create(product=self.product, store=self.store, quantity=10)
        self.customer = Customer.objects.create(
            store=self.store, first_name="Customer", mobile="09120000999"
        )
        self.cashbox = CashBox.objects.create(store=self.store, name="Cash")

        self.users = {}
        for role in ("manager", "warehouse", "seller", "cashier"):
            user = User.objects.create_user(username=f"perm_{role}", password="pw")
            UserStore.objects.create(user=user, store=self.store, role=role)
            self.users[role] = user

    def _permission(self, view_cls, method, role, data=None, query=None, **kwargs):
        factory = APIRequestFactory()
        path = "/permission-matrix/"
        if method == "GET":
            effective_query = query or {}
            if not effective_query and not kwargs:
                effective_query = {"store": self.store.id}
            request = factory.get(path, effective_query)
        elif method == "DELETE":
            request = factory.delete(path, data or {}, format="json")
        else:
            request = getattr(factory, method.lower())(path, data or {}, format="json")
        force_authenticate(request, user=self.users[role])
        view = view_cls()
        view.action_map = {method.lower(): "list" if method == "GET" else "create"}
        view.kwargs = kwargs
        view.format_kwarg = None
        drf_request = view.initialize_request(request)

        # APIRequestFactory.force_authenticate marks the underlying request,
        # but this helper calls permission classes directly instead of going
        # through APIView.initial(). Bind the authenticated user explicitly so
        # IsAuthenticated and StoreRolePermission see the same user that a
        # real DRF request would see.
        drf_request.user = self.users[role]
        view.request = drf_request

        return all(permission.has_permission(drf_request, view) for permission in view.get_permissions())

    def test_catalog_write_matrix(self):
        from products.views import CategoryViewSet, ProductViewSet
        for view_cls in (CategoryViewSet, ProductViewSet):
            for role in ("manager", "warehouse"):
                self.assertTrue(self._permission(view_cls, "POST", role, {"store": self.store.id, "category": self.category.id}), (view_cls.__name__, role, "POST"))
            for role in ("seller", "cashier"):
                self.assertFalse(self._permission(view_cls, "POST", role, {"store": self.store.id, "category": self.category.id}), (view_cls.__name__, role, "POST"))
            self.assertTrue(self._permission(view_cls, "GET", "seller", query={"store": self.store.id}))
            self.assertFalse(self._permission(view_cls, "DELETE", "warehouse", {"store": self.store.id}))
            self.assertTrue(self._permission(view_cls, "DELETE", "manager", {"store": self.store.id}))

    def test_read_access_also_respects_restricted_roles(self):
        from products.views import SupplierViewSet, PurchaseViewSet
        from sales.views import CashBoxViewSet, CustomerViewSet

        # Purchasing data is manager/warehouse only.
        for view_cls in (SupplierViewSet, PurchaseViewSet):
            self.assertTrue(self._permission(view_cls, "GET", "warehouse"))
            self.assertTrue(self._permission(view_cls, "GET", "manager"))
            self.assertFalse(self._permission(view_cls, "GET", "seller"))
            self.assertFalse(self._permission(view_cls, "GET", "cashier"))

        # Financial cashbox data is manager/cashier only.
        self.assertTrue(self._permission(CashBoxViewSet, "GET", "cashier"))
        self.assertTrue(self._permission(CashBoxViewSet, "GET", "manager"))
        self.assertFalse(self._permission(CashBoxViewSet, "GET", "seller"))
        self.assertFalse(self._permission(CashBoxViewSet, "GET", "warehouse"))

        # Customer data remains available to sales roles.
        for role in ("manager", "seller", "cashier"):
            self.assertTrue(self._permission(CustomerViewSet, "GET", role))
        self.assertFalse(self._permission(CustomerViewSet, "GET", "warehouse"))

    def test_sales_and_financial_matrix(self):
        from sales.views import (
            CartViewSet, CustomerViewSet, CustomerTransactionViewSet,
            CashBoxViewSet, CashBoxTransactionViewSet, CashTransferViewSet,
            ExpenseViewSet,
        )
        sales_roles = ("manager", "seller", "cashier")
        non_sales_role = "warehouse"

        for role in sales_roles:
            self.assertTrue(self._permission(CartViewSet, "POST", role, {"store": self.store.id}), role)
            self.assertTrue(self._permission(CustomerViewSet, "POST", role, {"store": self.store.id}), role)
        self.assertFalse(self._permission(CartViewSet, "POST", non_sales_role, {"store": self.store.id}))
        self.assertFalse(self._permission(CustomerViewSet, "POST", non_sales_role, {"store": self.store.id}))

        for view_cls, data in (
            (CashBoxViewSet, {"store": self.store.id, "name": "Second"}),
            (ExpenseViewSet, {"store": self.store.id, "cashbox": self.cashbox.id, "amount": "1"}),
            (CashBoxTransactionViewSet, {"cashbox": self.cashbox.id, "transaction_type": "deposit", "amount": "1"}),
            (CashTransferViewSet, {"from_cashbox": self.cashbox.id, "to_cashbox": self.cashbox.id, "amount": "1"}),
            (CustomerTransactionViewSet, {"customer": self.customer.id, "transaction_type": "payment", "amount": "1", "cashbox": self.cashbox.id}),
        ):
            for role in ("manager", "cashier"):
                self.assertTrue(self._permission(view_cls, "POST", role, data), (view_cls.__name__, role))
            for role in ("seller", "warehouse"):
                self.assertFalse(self._permission(view_cls, "POST", role, data), (view_cls.__name__, role))

    def test_inventory_and_purchasing_matrix(self):
        from products.views import InventoryViewSet, SupplierViewSet, PurchaseViewSet, SupplierTransactionViewSet, SupplierPaymentViewSet
        from products.models import Supplier
        supplier = Supplier.objects.create(store=self.store, name="Supplier")
        warehouse_roles = ("manager", "warehouse")

        for role in warehouse_roles:
            self.assertTrue(self._permission(InventoryViewSet, "POST", role, {"store": self.store.id, "product": self.product.id, "quantity": "1"}), ("inventory", role))
            self.assertTrue(self._permission(SupplierViewSet, "POST", role, {"store": self.store.id, "name": "S"}), ("supplier", role))
            self.assertTrue(self._permission(PurchaseViewSet, "POST", role, {"store": self.store.id, "supplier": supplier.id}), ("purchase", role))
            self.assertTrue(self._permission(SupplierTransactionViewSet, "POST", role, {"supplier": supplier.id, "transaction_type": "purchase", "amount": "1"}), ("supplier_tx", role))

        for role in ("seller", "cashier"):
            self.assertFalse(self._permission(InventoryViewSet, "POST", role, {"store": self.store.id, "product": self.product.id, "quantity": "1"}))
            self.assertFalse(self._permission(SupplierViewSet, "POST", role, {"store": self.store.id, "name": "S"}))
            self.assertFalse(self._permission(PurchaseViewSet, "POST", role, {"store": self.store.id, "supplier": supplier.id}))
            self.assertFalse(self._permission(SupplierTransactionViewSet, "POST", role, {"supplier": supplier.id, "transaction_type": "purchase", "amount": "1"}))

        for role in ("manager", "cashier"):
            self.assertTrue(self._permission(SupplierPaymentViewSet, "POST", role, {"supplier": supplier.id, "amount": "1", "cashbox": self.cashbox.id}), ("supplier_payment", role))
        for role in ("seller", "warehouse"):
            self.assertFalse(self._permission(SupplierPaymentViewSet, "POST", role, {"supplier": supplier.id, "amount": "1", "cashbox": self.cashbox.id}), ("supplier_payment", role))
