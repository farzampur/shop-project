from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from core.models import Store
from products.models import Category, Product, Supplier, Purchase, PurchaseItem, ProductBatch, Inventory
from products.services import PurchaseService
from sales.models import OrderItemBatch
from rest_framework.exceptions import ValidationError
from products.pricing import get_active_batch, get_effective_sale_price
from sales.models import Cart, CartItem
from sales.services import CheckoutService


class ProductBatchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="batch-user", password="pass")
        self.store = Store.objects.create(name="Batch Store", code="BATCH01")
        self.category = Category.objects.create(name="کالا", store=self.store)
        self.product = Product.objects.create(name="محصول بچی", barcode="660000009999", category=self.category, unit="عدد")
        self.supplier = Supplier.objects.create(store=self.store, name="تامین‌کننده بچ")

    def _purchase(self, qty, buy, sell, received=True):
        purchase = Purchase.objects.create(supplier=self.supplier, store=self.store, user=self.user, received=False)
        PurchaseItem.objects.create(
            purchase=purchase, product=self.product, quantity=Decimal(qty),
            unit_price=Decimal(buy), sale_price=Decimal(sell)
        )
        purchase.refresh_from_db()
        if received:
            PurchaseService.receive_purchase(purchase)
        return purchase

    def test_received_purchase_creates_batch_with_purchase_and_sale_price(self):
        purchase = self._purchase("10", "100", "130")
        batch = ProductBatch.objects.get(purchase_item__purchase=purchase)
        self.assertEqual(batch.quantity, Decimal("10"))
        self.assertEqual(batch.remaining_quantity, Decimal("10"))
        self.assertEqual(batch.purchase_price, Decimal("100"))
        self.assertEqual(batch.sale_price, Decimal("130"))
        self.assertEqual(get_effective_sale_price(self.product, self.store.id), Decimal("130"))

    def test_active_sale_price_switches_after_old_batch_is_exhausted(self):
        first = self._purchase("5", "100", "130")
        second = self._purchase("7", "120", "155")
        first_batch = ProductBatch.objects.get(purchase_item__purchase=first)
        second_batch = ProductBatch.objects.get(purchase_item__purchase=second)
        self.assertEqual(get_active_batch(self.product, self.store.id).id, first_batch.id)
        first_batch.remaining_quantity = Decimal("0")
        first_batch.save(update_fields=["remaining_quantity", "updated_at"])
        self.assertEqual(get_active_batch(self.product, self.store.id).id, second_batch.id)
        self.assertEqual(get_effective_sale_price(self.product, self.store.id), Decimal("155"))

    def test_retail_sale_can_cross_batches_and_uses_each_batch_sale_price(self):
        self._purchase("5", "100", "130")
        self._purchase("7", "120", "155")
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("7"),
            unit_price=Decimal("130"), price_type="retail"
        )

        order = CheckoutService.checkout(cart, [])
        items = list(order.items.order_by("id"))

        self.assertEqual(
            [(i.quantity, i.unit_price, i.purchase_price) for i in items],
            [
                (Decimal("5"), Decimal("130"), Decimal("100")),
                (Decimal("2"), Decimal("155"), Decimal("120")),
            ],
        )
        self.assertEqual(order.total_price, Decimal("960"))
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, Decimal("5"))

    def test_fifo_allocation_is_shared_across_retail_and_wholesale_lines(self):
        self._purchase("9", "100", "130")
        self._purchase("7", "120", "155")

        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("4"),
            unit_price=Decimal("130"), price_type="retail"
        )
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("5"),
            unit_price=Decimal("110"), price_type="wholesale"
        )

        order = CheckoutService.checkout(cart, [])
        allocations = list(
            order.items.order_by("id").values_list(
                "price_type", "quantity", "purchase_price"
            )
        )
        self.assertEqual(
            allocations,
            [
                ("retail", Decimal("4"), Decimal("100")),
                ("wholesale", Decimal("5"), Decimal("100")),
            ],
        )

        first = ProductBatch.objects.order_by("received_at", "id").first()
        self.assertEqual(first.remaining_quantity, Decimal("0"))

    def test_wholesale_sale_spans_batches_and_snapshots_weighted_cost(self):
        self._purchase("5", "100", "130")
        self._purchase("7", "120", "155")
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("8"),
            unit_price=Decimal("110"), price_type="wholesale"
        )

        order = CheckoutService.checkout(cart, [])
        item = order.items.get(product=self.product)

        self.assertEqual(item.quantity, Decimal("8"))
        self.assertEqual(item.unit_price, Decimal("110"))
        # FIFO COGS snapshot is the quantity-weighted average of the allocated batches:
        # (5*100 + 3*120) / 8 = 107.50.
        self.assertEqual(item.purchase_price, Decimal("107.50"))
        allocations = list(
            OrderItemBatch.objects.filter(order_item=item)
            .order_by("id")
            .values_list("quantity", "batch__purchase_price")
        )
        self.assertEqual(
            allocations,
            [(Decimal("5"), Decimal("100")), (Decimal("3"), Decimal("120"))],
        )

    def test_sale_rejects_when_batch_stock_is_less_than_inventory(self):
        self._purchase("5", "100", "130")
        inventory = Inventory.objects.get(product=self.product, store=self.store)
        inventory.quantity = Decimal("8")
        inventory.save(update_fields=["quantity", "updated_at"])

        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=Decimal("6"),
            unit_price=Decimal("130"), price_type="retail"
        )

        with self.assertRaises(ValidationError):
            CheckoutService.checkout(cart, [])

        self.assertEqual(ProductBatch.objects.get(purchase_item__purchase__items__product=self.product).remaining_quantity, Decimal("5"))
        self.assertEqual(Inventory.objects.get(product=self.product, store=self.store).quantity, Decimal("8"))

    def test_sale_consumes_fifo_batch_and_snapshots_cost(self):
        self._purchase("5", "100", "130")
        self._purchase("7", "120", "155")
        cart = Cart.objects.create(user=self.user, store=self.store)
        CartItem.objects.create(cart=cart, product=self.product, quantity=Decimal("5"), unit_price=Decimal("130"), price_type="retail")
        order = CheckoutService.checkout(cart, [])
        item = order.items.get(product=self.product)
        self.assertEqual(item.purchase_price, Decimal("100"))
        first = ProductBatch.objects.order_by("received_at", "id").first()
        self.assertEqual(first.remaining_quantity, Decimal("0"))
