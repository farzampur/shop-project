from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
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
        TokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),

    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
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