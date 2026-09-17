from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Store
from .models import Category, Product, Supplier, Purchase, PurchaseReturn, StockTransfer, StockTransferItem


class DocumentIntegrity611Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="611 Store", code="611")
        self.store2 = Store.objects.create(name="611 Store 2", code="611-2")
        self.user = User.objects.create_user(username="611", password="x")
        self.category = Category.objects.create(store=self.store, name="611 Cat")
        self.product = Product.objects.create(category=self.category, name="611 Product", barcode="61101")
        self.supplier = Supplier.objects.create(store=self.store, name="611 Supplier")
        self.purchase = Purchase.objects.create(store=self.store, user=self.user, supplier=self.supplier)

    def assert_db_rejects(self, model, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                model.objects.create(**kwargs)

    def test_purchase_total_amount_cannot_be_negative(self):
        self.assert_db_rejects(Purchase, store=self.store, user=self.user, supplier=self.supplier, total_amount=-1)

    def test_purchase_return_values_cannot_be_invalid(self):
        base = dict(purchase=self.purchase, product=self.product, created_by=self.user, unit_price=10)
        self.assert_db_rejects(PurchaseReturn, **base, quantity=0)
        self.assert_db_rejects(PurchaseReturn, **{**base, "unit_price": -1}, quantity=1)
        # PurchaseReturn.save() derives total_amount from quantity * unit_price,
        # so passing total_amount=-1 to objects.create() is intentionally overwritten.
        # Exercise the database CHECK directly via UPDATE instead.
        valid_return = PurchaseReturn.objects.create(**base, quantity=1)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PurchaseReturn.objects.filter(pk=valid_return.pk).update(total_amount=-1)

    def test_stock_transfer_cannot_have_same_source_and_destination(self):
        self.assert_db_rejects(
            StockTransfer,
            source_store=self.store,
            destination_store=self.store,
            created_by=self.user,
        )

    def test_stock_transfer_item_quantity_must_be_positive(self):
        transfer = StockTransfer.objects.create(
            source_store=self.store, destination_store=self.store2, created_by=self.user
        )
        self.assert_db_rejects(StockTransferItem, transfer=transfer, product=self.product, quantity=0)
