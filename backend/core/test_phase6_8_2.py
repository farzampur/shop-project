from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Category,
    Inventory,
    Purchase,
    PurchaseItem,
    Product,
    ProductPrice,
    StockTransfer,
    StockTransferItem,
    Supplier,
    SupplierTransaction,
)
from products.services import PurchaseService
from products.views import StockTransferViewSet, SupplierPaymentViewSet
from sales.models import Cart, CashBox, Customer, CustomerTransaction, Order
from sales.services import CheckoutService, OrderService
from sales.views import CartItemViewSet, CustomerTransactionViewSet, FinancialSummaryView


class Phase682E2EAndIsolationTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.manager = User.objects.create_user(username="p682-manager", password="pw")
        self.cashier = User.objects.create_user(username="p682-cashier", password="pw")
        self.other = User.objects.create_user(username="p682-other", password="pw")

        self.a = Store.objects.create(name="شعبه 682A", code="682-A")
        self.b = Store.objects.create(name="شعبه 682B", code="682-B")
        self.c = Store.objects.create(name="شعبه 682C", code="682-C")

        UserStore.objects.create(user=self.manager, store=self.a, role="manager")
        UserStore.objects.create(user=self.manager, store=self.b, role="manager")
        UserStore.objects.create(user=self.cashier, store=self.b, role="cashier")
        UserStore.objects.create(user=self.other, store=self.c, role="cashier")

        self.category = Category.objects.create(store=self.a, name="کالای 682")
        self.product = Product.objects.create(
            category=self.category,
            name="کالای E2E",
            barcode="6820001",
            purchase_price=Decimal("100.00"),
            sale_price=Decimal("150.00"),
        )
        self.inventory_a = Inventory.objects.create(
            product=self.product, store=self.a, quantity=Decimal("10")
        )
        self.supplier = Supplier.objects.create(store=self.a, name="تامین‌کننده E2E")
        self.cash_a = CashBox.objects.create(store=self.a, name="صندوق A", balance=Decimal("1000"))
        self.cash_b = CashBox.objects.create(store=self.b, name="صندوق B", balance=Decimal("100"))
        self.customer_b = Customer.objects.create(
            store=self.b,
            first_name="مشتری",
            last_name="E2E",
            mobile="09126820001",
        )

    def _view_post(self, view, user, path, data, kwargs=None, actions=None):
        request = self.factory.post(path, data, format="json")
        force_authenticate(request, user=user)
        if actions:
            return view.as_view(actions)(request, **(kwargs or {}))
        return view.as_view()(request, **(kwargs or {}))

    def _cart_item(self, cart, user, quantity, price_type="retail"):
        return self._view_post(
            CartItemViewSet,
            user,
            f"/api/sales/carts/{cart.id}/items/",
            {"product": self.product.id, "quantity": str(quantity), "price_type": price_type},
            kwargs={"cart_pk": cart.id},
            actions={"post": "create"},
        )

    def _customer_payment(self, user, amount):
        request = self.factory.post(
            "/api/sales/customer-transactions/",
            {
                "customer": self.customer_b.id,
                "transaction_type": "payment",
                "amount": str(amount),
                "cashbox": self.cash_b.id,
            },
            format="json",
        )
        force_authenticate(request, user=user)
        return CustomerTransactionViewSet.as_view({"post": "create"})(request)

    def _supplier_payment(self, user, amount):
        request = self.factory.post(
            "/api/products/supplier-payments/",
            {
                "supplier": self.supplier.id,
                "amount": str(amount),
                "cashbox": self.cash_a.id,
            },
            format="json",
        )
        force_authenticate(request, user=user)
        return SupplierPaymentViewSet.as_view({"post": "create"})(request)

    def test_end_to_end_store_workflow_preserves_stock_and_financial_integrity(self):
        # 1) Purchase + receive in source store.
        purchase = Purchase.objects.create(
            supplier=self.supplier,
            store=self.a,
            user=self.manager,
            invoice_number="682-E2E",
        )
        PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=Decimal("5"),
            unit_price=Decimal("100"),
        )
        PurchaseService.receive_purchase(purchase)
        self.inventory_a.refresh_from_db()
        self.assertEqual(self.inventory_a.quantity, Decimal("15.000"))
        SupplierTransaction.objects.create(
            supplier=self.supplier,
            transaction_type="purchase",
            amount=purchase.total_amount,
            reference_id=purchase.id,
        )

        # 2) Transfer source -> destination and receive it.
        transfer = StockTransfer.objects.create(
            source_store=self.a,
            destination_store=self.b,
            created_by=self.manager,
        )
        StockTransferItem.objects.create(
            transfer=transfer,
            product=self.product,
            quantity=Decimal("5"),
        )
        approve = self._view_post(
            StockTransferViewSet, self.manager,
            f"/api/products/stock-transfers/{transfer.id}/approve/", {},
            kwargs={"pk": transfer.id}, actions={"post": "approve"},
        )
        self.assertEqual(approve.status_code, 200)
        ship = self._view_post(
            StockTransferViewSet, self.manager,
            f"/api/products/stock-transfers/{transfer.id}/ship/", {},
            kwargs={"pk": transfer.id}, actions={"post": "ship"},
        )
        self.assertEqual(ship.status_code, 200)
        receive = self._view_post(
            StockTransferViewSet, self.manager,
            f"/api/products/stock-transfers/{transfer.id}/receive/", {},
            kwargs={"pk": transfer.id}, actions={"post": "receive"},
        )
        self.assertEqual(receive.status_code, 200)
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.a).quantity, Decimal("10.000"))
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.b).quantity, Decimal("5.000"))

        # 3) Configure destination-store pricing.
        ProductPrice.objects.create(
            product=self.product,
            store=self.b,
            price_type=ProductPrice.TYPE_RETAIL,
            amount=Decimal("200"),
            created_by=self.manager,
        )

        # 4) Cash sale in destination store, then cancel it.
        cash_cart = Cart.objects.create(user=self.manager, store=self.b, customer=None)
        item_response = self._cart_item(cash_cart, self.manager, Decimal("1"))
        self.assertEqual(item_response.status_code, 201)
        cash_cart.refresh_from_db()
        self.assertEqual(cash_cart.items.get().unit_price, Decimal("200.00"))
        cash_order = CheckoutService.checkout(
            cash_cart,
            [{"method": "cash", "amount": Decimal("200"), "cashbox_id": self.cash_b.id}],
        )
        self.assertEqual(cash_order.status, "paid")
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.b).quantity, Decimal("4.000"))
        self.cash_b.refresh_from_db()
        self.assertEqual(self.cash_b.balance, Decimal("300.000"))
        OrderService.change_status(cash_order, "cancelled", user=self.manager, reason="E2E cancellation")
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.b).quantity, Decimal("5.000"))
        self.cash_b.refresh_from_db()
        self.assertEqual(self.cash_b.balance, Decimal("100.000"))

        # 5) Credit sale + customer payment.
        credit_cart = Cart.objects.create(user=self.manager, store=self.b, customer=self.customer_b)
        item_response = self._cart_item(credit_cart, self.manager, Decimal("1"))
        self.assertEqual(item_response.status_code, 201)
        credit_order = CheckoutService.checkout(credit_cart, [{"method": "credit", "amount": Decimal("200")}])
        self.assertEqual(credit_order.status, "paid")
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.b).quantity, Decimal("4.000"))
        payment_response = self._customer_payment(self.manager, Decimal("200"))
        self.assertEqual(payment_response.status_code, 201)
        self.cash_b.refresh_from_db()
        self.assertEqual(self.cash_b.balance, Decimal("300.000"))

        # 6) Supplier payment against the purchase debt.
        supplier_payment = self._supplier_payment(self.manager, Decimal("200"))
        self.assertEqual(supplier_payment.status_code, 201)
        self.cash_a.refresh_from_db()
        self.assertEqual(self.cash_a.balance, Decimal("800.000"))

        # 7) Final financial snapshot: cancelled cash sale is excluded, paid credit sale remains.
        request = self.factory.get("/api/sales/financial-summary/")
        force_authenticate(request, user=self.manager)
        summary = FinancialSummaryView.as_view()(request)
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["sales"], Decimal("200.00"))
        self.assertEqual(summary.data["supplier_payable"], Decimal("300.00"))
        self.assertEqual(summary.data["customer_receivable"], Decimal("0.00"))

    def test_inactive_store_membership_cannot_read_or_write_store_data(self):
        inactive_user = User.objects.create_user(username="p682-inactive", password="pw")
        relation = UserStore.objects.create(user=inactive_user, store=self.b, role="manager", is_active=False)
        relation.save()

        cart = Cart.objects.create(user=self.manager, store=self.b)
        response = self._view_post(
            CartItemViewSet, inactive_user,
            f"/api/sales/carts/{cart.id}/items/",
            {"product": self.product.id, "quantity": "1"},
            kwargs={"cart_pk": cart.id}, actions={"post": "create"},
        )
        self.assertIn(response.status_code, {403, 404})

        request = self.factory.get("/api/sales/financial-summary/")
        force_authenticate(request, user=inactive_user)
        summary = FinancialSummaryView.as_view()(request)
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["sales"], Decimal("0.00"))
        self.assertEqual(summary.data["cash_balance"], Decimal("0.00"))

    def test_user_cannot_access_third_store_financials(self):
        request = self.factory.get("/api/sales/financial-summary/", {"store": self.c.id})
        force_authenticate(request, user=self.manager)
        response = FinancialSummaryView.as_view()(request)
        # FinancialSummaryView intentionally aggregates all authorized stores and
        # does not expose a store filter; this assertion documents that a manager
        # with A/B access cannot gain C data through the query string.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cash_balance"], Decimal("1100.000"))
