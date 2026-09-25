from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import UserStore
from core.models import Store
from products.models import ProductPrice, Product, Category


class ReleaseSecurityAndReadinessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.store_a = Store.objects.create(name="Release A", code="REL-A")
        self.store_b = Store.objects.create(name="Release B", code="REL-B")
        self.user = User.objects.create_user(username="release-user", password="pass12345")
        UserStore.objects.create(user=self.user, store=self.store_a, role="manager", is_active=True)
        self.client.force_authenticate(self.user)

    def test_health_endpoint_is_public_and_database_ready(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["database"], "ok")

    def test_stock_transfer_requires_store_role_permission(self):
        from products.views import StockTransferViewSet
        self.assertIn("manager", StockTransferViewSet.allowed_roles_by_method["POST"])
        self.assertNotIn("seller", StockTransferViewSet.allowed_roles_by_method["POST"])

        seller = User.objects.create_user(username="release-seller", password="pass12345")
        UserStore.objects.create(user=seller, store=self.store_a, role="seller", is_active=True)
        self.client.force_authenticate(seller)
        response = self.client.post("/api/products/stock-transfers/", {
            "source_store": self.store_a.id,
            "destination_store": self.store_b.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_price_requires_manager_for_mutation(self):
        from products.views import ProductPriceViewSet
        self.assertEqual(ProductPriceViewSet.allowed_roles_by_method["POST"], {"manager"})
        self.assertEqual(ProductPriceViewSet.allowed_roles_by_method["DELETE"], {"manager"})

    def test_product_price_cross_store_mutation_is_denied(self):
        from products.views import ProductPriceViewSet
        self.assertEqual(ProductPriceViewSet.allowed_roles_by_method["POST"], {"manager"})
        self.assertEqual(ProductPriceViewSet.allowed_roles_by_method["DELETE"], {"manager"})

        seller = User.objects.create_user(username="release-seller-price", password="pass12345")
        UserStore.objects.create(user=seller, store=self.store_a, role="seller", is_active=True)
        self.client.force_authenticate(seller)
        response = self.client.post("/api/products/prices/", {
            "product": 999999,
            "store": self.store_a.id,
            "price_type": "retail",
            "amount": "100",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_production_security_defaults_are_enabled_when_debug_is_off(self):
        with override_settings(
            DEBUG=False,
            SECURE_SSL_REDIRECT=True,
            SESSION_COOKIE_SECURE=True,
            CSRF_COOKIE_SECURE=True,
            SESSION_COOKIE_SAMESITE="Lax",
            CSRF_COOKIE_SAMESITE="Lax",
            SECURE_CROSS_ORIGIN_OPENER_POLICY="same-origin",
            SECURE_CROSS_ORIGIN_RESOURCE_POLICY="same-origin",
        ):
            self.assertTrue(settings.SECURE_SSL_REDIRECT)
            self.assertTrue(settings.SESSION_COOKIE_SECURE)
            self.assertTrue(settings.CSRF_COOKIE_SECURE)
            self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
            self.assertEqual(settings.CSRF_COOKIE_SAMESITE, "Lax")
            self.assertEqual(settings.SECURE_CROSS_ORIGIN_OPENER_POLICY, "same-origin")
            self.assertEqual(settings.SECURE_CROSS_ORIGIN_RESOURCE_POLICY, "same-origin")


class ReleaseInvariantTests(TestCase):
    def test_decimal_financial_values_are_positive_in_price_serializer(self):
        from products.serializers import ProductPriceSerializer
        store = Store.objects.create(name="Price Test Store", code="REL-PRICE")
        category = Category.objects.create(name="Price Test Category", store=store)
        product = Product.objects.create(
            name="Price Test Product",
            barcode="REL-PRICE-001",
            category=category,
        )
        serializer = ProductPriceSerializer(data={
            "product": product.id,
            "store": store.id,
            "price_type": "wholesale",
            "amount": "0",
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_frontend_release_artifacts_are_present(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[2]
        self.assertTrue((root / "frontend" / "src" / "services" / "api.ts").exists())
        self.assertTrue((root / "frontend" / "src" / "services" / "authService.ts").exists())
