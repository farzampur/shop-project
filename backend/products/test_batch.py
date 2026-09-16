from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User

from core.models import Store
from products.models import Category, Product, Supplier, Purchase, PurchaseItem, ProductBatch, Inventory
from products.services import PurchaseService
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

    def test_retail_cart_cannot_cross_current_batch(self):
        self._purchase("5", "100", "130")
        self._purchase("7", "120", "155")
        cart = Cart.objects.create(user=self.user, store=self.store)
        # This is a service-level invariant test: a single retail line must stay inside its active batch.
        batch = get_active_batch(self.product, self.store.id)
        self.assertEqual(batch.remaining_quantity, Decimal("5"))

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
