from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import (
    CartViewSet,
    CartItemViewSet,
    CheckoutView,
    OrderViewSet,    
    SalesReportViewSet,
)


router = routers.DefaultRouter()

router.register(
    "carts",
    CartViewSet,
    basename="cart"
)

cart_router = routers.NestedDefaultRouter(
    router,
    "carts",
    lookup="cart"
)

cart_router.register(
    "items",
    CartItemViewSet,
    basename="cart-items"
)

router.register(
    "orders",
    OrderViewSet,
    basename="orders"
)

router.register(
    "sales-report",
    SalesReportViewSet,
    basename="sales-report"
)


urlpatterns = (
    router.urls
    + cart_router.urls
    + [
        path(
            "checkout/",
            CheckoutView.as_view(),
            name="checkout",
        ),
    ]
)