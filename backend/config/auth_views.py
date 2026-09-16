from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)


REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/auth/token/"
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60

    
@ensure_csrf_cookie
def csrf_cookie_view(request):
    return JsonResponse(
        {
            "detail": "CSRF cookie set."
        }
    )
    
def set_refresh_cookie(response, refresh_token):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="Lax",
        path=REFRESH_COOKIE_PATH,
    )


class CookieTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        self.refresh_token = data.pop("refresh")
        return data


class CookieTokenObtainPairView(TokenObtainPairView):
    serializer_class = CookieTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response = Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )

        set_refresh_cookie(
            response,
            serializer.refresh_token,
        )

        return response


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    pass


@method_decorator(csrf_protect, name="dispatch")
class CookieTokenRefreshView(TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(
            REFRESH_COOKIE_NAME
        )

        if not refresh_token:
            raise serializers.ValidationError(
                {
                    "refresh": (
                        "Refresh token cookie is required."
                    )
                }
            )

        serializer = self.get_serializer(
            data={
                "refresh": refresh_token,
            },
            context={"request": request},
        )

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0]) from exc
            
        data = dict(serializer.validated_data)

        new_refresh_token = data.pop(
            "refresh",
            None,
        )

        response = Response(
            data,
            status=status.HTTP_200_OK,
        )

        if new_refresh_token:
            set_refresh_cookie(
                response,
                new_refresh_token,
            )

        return response

@method_decorator(csrf_protect, name="dispatch")
class CookieTokenBlacklistView(TokenBlacklistView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get(
            REFRESH_COOKIE_NAME
        )

        response = Response(
            status=status.HTTP_200_OK,
        )

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass

        response.delete_cookie(
            key=REFRESH_COOKIE_NAME,
            path=REFRESH_COOKIE_PATH,
        )

        return response