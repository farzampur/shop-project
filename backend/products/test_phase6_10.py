from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.parsers import JSONParser
from rest_framework.test import APIRequestFactory

from accounts.models import UserStore
from accounts.permissions import StoreRolePermission
from core.models import Store
from products.models import Category, Product, Supplier, Purchase, PurchaseItem, Inventory
from products.serializers import (
    CategorySerializer,
    ProductSerializer,
    SupplierSerializer,
    PurchaseSerializer,
    PurchaseItemSerializer,
    ProductPriceSerializer,
)
from sales.models import CashBox, Order, Customer
from sales.serializers import CashBoxSerializer, CustomerSerializer
from products.models import ProductPrice


class AccessControl610Tests(TestCase):
    """Phase 6.10: store isolation, role authorization and ID-tampering regression tests."""

    def setUp(self):
        self.manager = User.objects.create_user(username="m610m", password="pass12345")
        self.seller = User.objects.create_user(username="m610s", password="pass12345")
        self.warehouse = User.objects.create_user(username="m610w", password="pass12345")
        self.cashier = User.objects.create_user(username="m610c", password="pass12345")
        self.other = User.objects.create_user(username="m610o", password="pass12345")

        self.store_a = Store.objects.create(name="610 A", code="610A")
        self.store_b = Store.objects.create(name="610 B", code="610B")

        UserStore.objects.create(user=self.manager, store=self.store_a, role="manager")
        UserStore.objects.create(user=self.seller, store=self.store_a, role="seller")
        UserStore.objects.create(user=self.warehouse, store=self.store_a, role="warehouse")
        UserStore.objects.create(user=self.cashier, store=self.store_a, role="cashier")
        UserStore.objects.create(user=self.other, store=self.store_b, role="manager")

        self.cat_a = Category.objects.create(name="610 Cat A", store=self.store_a)
        self.cat_b = Category.objects.create(name="610 Cat B", store=self.store_b)
        self.product = Product.objects.create(name="610 Product", barcode="6100000000001", category=self.cat_a)
        self.product_b = Product.objects.create(name="610 Product B", barcode="6100000000002", category=self.cat_b)
        self.supplier_a = Supplier.objects.create(store=self.store_a, name="610 Supplier A")
        self.supplier_b = Supplier.objects.create(store=self.store_b, name="610 Supplier B")
        self.cash_a = CashBox.objects.create(store=self.store_a, name="610 Cash A")
        self.cash_b = CashBox.objects.create(store=self.store_b, name="610 Cash B")

    def serializer(self, cls, instance=None, data=None):
        return cls(instance=instance, data=data, partial=True, context={"request": None})

    def test_category_cannot_be_moved_between_stores(self):
        ser = self.serializer(CategorySerializer, self.cat_a, {"store": self.store_b.id})
        self.assertFalse(ser.is_valid())
        self.assertIn("store", ser.errors)

    def test_product_cannot_change_to_category_of_another_store(self):
        ser = self.serializer(ProductSerializer, self.product, {"category": self.cat_b.id, "name": "changed"})
        self.assertFalse(ser.is_valid())
        self.assertIn("category", ser.errors)

    def test_supplier_cannot_be_moved_between_stores(self):
        ser = self.serializer(SupplierSerializer, self.supplier_a, {"store": self.store_b.id})
        self.assertFalse(ser.is_valid())
        self.assertIn("store", ser.errors)

    def test_purchase_cannot_be_moved_between_stores(self):
        purchase = Purchase.objects.create(store=self.store_a, user=self.manager, supplier=self.supplier_a)
        ser = self.serializer(PurchaseSerializer, purchase, {"store": self.store_b.id, "supplier": self.supplier_b.id})
        self.assertFalse(ser.is_valid())
        self.assertIn("store", ser.errors)

    def test_purchase_item_cannot_switch_to_product_from_another_store(self):
        purchase = Purchase.objects.create(store=self.store_a, user=self.manager, supplier=self.supplier_a)
        item = PurchaseItem.objects.create(purchase=purchase, product=self.product, quantity=1, unit_price=10, total_price=10)
        ser = self.serializer(PurchaseItemSerializer, item, {"product": self.product_b.id, "quantity": 1, "unit_price": 10})
        self.assertFalse(ser.is_valid())
        self.assertIn("product", ser.errors)

    def test_cashbox_cannot_be_moved_between_stores(self):
        ser = self.serializer(CashBoxSerializer, self.cash_a, {"store": self.store_b.id})
        self.assertFalse(ser.is_valid())
        self.assertIn("store", ser.errors)

    def test_product_price_record_cannot_be_moved_between_stores(self):
        Inventory.objects.create(product=self.product, store=self.store_a, quantity=1)
        price = ProductPrice.objects.create(
            product=self.product, store=self.store_a, price_type=ProductPrice.TYPE_WHOLESALE,
            amount=10, created_by=self.manager,
        )
        ser = self.serializer(ProductPriceSerializer, price, {"store": self.store_b.id})
        self.assertFalse(ser.is_valid())
        self.assertIn("store", ser.errors)

    def test_store_role_permission_is_store_specific(self):
        factory = APIRequestFactory()
        permission = StoreRolePermission()
        view = type("V", (), {"allowed_roles_by_method": {"POST": {"manager", "warehouse"}}})()

        request_a = Request(factory.post("/x", {"store": self.store_a.id}, format="json"), parsers=[JSONParser()])
        request_a.user = self.warehouse
        self.assertTrue(permission.has_permission(request_a, view))

        request_b = Request(factory.post("/x", {"store": self.store_b.id}, format="json"), parsers=[JSONParser()])
        request_b.user = self.warehouse
        self.assertFalse(permission.has_permission(request_b, view))

    def test_role_matrix_rejects_seller_write_and_allows_warehouse_write(self):
        factory = APIRequestFactory()
        permission = StoreRolePermission()
        view = type("V", (), {"allowed_roles_by_method": {"POST": {"manager", "warehouse"}}})()

        seller_request = Request(factory.post("/x", {"store": self.store_a.id}, format="json"), parsers=[JSONParser()])
        seller_request.user = self.seller
        self.assertFalse(permission.has_permission(seller_request, view))

        warehouse_request = Request(factory.post("/x", {"store": self.store_a.id}, format="json"), parsers=[JSONParser()])
        warehouse_request.user = self.warehouse
        self.assertTrue(permission.has_permission(warehouse_request, view))

    def test_customer_store_cannot_be_changed(self):
        customer = Customer.objects.create(store=self.store_a, first_name="610 Customer", mobile="0610000000")
        ser = self.serializer(CustomerSerializer, customer, {"store": self.store_b.id})
        self.assertFalse(ser.is_valid())
        self.assertIn("store", ser.errors)

    def test_object_scoped_financial_records_do_not_cross_store(self):
        from sales.views import CashBoxViewSet
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = Request(factory.get("/api/sales/cashboxes/", {"store": self.store_a.id}))
        request.user = self.manager
        view = CashBoxViewSet()
        view.request = request
        qs = view.get_queryset()
        self.assertTrue(qs.filter(pk=self.cash_a.pk).exists())
        self.assertFalse(qs.filter(pk=self.cash_b.pk).exists())
