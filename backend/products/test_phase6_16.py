from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Category,
    Inventory,
    InventoryTransaction,
    Product,
    ProductBatch,
    Purchase,
    PurchaseItem,
    Supplier,
    SupplierTransaction,
)
from products.services import PurchaseService
from products.views import PurchaseReturnViewSet
from sales.models import Cart, CartItem, CashBox, CashBoxTransaction, Customer, CustomerTransaction, Order, OrderItemBatch
from sales.services import CheckoutService, OrderService


class Phase616FinancialInventoryE2ETests(TestCase):
    """Targeted end-to-end financial + inventory integrity checks.

    This phase intentionally stays small: it validates the critical business
    flows without rerunning the historical/full regression suite.
    """

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="p616-manager", password="pw")
        self.store = Store.objects.create(name="Phase 616 Store", code="616-S")
        UserStore.objects.create(user=self.user, store=self.store, role="manager")

        self.category = Category.objects.create(name="Phase 616 Category", store=self.store)
        self.product = Product.objects.create(
            name="Phase 616 Product",
            barcode="6160000001",
            category=self.category,
        )
        self.supplier = Supplier.objects.create(store=self.store, name="Phase 616 Supplier")
        self.cashbox = CashBox.objects.create(
            store=self.store, name="Phase 616 Cashbox", balance=Decimal("1000")
        )
        self.customer = Customer.objects.create(
            store=self.store,
            first_name="Phase",
            last_name="Customer",
            mobile="09166160001",
        )

    def _purchase(self, quantity, buy_price, sale_price):
        purchase = Purchase.objects.create(
            supplier=self.supplier,
            store=self.store,
            user=self.user,
        )
        PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=Decimal(quantity),
            unit_price=Decimal(buy_price),
            sale_price=Decimal(sale_price),
        )
        PurchaseService.receive_purchase(purchase)
        purchase.refresh_from_db()
        return purchase

    def _cash_cart(self, quantity="1", customer=None):
        cart = Cart.objects.create(user=self.user, store=self.store, customer=customer)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=Decimal(quantity),
            unit_price=Decimal("999"),
            price_type="retail",
            discount_percent=Decimal("0"),
        )
        return cart

    def _purchase_return(self, purchase, quantity):
        request = self.factory.post(
            "/api/products/purchase-returns/",
            {
                "purchase": purchase.id,
                "product": self.product.id,
                "quantity": str(quantity),
                "unit_price": "1",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = PurchaseReturnViewSet.as_view({"post": "create"})(request)
        return response

    def test_purchase_receive_keeps_inventory_batch_and_supplier_value_aligned(self):
        purchase = self._purchase("5", "40", "70")

        inventory = Inventory.objects.get(product=self.product, store=self.store)
        batch = ProductBatch.objects.get(purchase_item__purchase=purchase)
        ledger = InventoryTransaction.objects.get(
            product=self.product,
            store=self.store,
            transaction_type=InventoryTransaction.TYPE_PURCHASE,
            reference_id=purchase.id,
        )

        self.assertEqual(inventory.quantity, Decimal("5.000"))
        self.assertEqual(batch.quantity, Decimal("5.000"))
        self.assertEqual(batch.remaining_quantity, Decimal("5.000"))
        self.assertEqual(batch.purchase_price, Decimal("40.00"))
        self.assertEqual(batch.sale_price, Decimal("70.00"))
        self.assertEqual(purchase.total_amount, Decimal("200.00"))
        self.assertEqual(ledger.quantity, Decimal("5.000"))

    def test_retail_sale_spans_fifo_batches_and_preserves_batch_snapshots(self):
        first = self._purchase("2", "40", "70")
        second = self._purchase("3", "50", "90")
        cart = self._cash_cart("4")

        order = CheckoutService.checkout(
            cart,
            [{"method": "cash", "amount": Decimal("320"), "cashbox_id": self.cashbox.id}],
        )

        self.assertEqual(order.status, "paid")
        self.assertEqual(order.total_price, Decimal("320.00"))
        self.assertEqual(order.items.count(), 2)

        items = list(order.items.order_by("id"))
        self.assertEqual(
            [(item.quantity, item.unit_price, item.purchase_price) for item in items],
            [
                (Decimal("2.000"), Decimal("70.00"), Decimal("40.00")),
                (Decimal("2.000"), Decimal("90.00"), Decimal("50.00")),
            ],
        )

        allocations = list(
            OrderItemBatch.objects.filter(order_item__order=order)
            .order_by("order_item_id")
            .values_list("batch_id", "quantity")
        )
        first_batch = ProductBatch.objects.get(purchase_item__purchase=first)
        second_batch = ProductBatch.objects.get(purchase_item__purchase=second)
        self.assertEqual(
            allocations,
            [(first_batch.id, Decimal("2.000")), (second_batch.id, Decimal("2.000"))],
        )
        self.assertEqual(ProductBatch.objects.get(pk=first_batch.id).remaining_quantity, Decimal("0.000"))
        self.assertEqual(ProductBatch.objects.get(pk=second_batch.id).remaining_quantity, Decimal("1.000"))
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, Decimal("1.000"))

    def test_cash_sale_cancellation_reverses_stock_batch_cash_and_ledger_once(self):
        purchase = self._purchase("5", "40", "70")
        batch = ProductBatch.objects.get(purchase_item__purchase=purchase)
        order = CheckoutService.checkout(
            self._cash_cart("2"),
            [{"method": "cash", "amount": Decimal("140"), "cashbox_id": self.cashbox.id}],
        )

        self.assertEqual(self.cashbox.__class__.objects.get(pk=self.cashbox.id).balance, Decimal("1140.000"))
        OrderService.change_status(order, "cancelled", user=self.user, reason="phase 6.16")

        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, Decimal("5.000"))
        self.assertEqual(ProductBatch.objects.get(pk=batch.id).remaining_quantity, Decimal("5.000"))
        self.assertEqual(CashBox.objects.get(pk=self.cashbox.id).balance, Decimal("1000.000"))
        self.assertEqual(
            CashBoxTransaction.objects.filter(reference_id=order.id, transaction_type="receive").count(),
            1,
        )
        self.assertEqual(
            CashBoxTransaction.objects.filter(reference_id=order.id, transaction_type="payment").count(),
            1,
        )
        self.assertEqual(
            InventoryTransaction.objects.filter(reference_id=order.id, transaction_type="sale").count(),
            1,
        )
        self.assertEqual(
            InventoryTransaction.objects.filter(reference_id=order.id, transaction_type="return").count(),
            1,
        )

    def test_credit_sale_cancellation_reverses_customer_receivable(self):
        self._purchase("3", "40", "70")
        order = CheckoutService.checkout(
            self._cash_cart("1", customer=self.customer),
            [{"method": "credit", "amount": Decimal("70")}],
        )

        sale_tx = CustomerTransaction.objects.get(
            customer=self.customer, reference_id=order.id, transaction_type="sale"
        )
        self.assertEqual(sale_tx.amount, Decimal("70.00"))

        OrderService.change_status(order, "cancelled", user=self.user, reason="phase 6.16 credit reversal")

        reversal = CustomerTransaction.objects.get(
            customer=self.customer, reference_id=order.id, transaction_type="payment"
        )
        self.assertEqual(reversal.amount, Decimal("70.00"))
        self.assertEqual(
            CustomerTransaction.objects.filter(customer=self.customer, reference_id=order.id).count(),
            2,
        )

    def test_purchase_return_reduces_batch_inventory_and_supplier_debt(self):
        purchase = self._purchase("5", "40", "70")
        response = self._purchase_return(purchase, "2")

        self.assertEqual(response.status_code, 201, response.data)
        batch = ProductBatch.objects.get(purchase_item__purchase=purchase)
        inventory = Inventory.objects.get(product=self.product, store=self.store)
        return_tx = SupplierTransaction.objects.get(
            supplier=self.supplier,
            transaction_type="return",
            reference_id=response.data["id"],
        )

        self.assertEqual(inventory.quantity, Decimal("3.000"))
        self.assertEqual(batch.remaining_quantity, Decimal("3.000"))
        self.assertEqual(response.data["total_amount"], "80.00")
        self.assertEqual(return_tx.amount, Decimal("80.00"))

    def test_failed_payment_rolls_back_sale_stock_batch_and_cashbox(self):
        purchase = self._purchase("5", "40", "70")
        batch = ProductBatch.objects.get(purchase_item__purchase=purchase)
        cart = self._cash_cart("2")

        with self.assertRaises(ValidationError):
            CheckoutService.checkout(
                cart,
                [{"method": "cash", "amount": Decimal("69"), "cashbox_id": self.cashbox.id}],
            )

        self.assertFalse(Order.objects.filter(store=self.store).exists())
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, Decimal("5.000"))
        self.assertEqual(ProductBatch.objects.get(pk=batch.id).remaining_quantity, Decimal("5.000"))
        self.assertEqual(CashBox.objects.get(pk=self.cashbox.id).balance, Decimal("1000.000"))
        self.assertFalse(InventoryTransaction.objects.filter(transaction_type="sale").exists())
        self.assertTrue(CartItem.objects.filter(cart=cart).exists())

    def test_purchase_return_cannot_exceed_stock_remaining_after_sale(self):
        purchase = self._purchase("5", "40", "70")
        CheckoutService.checkout(
            self._cash_cart("3"),
            [{"method": "cash", "amount": Decimal("210"), "cashbox_id": self.cashbox.id}],
        )

        before_inventory = Inventory.objects.get(product=self.product, store=self.store).quantity
        before_batch = ProductBatch.objects.get(purchase_item__purchase=purchase).remaining_quantity
        before_returns = purchase.returns.count()

        response = self._purchase_return(purchase, "3")
        self.assertEqual(response.status_code, 400)

        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, before_inventory)
        self.assertEqual(ProductBatch.objects.get(purchase_item__purchase=purchase).remaining_quantity, before_batch)
        self.assertEqual(purchase.returns.count(), before_returns)
        self.assertFalse(
            SupplierTransaction.objects.filter(supplier=self.supplier, transaction_type="return").exists()
        )
