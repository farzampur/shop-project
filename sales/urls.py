from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import (
    CartViewSet,
    CartItemViewSet,
    CheckoutView,
    OrderViewSet,    
    SalesReportViewSet,
    DashboardView,
    ExpenseViewSet,
    CustomerViewSet,
    CustomerReportView,
    CustomerTransactionViewSet,
    CustomerBalanceView,
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

router.register(
    "expenses",
    ExpenseViewSet,
    basename="expenses"
)

router.register(
    "customers",
    CustomerViewSet,
    basename="customers"
)

router.register(
    "customer-transactions",
    CustomerTransactionViewSet,
    basename="customer-transactions"
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

        path(
            "dashboard/",
            DashboardView.as_view(),
            name="dashboard",
        ),
        path(
            "customer-report/",
            CustomerReportView.as_view(),
            name="customer-report",
        ),
        path(
            "customers/<int:customer_id>/balance/",
            CustomerBalanceView.as_view(),
            name="customer-balance",
        ),        
    ]
)
