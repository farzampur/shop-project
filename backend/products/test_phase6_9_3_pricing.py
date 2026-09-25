from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Category, Inventory, Product, ProductBatch, ProductPrice,
    Purchase, PurchaseItem, Supplier,
)
from products.pricing import get_effective_sale_price
from products.serializers import ProductPriceSerializer


class Phase693RetailPricingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="p693-pricing-manager", password="pw")
        self.store = Store.objects.create(name="P693 Pricing Store", code="P693-P")
        UserStore.objects.create(user=self.user, store=self.store, role="manager")
        self.category = Category.objects.create(name="P693 Pricing Cat", store=self.store)
        self.product = Product.objects.create(
            name="P693 Pricing Product", barcode="9234567890456",
            category=self.category,
        )
        Inventory.objects.create(product=self.product, store=self.store, quantity=Decimal("10"), min_quantity=Decimal("1"))
        self.supplier = Supplier.objects.create(store=self.store, name="P693 Supplier")

    def _batch(self, quantity, buy, sell, received_at=None):
        purchase = Purchase.objects.create(store=self.store, supplier=self.supplier, user=self.user, received=True)
        item = PurchaseItem.objects.create(
            purchase=purchase, product=self.product, quantity=Decimal(quantity),
            unit_price=Decimal(buy), sale_price=Decimal(sell),
        )
        kwargs = {"received_at": received_at} if received_at else {}
        return ProductBatch.objects.create(
            purchase_item=item, product=self.product, store=self.store,
            quantity=Decimal(quantity), remaining_quantity=Decimal(quantity),
            purchase_price=Decimal(buy), sale_price=Decimal(sell), **kwargs,
        )

    def test_active_retail_product_price_cannot_override_active_batch(self):
        self._batch("5", "50", "80")
        now = timezone.now()
        ProductPrice.objects.create(
            product=self.product, store=self.store, price_type=ProductPrice.TYPE_RETAIL,
            amount=Decimal("200"), effective_from=now - timedelta(minutes=1), created_by=self.user,
        )
        self.assertEqual(get_effective_sale_price(self.product, self.store.id, at=now), Decimal("80"))

    def test_retail_price_switches_to_next_batch_after_current_batch_is_exhausted(self):
        now = timezone.now()
        first = self._batch("5", "50", "80", received_at=now - timedelta(seconds=2))
        second = self._batch("7", "60", "95", received_at=now - timedelta(seconds=1))
        ProductPrice.objects.create(
            product=self.product, store=self.store, price_type=ProductPrice.TYPE_RETAIL,
            amount=Decimal("200"), effective_from=timezone.now() - timedelta(minutes=1), created_by=self.user,
        )
        self.assertEqual(get_effective_sale_price(self.product, self.store.id), Decimal("80"))
        first.remaining_quantity = Decimal("0")
        first.save(update_fields=["remaining_quantity", "updated_at"])
        self.assertEqual(get_effective_sale_price(self.product, self.store.id), Decimal("95"))
        self.assertEqual(second.remaining_quantity, Decimal("7"))

    def test_retail_price_is_none_without_sellable_batch(self):
        ProductPrice.objects.create(
            product=self.product, store=self.store, price_type=ProductPrice.TYPE_RETAIL,
            amount=Decimal("120"), created_by=self.user,
        )
        self.assertIsNone(get_effective_sale_price(self.product, self.store.id))

    def test_product_price_serializer_still_supports_wholesale_and_special(self):
        now = timezone.now()
        for price_type, amount in ((ProductPrice.TYPE_WHOLESALE, Decimal("70")), (ProductPrice.TYPE_SPECIAL, Decimal("75"))):
            serializer = ProductPriceSerializer(data={
                "product": self.product.id, "store": self.store.id, "price_type": price_type,
                "amount": str(amount), "effective_from": now.isoformat(), "is_active": True,
            })
            self.assertTrue(serializer.is_valid(), serializer.errors)
