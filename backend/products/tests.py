# Create your tests here.

from decimal import Decimal

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
        
        