from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase

from accounts.models import UserStore
from core.models import Store
from sales.models import Customer
from sales.models import Cart


class CartCustomerPatchPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="cashier685", password="pass12345")
        self.store = Store.objects.create(name="Store 685")
        UserStore.objects.create(user=self.user, store=self.store, role="cashier", is_active=True)
        self.customer = Customer.objects.create(
            store=self.store, first_name="مشتری", last_name="685", mobile="09126850000"
        )
        self.cart = Cart.objects.create(user=self.user, store=self.store)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_customer_only_patch_is_allowed_for_cart_store(self):
        response = self.client.patch(
            f"/api/sales/carts/{self.cart.id}/",
            {"customer": self.customer.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.customer_id, self.customer.id)
