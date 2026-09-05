from .models import UserStore
from core.models import Store
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.test import TestCase

# Create your tests here.


class MeEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="me-user", password="password123")
        self.store_a = Store.objects.create(name="Store A", code="ME-A")
        self.store_b = Store.objects.create(name="Store B", code="ME-B")
        UserStore.objects.create(user=self.user, store=self.store_a, role="manager")
        UserStore.objects.create(user=self.user, store=self.store_b, role="cashier")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_me_returns_identity_and_store_roles(self):
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "me-user")
        self.assertEqual(
            [(item["id"], item["role"]) for item in response.data["stores"]],
            [(self.store_a.id, "manager"), (self.store_b.id, "cashier")],
        )

    def test_me_excludes_inactive_stores(self):
        self.store_b.is_active = False
        self.store_b.save(update_fields=["is_active"])
        response = self.client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data["stores"]], [self.store_a.id])
