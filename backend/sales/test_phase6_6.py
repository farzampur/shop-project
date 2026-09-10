from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from core.models import Store
from accounts.models import UserStore
from products.models import Category, Product, Inventory
from .models import Cart, CartItem, CashBox
from .services import CheckoutService
from .views import SalesReportViewSet


class Phase66ReportTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.manager = User.objects.create_user(username="phase66-manager", password="pw")
        self.seller = User.objects.create_user(username="phase66-seller", password="pw")
        self.a = Store.objects.create(name="شعبه A", code="66-A")
        self.b = Store.objects.create(name="شعبه B", code="66-B")
        UserStore.objects.create(user=self.manager, store=self.a, role="manager")
        UserStore.objects.create(user=self.manager, store=self.b, role="manager")
        UserStore.objects.create(user=self.seller, store=self.a, role="seller")
        ca = Category.objects.create(name="A", store=self.a)
        cb = Category.objects.create(name="B", store=self.b)
        self.pa = Product.objects.create(name="کالای A", barcode="660000000001", category=ca, purchase_price=10, sale_price=20)
        self.pb = Product.objects.create(name="کالای B", barcode="660000000002", category=cb, purchase_price=15, sale_price=30)
        Inventory.objects.create(product=self.pa, store=self.a, quantity=10, min_quantity=3)
        Inventory.objects.create(product=self.pb, store=self.b, quantity=2, min_quantity=5)
        self.cash = CashBox.objects.create(store=self.a, name="صندوق A", balance=0)
        cart = Cart.objects.create(user=self.seller, store=self.a)
        CartItem.objects.create(cart=cart, product=self.pa, quantity=2, unit_price=20)
        CheckoutService.checkout(cart, [{"method": "cash", "amount": Decimal("40"), "cashbox_id": self.cash.id}])

    def _get(self, action, user, params=None):
        request = self.factory.get("/api/sales/sales-report/", params or {})
        force_authenticate(request, user=user)
        return SalesReportViewSet.as_view({"get": action})(request)

    def test_store_comparison_is_manager_only_and_isolated(self):
        response = self._get("store_comparison", self.manager)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["store_id"], self.a.id)

    def test_inventory_overview_never_leaks_inaccessible_store(self):
        response = self._get("inventory_overview", self.seller)
        self.assertEqual(response.status_code, 200)
        self.assertEqual({x["store_id"] for x in response.data}, {self.a.id})

    def test_low_stock_respects_store_isolation(self):
        response = self._get("low_stock", self.seller)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(x["store_id"] == self.a.id for x in response.data))

    def test_seller_performance_reports_only_accessible_store(self):
        response = self._get("seller_performance", self.seller)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["store_id"], self.a.id)
        self.assertEqual(response.data[0]["user__username"], self.seller.username)
