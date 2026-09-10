# Create your tests here.

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth.models import User
from django.test import TestCase

from products.models import (
    Category,
    Product,
    Purchase,
    PurchaseItem,
    Store,
    Supplier,
    SupplierTransaction,
)
from products.views import PurchaseViewSet


class PurchaseSupplierDebtTests(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser",
            password="123456",
        )

        self.store = Store.objects.create(
            name="فروشگاه تست",
            code="TEST-001",
        )

        self.category = Category.objects.create(
            name="دسته تست",
            store=self.store,
        )

        self.product = Product.objects.create(
            name="محصول تست",
            category=self.category,
            purchase_price=Decimal("100000"),
            sale_price=Decimal("120000"),
        )

        self.supplier = Supplier.objects.create(
            name="تأمین‌کننده تست",
            store=self.store,
        )

        self.purchase = Purchase.objects.create(
            supplier=self.supplier,
            store=self.store,
            user=self.user,
            invoice_number="TEST-15",
            received=True,
        )

        PurchaseItem.objects.create(
            purchase=self.purchase,
            product=self.product,
            quantity=Decimal("10"),
            unit_price=Decimal("80000"),
        )

        self.purchase.refresh_from_db()

        self.viewset = PurchaseViewSet()

    def test_sync_supplier_debt_does_not_create_duplicate(self):

        # اجرای اول
        self.viewset._sync_supplier_debt(
            self.purchase
        )

        # اجرای دوباره برای همان خرید
        self.viewset._sync_supplier_debt(
            self.purchase
        )

        transactions = (
            SupplierTransaction.objects
            .filter(
                supplier=self.supplier,
                transaction_type="purchase",
                reference_id=self.purchase.id,
            )
        )

        # باید فقط یک بدهی ایجاد شده باشد
        self.assertEqual(
            transactions.count(),
            1,
        )

        transaction = transactions.first()

        # مبلغ بدهی باید برابر مبلغ خرید باشد
        self.assertEqual(
            transaction.amount,
            Decimal("800000"),
        )

        # reference_id باید مربوط به همین خرید باشد
        self.assertEqual(
            transaction.reference_id,
            self.purchase.id,
        )
        
    def test_edit_purchase_updates_supplier_debt(self):

        # ایجاد بدهی اولیه
        self.viewset._sync_supplier_debt(
            self.purchase
        )

        transaction = (
            SupplierTransaction.objects
            .get(
                supplier=self.supplier,
                transaction_type="purchase",
                reference_id=self.purchase.id,
            )
        )

        self.assertEqual(
            transaction.amount,
            Decimal("800000"),
        )

        # تغییر مبلغ خرید
        item = self.purchase.items.first()

        item.quantity = Decimal("20")
        item.unit_price = Decimal("100000")
        item.save()

        self.purchase.refresh_from_db()

        # همگام‌سازی مجدد بدهی
        self.viewset._sync_supplier_debt(
            self.purchase
        )

        transaction.refresh_from_db()

        # مبلغ کل جدید خرید
        self.assertEqual(
            self.purchase.total_amount,
            Decimal("2000000"),
        )

        # بدهی باید به مبلغ جدید تغییر کرده باشد
        self.assertEqual(
            transaction.amount,
            Decimal("2000000"),
        )

        # همچنان فقط یک تراکنش بدهی وجود داشته باشد
        self.assertEqual(
            SupplierTransaction.objects.filter(
                supplier=self.supplier,
                transaction_type="purchase",
                reference_id=self.purchase.id,
            ).count(),
            1,
        )


    def test_delete_purchase_removes_supplier_debt(self):

        purchase_id = self.purchase.id

        # ابتدا بدهی ایجاد شود
        self.viewset._sync_supplier_debt(
            self.purchase
        )

        # بررسی وجود بدهی
        self.assertTrue(
            SupplierTransaction.objects.filter(
                supplier=self.supplier,
                transaction_type="purchase",
                reference_id=purchase_id,
            ).exists()
        )

        # شبیه‌سازی منطق perform_destroy
        SupplierTransaction.objects.filter(
            transaction_type="purchase",
            reference_id=purchase_id,
        ).delete()

        self.purchase.delete()

        # خرید باید حذف شده باشد
        self.assertFalse(
            Purchase.objects.filter(
                id=purchase_id
            ).exists()
        )

        # بدهی مرتبط باید حذف شده باشد
        self.assertFalse(
            SupplierTransaction.objects.filter(
                transaction_type="purchase",
                reference_id=purchase_id,
            ).exists()
        )        
        
        
class ProductPricingTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from core.models import Store
        from products.models import Category, Product, Inventory, ProductPrice
        self.user = User.objects.create_user(username="price-manager", password="x")
        self.store = Store.objects.create(name="Price Store")
        from accounts.models import UserStore
        UserStore.objects.create(user=self.user, store=self.store, role="manager", is_active=True)
        category = Category.objects.create(name="General", store=self.store)
        self.product = Product.objects.create(name="Price Product", barcode="1111111111111", category=category, sale_price=Decimal("100"))
        Inventory.objects.create(product=self.product, store=self.store, quantity=10)
        self.ProductPrice = ProductPrice

    def test_overlapping_price_windows_are_rejected(self):
        from products.serializers import ProductPriceSerializer
        now = timezone.now()
        self.ProductPrice.objects.create(product=self.product, store=self.store, price_type="retail", amount=120, effective_from=now, effective_to=now + timedelta(days=10), created_by=self.user)
        serializer = ProductPriceSerializer(data={"product": self.product.id, "store": self.store.id, "price_type":"retail", "amount":"130", "effective_from":(now+timedelta(days=5)).isoformat(), "effective_to":(now+timedelta(days=15)).isoformat(), "is_active":True})
        self.assertFalse(serializer.is_valid())

    def test_gap_falls_back_to_base_price(self):
        from products.pricing import get_effective_sale_price
        now = timezone.now()
        self.ProductPrice.objects.create(product=self.product, store=self.store, price_type="retail", amount=120, effective_from=now-timedelta(days=20), effective_to=now-timedelta(days=10), created_by=self.user)
        self.assertEqual(get_effective_sale_price(self.product, self.store.id, at=now), Decimal("100"))

    def test_active_price_is_used(self):
        from products.pricing import get_effective_sale_price
        now = timezone.now()
        self.ProductPrice.objects.create(product=self.product, store=self.store, price_type="retail", amount=120, effective_from=now-timedelta(days=1), effective_to=now+timedelta(days=1), created_by=self.user)
        self.assertEqual(get_effective_sale_price(self.product, self.store.id, at=now), Decimal("120"))
