from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from .auth_views import (
    CookieTokenBlacklistView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    csrf_cookie_view,
)


urlpatterns = [

    # Django Admin
    path(
        "admin/",
        admin.site.urls
    ),

    # JWT Authentication
    path(
        "api/auth/token/",
        CookieTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/auth/token/refresh/",
        CookieTokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "api/auth/token/blacklist/",
        CookieTokenBlacklistView.as_view(),
        name="token_blacklist",
    ),
    
    path(
        "api/auth/csrf/",
        csrf_cookie_view,
        name="csrf_cookie",
    ),

    # Core API
    path(
        "api/",
        include("core.urls")
    ),
    
    # Accounts
    path(
        "api/accounts/",
        include("accounts.urls")
    ),

    # Products
    path(
        "api/products/",
        include("products.urls")
    ),

    #sales
    path(
        "api/sales/",
        include("sales.urls")
    ),
    
]

urlpatterns += static(
    settings.STATIC_URL,
    document_root=settings.STATIC_ROOT
)