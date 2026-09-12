from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.test import APIClient
from datetime import timedelta        


User = get_user_model()

REFRESH_COOKIE_NAME = "refresh_token"
CSRF_COOKIE_NAME = "csrftoken"


class JWTAuthenticationHardeningTests(TestCase):

    def setUp(self):
        self.client = APIClient(
            enforce_csrf_checks=True,
        )

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

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertNotIn(
            "refresh",
            response.data,
        )

        return response

    def _get_csrf_token(self):
        """
        Obtain a CSRF token from the dedicated CSRF endpoint
        and attach the cookie to the test client.
        """
        response = self.client.get(
            reverse("csrf_cookie"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        csrf_cookie = response.cookies.get(
            CSRF_COOKIE_NAME
        )

        self.assertIsNotNone(
            csrf_cookie,
        )

        csrf_token = csrf_cookie.value

        self.client.cookies[CSRF_COOKIE_NAME] = csrf_token

        return csrf_token

    def test_login_stores_refresh_token_in_httponly_cookie(self):
        response = self._login()

        self.assertIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )

        cookie = response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertTrue(
            cookie["httponly"]
        )

        self.assertEqual(
            cookie["samesite"],
            "Lax",
        )

        self.assertEqual(
            cookie["path"],
            "/api/auth/token/",
        )

        self.assertEqual(
            int(cookie["max-age"]),
            7 * 24 * 60 * 60,
        )

    def test_refresh_uses_cookie_and_rotates_refresh_token(self):
        login_response = self._login()

        old_refresh = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = old_refresh

        csrf_token = self._get_csrf_token()

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_200_OK,
            refresh_response.data,
        )

        self.assertIn(
            "access",
            refresh_response.data,
        )

        self.assertNotIn(
            "refresh",
            refresh_response.data,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            refresh_response.cookies,
        )

        new_refresh = refresh_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.assertNotEqual(
            old_refresh,
            new_refresh,
        )

    def test_old_refresh_cookie_is_blacklisted_after_rotation(self):
        login_response = self._login()

        old_refresh = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = old_refresh

        csrf_token = self._get_csrf_token()

        rotation_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            rotation_response.status_code,
            status.HTTP_200_OK,
            rotation_response.data,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            rotation_response.cookies,
        )

        new_refresh = rotation_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.assertNotEqual(
            old_refresh,
            new_refresh,
        )

        # Simulate reuse of the OLD refresh token.
        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = old_refresh

        old_refresh_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            old_refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            old_refresh_response.data,
        )

        # The rotated token must still be usable.
        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = new_refresh

        new_refresh_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            new_refresh_response.status_code,
            status.HTTP_200_OK,
            new_refresh_response.data,
        )

    def test_refresh_without_cookie_is_rejected(self):
        # Obtain a valid CSRF token first so that the request
        # reaches the refresh view instead of being rejected
        # by CsrfViewMiddleware.
        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_logout_blacklists_cookie_and_deletes_it(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token
        
        csrf_token = self._get_csrf_token()
        
        blacklist_response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,            
        )

        self.assertEqual(
            blacklist_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            blacklist_response.cookies,
        )

        deleted_cookie = blacklist_response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            int(deleted_cookie["max-age"]),
            0,
        )

    def test_refresh_cookie_is_secure_in_production(self):
        original_value = settings.REFRESH_COOKIE_SECURE

        try:
            settings.REFRESH_COOKIE_SECURE = True

            response = self._login()

            cookie = response.cookies[
                REFRESH_COOKIE_NAME
            ]

            self.assertTrue(
                cookie["secure"]
            )

        finally:
            settings.REFRESH_COOKIE_SECURE = original_value

    def test_refresh_cookie_can_be_insecure_in_development(self):
        original_value = settings.REFRESH_COOKIE_SECURE

        try:
            settings.REFRESH_COOKIE_SECURE = False

            response = self._login()

            cookie = response.cookies[
                REFRESH_COOKIE_NAME
            ]

            self.assertFalse(
                cookie["secure"]
            )

        finally:
            settings.REFRESH_COOKIE_SECURE = original_value

    def test_cors_allows_configured_origin_with_credentials(self):
        response = self.client.options(
            reverse("token_refresh"),
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.get("Access-Control-Allow-Origin"),
            "http://localhost:5173",
        )

        self.assertEqual(
            response.get("Access-Control-Allow-Credentials"),
            "true",
        )

    def test_cors_rejects_untrusted_origin(self):
        response = self.client.options(
            reverse("token_refresh"),
            HTTP_ORIGIN="https://evil.example.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        self.assertNotEqual(
            response.get("Access-Control-Allow-Origin"),
            "https://evil.example.com",
        )

    @override_settings(
        CSRF_TRUSTED_ORIGINS=[
            "http://localhost:5173",
        ],
    )
    def test_refresh_requires_csrf_token_for_trusted_origin(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_ORIGIN="http://localhost:5173",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.content,
        )

    def test_refresh_rejects_cross_site_origin_without_csrf(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_ORIGIN="https://evil.example.com",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.content,
        )

    @override_settings(
        CSRF_TRUSTED_ORIGINS=[
            "http://localhost:5173",
        ],
    )
    def test_refresh_with_valid_csrf_token_is_allowed(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            getattr(response, "data", None),
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertNotIn(
            "refresh",
            response.data,
        )
        
        
    @override_settings(
        CSRF_TRUSTED_ORIGINS=[
            "http://localhost:5173",
        ],
    )
    def test_logout_requires_csrf_token(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token

        response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_ORIGIN="http://localhost:5173",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            response.content,
        )        
        
    @override_settings(
        CSRF_TRUSTED_ORIGINS=[
            "http://localhost:5173",
        ],
    )
    def test_logout_with_valid_csrf_token_is_allowed(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )

        deleted_cookie = response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            int(deleted_cookie["max-age"]),
            0,
        )        
        
    def test_logout_with_malformed_refresh_cookie_does_not_return_500(self):
        csrf_token = self._get_csrf_token()

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = "malformed-refresh-token"

        response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )        
        
    def test_logout_with_malformed_refresh_cookie_deletes_it(self):
        csrf_token = self._get_csrf_token()

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = "malformed-refresh-token"

        response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )

        deleted_cookie = response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            int(deleted_cookie["max-age"]),
            0,
        )  

    def test_logout_with_expired_refresh_cookie_deletes_it(self):
        csrf_token = self._get_csrf_token()

        expired_refresh = RefreshToken.for_user(self.user)
        expired_refresh.set_exp(
            lifetime=timedelta(seconds=-1),
        )

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = str(expired_refresh)

        response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )

        deleted_cookie = response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            int(deleted_cookie["max-age"]),
            0,
        )        
        
    def test_refresh_token_replay_is_rejected_after_rotation(self):
        login_response = self._login()

        old_refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = old_refresh_token

        csrf_token = self._get_csrf_token()

        # First refresh: rotates the refresh token.
        first_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
            getattr(first_response, "data", None),
        )

        self.assertIn(
            "access",
            first_response.data,
        )

        self.assertNotIn(
            "refresh",
            first_response.data,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            first_response.cookies,
        )

        new_refresh_token = first_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.assertNotEqual(
            old_refresh_token,
            new_refresh_token,
        )

        # Replay the old refresh token.
        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = old_refresh_token

        replay_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            replay_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            replay_response.content,
        )

    
    def test_new_refresh_token_is_usable_after_rotation(self):
        login_response = self._login()

        old_refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = old_refresh_token

        csrf_token = self._get_csrf_token()

        # First refresh: rotate old refresh token.
        first_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
            getattr(first_response, "data", None),
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            first_response.cookies,
        )

        new_refresh_token = first_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.assertNotEqual(
            old_refresh_token,
            new_refresh_token,
        )

        # Use the newly rotated refresh token.
        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = new_refresh_token

        second_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_200_OK,
            getattr(second_response, "data", None),
        )

        self.assertIn(
            "access",
            second_response.data,
        )

        self.assertNotIn(
            "refresh",
            second_response.data,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            second_response.cookies,
        )

    def test_refresh_cookie_has_restricted_path(self):
        login_response = self._login()

        self.assertIn(
            REFRESH_COOKIE_NAME,
            login_response.cookies,
        )

        refresh_cookie = login_response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            refresh_cookie["path"],
            "/api/auth/token/",
        )    
        
    def test_refresh_cookie_is_httponly(self):
        login_response = self._login()

        cookie = login_response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            cookie["httponly"],
            True,
        )


    def test_refresh_cookie_samesite_is_lax(self):
        login_response = self._login()

        cookie = login_response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            cookie["samesite"].lower(),
            "lax",
        )


    def test_refresh_cookie_has_max_age(self):
        login_response = self._login()

        cookie = login_response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            int(cookie["max-age"]),
            7 * 24 * 60 * 60,
        )


    def test_login_response_does_not_expose_refresh_token(self):
        response = self._login()

        self.assertNotIn(
            "refresh",
            response.data,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )


    def test_refresh_response_does_not_expose_refresh_token(self):
        login_response = self._login()

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            getattr(response, "data", None),
        )

        self.assertNotIn(
            "refresh",
            response.data,
        )


    def test_refresh_without_refresh_cookie_is_rejected(self):
        csrf_token = self._get_csrf_token()

        self.client.cookies.pop(
            REFRESH_COOKIE_NAME,
            None,
        )

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            response.content,
        )        
        
    def test_refresh_with_malformed_cookie_is_rejected_without_500(self):
        csrf_token = self._get_csrf_token()

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = "malformed-refresh-token"

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


    def test_refresh_with_expired_cookie_is_rejected_without_500(self):
        csrf_token = self._get_csrf_token()

        expired_refresh = RefreshToken.for_user(self.user)
        expired_refresh.set_exp(
            lifetime=timedelta(seconds=-1),
        )

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = str(expired_refresh)

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


    def test_refresh_with_invalid_token_is_rejected(self):
        csrf_token = self._get_csrf_token()

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = "invalid-token"

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


    def test_refresh_cookie_is_not_returned_on_failed_refresh(self):
        csrf_token = self._get_csrf_token()

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = "malformed-refresh-token"

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertNotIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )


    def test_logout_is_idempotent_without_refresh_cookie(self):
        csrf_token = self._get_csrf_token()

        self.client.cookies.pop(
            REFRESH_COOKIE_NAME,
            None,
        )

        response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )


    def test_refresh_cookie_is_httponly_and_has_expected_path(self):
        response = self._login()

        cookie = response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertTrue(
            cookie["httponly"],
        )

        self.assertEqual(
            cookie["path"],
            "/api/auth/token/",
        )


    def test_refresh_cookie_secure_flag_follows_setting(self):
        with override_settings(
            REFRESH_COOKIE_SECURE=True,
        ):
            response = self._login()

            cookie = response.cookies[
                REFRESH_COOKIE_NAME
            ]

            self.assertTrue(
                cookie["secure"],
            )

        with override_settings(
            REFRESH_COOKIE_SECURE=False,
        ):
            response = self._login()

            cookie = response.cookies[
                REFRESH_COOKIE_NAME
            ]

            self.assertFalse(
                cookie["secure"],
            )


    def test_refresh_cookie_has_expected_samesite_and_max_age(self):
        response = self._login()

        cookie = response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertEqual(
            cookie["samesite"].lower(),
            "lax",
        )

        self.assertEqual(
            int(cookie["max-age"]),
            7 * 24 * 60 * 60,
        )

    
    def test_logout_blacklists_refresh_token_and_replay_is_rejected(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token

        csrf_token = self._get_csrf_token()

        logout_response = self.client.post(
            reverse("token_blacklist"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_200_OK,
        )

        # Try to reuse the logged-out refresh token.
        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = refresh_token

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


    def test_refresh_does_not_accept_refresh_token_from_request_body(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        # Remove the HttpOnly refresh cookie.
        self.client.cookies.pop(
            REFRESH_COOKIE_NAME,
            None,
        )

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh_token,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        # Refresh must be cookie-only.
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


    def test_access_token_cannot_be_used_as_refresh_cookie(self):
        login_response = self._login()

        access_token = login_response.data["access"]

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = access_token

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


    def test_tampered_refresh_token_is_rejected_without_500(self):
        login_response = self._login()

        refresh_token = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        # Tamper with the JWT signature, not the final encoded character.
        parts = refresh_token.split(".")

        self.assertEqual(
            len(parts),
            3,
        )

        signature = parts[2]

        tampered_signature = (
            ("a" if signature[0] != "a" else "b")
            + signature[1:]
        )

        tampered_token = ".".join(
            [
                parts[0],
                parts[1],
                tampered_signature,
            ]
        )

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = tampered_token

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertNotEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_rotated_refresh_cookie_preserves_security_attributes(self):
        login_response = self._login()

        old_refresh = login_response.cookies[
            REFRESH_COOKIE_NAME
        ].value

        self.client.cookies[
            REFRESH_COOKIE_NAME
        ] = old_refresh

        csrf_token = self._get_csrf_token()

        response = self.client.post(
            reverse("token_refresh"),
            {},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            REFRESH_COOKIE_NAME,
            response.cookies,
        )

        cookie = response.cookies[
            REFRESH_COOKIE_NAME
        ]

        self.assertTrue(
            cookie["httponly"],
        )

        self.assertEqual(
            cookie["path"],
            "/api/auth/token/",
        )

        self.assertEqual(
            cookie["samesite"].lower(),
            "lax",
        )

        self.assertEqual(
            bool(cookie["secure"]),
            settings.REFRESH_COOKIE_SECURE,
        )

        self.assertEqual(
            int(cookie["max-age"]),
            7 * 24 * 60 * 60,
        )

        