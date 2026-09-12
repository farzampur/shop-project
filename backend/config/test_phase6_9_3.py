from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class JWTAuthenticationHardeningTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.username = "jwt-test-user"
        self.password = "StrongTestPassword123!"

        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def _login(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        return response.data

    def test_blacklisted_refresh_token_cannot_be_reused(self):
        tokens = self._login()
        refresh_token = tokens["refresh"]

        blacklist_response = self.client.post(
            reverse("token_blacklist"),
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            blacklist_response.status_code,
            status.HTTP_200_OK,
        )

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_refresh_rotation_returns_new_refresh_and_invalidates_old_one(self):
        tokens = self._login()
        old_refresh = tokens["refresh"]

        rotation_response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": old_refresh,
            },
            format="json",
        )

        self.assertEqual(
            rotation_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn("access", rotation_response.data)
        self.assertIn("refresh", rotation_response.data)

        new_refresh = rotation_response.data["refresh"]

        self.assertNotEqual(old_refresh, new_refresh)

        old_refresh_response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": old_refresh,
            },
            format="json",
        )

        self.assertEqual(
            old_refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        new_refresh_response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": new_refresh,
            },
            format="json",
        )

        self.assertEqual(
            new_refresh_response.status_code,
            status.HTTP_200_OK,
        )