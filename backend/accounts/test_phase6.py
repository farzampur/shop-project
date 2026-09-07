from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import UserStore
from core.models import Store


class Phase6UserManagementTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="manager6", password="pass12345")
        self.other = User.objects.create_user(username="other6", password="pass12345")
        self.store_a = Store.objects.create(name="شعبه یک", code="P6-A")
        self.store_b = Store.objects.create(name="شعبه دو", code="P6-B")
        UserStore.objects.create(user=self.manager, store=self.store_a, role="manager")
        UserStore.objects.create(user=self.other, store=self.store_b, role="manager")
        UserStore.objects.create(user=self.manager, store=self.store_b, role="cashier", is_active=False)
        self.client = APIClient()
        self.client.force_authenticate(self.manager)

    def test_manager_sees_only_managed_store_users(self):
        response = self.client.get(f"/api/accounts/store-users/?store={self.store_a.id}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(row["store"] == self.store_a.id for row in response.data))
        self.assertFalse(any(row["store"] == self.store_b.id for row in response.data))

    def test_manager_can_create_employee_in_managed_store(self):
        response = self.client.post("/api/accounts/store-users/", {"username": "seller6", "password": "pass12345", "first_name": "فروشنده", "role": "seller", "store": self.store_a.id}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], "seller")
        self.assertTrue(UserStore.objects.filter(user__username="seller6", store=self.store_a, is_active=True).exists())

    def test_manager_cannot_manage_other_store(self):
        response = self.client.patch(f"/api/accounts/store-users/{UserStore.objects.get(user=self.other, store=self.store_b).id}/", {"role": "cashier"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_manager_can_change_role_and_active_state(self):
        relation = UserStore.objects.create(user=User.objects.create_user(username="seller6b", password="pass12345"), store=self.store_a, role="seller")
        response = self.client.patch(f"/api/accounts/store-users/{relation.id}/", {"role": "warehouse", "is_active": False}, format="json")
        self.assertEqual(response.status_code, 200)
        relation.refresh_from_db()
        self.assertEqual(relation.role, "warehouse")
        self.assertFalse(relation.is_active)


class Phase6StoreManagementTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="manager-store6", password="pass12345")
        self.store = Store.objects.create(name="شعبه مدیریت", code="P6-S")
        UserStore.objects.create(user=self.manager, store=self.store, role="manager")
        self.client = APIClient()
        self.client.force_authenticate(self.manager)

    def test_manager_can_update_own_store(self):
        response = self.client.patch(f"/api/stores/{self.store.id}/", {"phone": "021123456"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.store.refresh_from_db()
        self.assertEqual(self.store.phone, "021123456")

    def test_manager_cannot_create_store(self):
        response = self.client.post("/api/stores/", {"name": "شعبه جدید", "code": "P6-NEW"}, format="json")
        self.assertEqual(response.status_code, 403)

