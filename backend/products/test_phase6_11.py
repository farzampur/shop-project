from decimal import Decimal
from threading import Barrier, Thread
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError

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
)
from products.services import PurchaseService
from sales.models import CashBox, Cart, CartItem, Order
from sales.services import CheckoutService


class Phase611TransactionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(username="phase611", password="pw")
        self.store = Store.objects.create(name="611 Store", code="611")
        self.category = Category.objects.create(name="611 Category", store=self.store)
        self.product = Product.objects.create(
            name="611 Product",
            barcode="611000000001",
            category=self.category,
            unit="عدد",
        )
        self.supplier = Supplier.objects.create(store=self.store, name="611 Supplier")

    def _purchase(self, quantity, buy="100", sell="130"):
        purchase = Purchase.objects.create(
            supplier=self.supplier,
            store=self.store,
            user=self.user,
            received=False,
        )
        PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=Decimal(quantity),
            unit_price=Decimal(buy),
            sale_price=Decimal(sell),
        )
        return purchase

    def _run_threads(self, target, count=2):
        barrier = Barrier(count)
        results = [None] * count

        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                target(index)
                results[index] = ("ok", None)
            except Exception as exc:  # noqa: BLE001 - assertions inspect exact outcomes below
                results[index] = ("error", exc)
            finally:
                close_old_connections()

        threads = [Thread(target=worker, args=(i,)) for i in range(count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        self.assertTrue(all(not thread.is_alive() for thread in threads), "thread did not finish")
        return results

    def test_concurrent_sales_cannot_oversell_locked_inventory(self):
        Inventory.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("5"),
            min_quantity=Decimal("0"),
        )
        ProductBatch.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("5"),
            remaining_quantity=Decimal("5"),
            purchase_price=Decimal("100"),
            sale_price=Decimal("130"),
        )
        carts = [
            Cart.objects.create(user=self.user, store=self.store),
            Cart.objects.create(user=self.user, store=self.store),
        ]
        for cart in carts:
            CartItem.objects.create(
                cart=cart,
                product=self.product,
                quantity=Decimal("4"),
                unit_price=Decimal("130"),
                price_type="retail",
            )

        def checkout(index):
            CheckoutService.checkout(carts[index], [])

        results = self._run_threads(checkout)
        self.assertEqual(sum(status == "ok" for status, _ in results), 1)
        self.assertEqual(sum(status == "error" for status, _ in results), 1)
        self.assertIsInstance(next(exc for status, exc in results if status == "error"), ValidationError)

        inventory = Inventory.objects.get(product=self.product, store=self.store)
        batch = ProductBatch.objects.get(product=self.product, store=self.store)
        self.assertEqual(inventory.quantity, Decimal("1"))
        self.assertEqual(batch.remaining_quantity, Decimal("1"))
        self.assertEqual(Order.objects.filter(store=self.store, items__product=self.product).count(), 1)

    def test_concurrent_purchase_receives_serialize_inventory_creation(self):
        purchases = [self._purchase("5"), self._purchase("7")]

        def receive(index):
            PurchaseService.receive_purchase(purchases[index])

        results = self._run_threads(receive)
        self.assertEqual([status for status, _ in results].count("ok"), 2)

        inventory = Inventory.objects.get(product=self.product, store=self.store)
        self.assertEqual(inventory.quantity, Decimal("12"))
        self.assertEqual(ProductBatch.objects.filter(product=self.product, store=self.store).count(), 2)
        self.assertEqual(InventoryTransaction.objects.filter(
            product=self.product,
            store=self.store,
            transaction_type=InventoryTransaction.TYPE_PURCHASE,
        ).count(), 2)

    def test_concurrent_cashbox_settlement_preserves_balance(self):
        Inventory.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("20"),
            min_quantity=Decimal("0"),
        )
        ProductBatch.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("20"),
            remaining_quantity=Decimal("20"),
            purchase_price=Decimal("50"),
            sale_price=Decimal("100"),
        )
        cashbox = CashBox.objects.create(name="611 Cash", store=self.store, balance=Decimal("0"))
        carts = [
            Cart.objects.create(user=self.user, store=self.store),
            Cart.objects.create(user=self.user, store=self.store),
        ]
        for cart in carts:
            CartItem.objects.create(
                cart=cart,
                product=self.product,
                quantity=Decimal("5"),
                unit_price=Decimal("100"),
                price_type="retail",
            )

        def checkout(index):
            CheckoutService.checkout(
                carts[index],
                [{"method": "cash", "amount": "500", "cashbox_id": cashbox.id}],
            )

        results = self._run_threads(checkout)
        self.assertEqual([status for status, _ in results].count("ok"), 2)
        cashbox.refresh_from_db()
        self.assertEqual(cashbox.balance, Decimal("1000.000"))

    def test_purchase_receive_rolls_back_inventory_batch_and_flag_on_failure(self):
        purchase = self._purchase("5")
        with patch.object(InventoryTransaction.objects, "create", side_effect=RuntimeError("ledger failure")):
            with self.assertRaises(RuntimeError):
                PurchaseService.receive_purchase(purchase)

        purchase.refresh_from_db()
        self.assertFalse(purchase.received)
        self.assertFalse(Inventory.objects.filter(product=self.product, store=self.store).exists())
        self.assertFalse(ProductBatch.objects.filter(purchase_item__purchase=purchase).exists())
        self.assertFalse(InventoryTransaction.objects.filter(reference_id=purchase.id).exists())

    def test_checkout_rolls_back_order_inventory_batch_and_payment_on_failure(self):
        Inventory.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("5"),
            min_quantity=Decimal("0"),
        )
        batch = ProductBatch.objects.create(
            product=self.product,
            store=self.store,
            quantity=Decimal("5"),
            remaining_quantity=Decimal("5"),
            purchase_price=Decimal("100"),
            sale_price=Decimal("130"),
        )
        cashbox = CashBox.objects.create(name="611 Cash Rollback", store=self.store, balance=Decimal("0"))
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=Decimal("2"),
            unit_price=Decimal("130"),
            price_type="retail",
        )

        with patch.object(InventoryTransaction.objects, "create", side_effect=RuntimeError("ledger failure")):
            with self.assertRaises(RuntimeError):
                CheckoutService.checkout(
                    cart,
                    [{"method": "cash", "amount": "260", "cashbox_id": cashbox.id}],
                )

        self.assertFalse(Order.objects.filter(store=self.store, items__product=self.product).exists())
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, Decimal("5"))
        batch.refresh_from_db()
        self.assertEqual(batch.remaining_quantity, Decimal("5"))
        cashbox.refresh_from_db()
        self.assertEqual(cashbox.balance, Decimal("0.000"))
        self.assertTrue(CartItem.objects.filter(cart=cart).exists())
