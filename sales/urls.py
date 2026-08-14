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
    DebtorCustomersView,
    CreditorCustomersView,
    CustomerLedgerView,
    CashBoxViewSet,
    CashBoxTransactionViewSet,
    FinancialReportView,
    CashLedgerView,
    CashBoxBalanceReportView,
    DailyCashFlowReportView,
    CashTransferViewSet,
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

router.register(
    "cashboxes",
    CashBoxViewSet,
    basename="cashboxes"
)

router.register(
    "cashbox-transactions",
    CashBoxTransactionViewSet,
    basename="cashbox-transactions"
)

router.register(
    r"cash-transfers",
    CashTransferViewSet,
    basename="cash-transfer"
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
        path(
            "customers/debtors/",
            DebtorCustomersView.as_view(),
            name="customer-debtors",
        ),
        path(
            "customers/creditors/",
            CreditorCustomersView.as_view(),
            name="customer-creditors",
        ),
        path(
            "customers/<int:customer_id>/ledger/",
            CustomerLedgerView.as_view(),
            name="customer-ledger",
        ), 
        path(
            "financial-report/",
            FinancialReportView.as_view(),
            name="financial-report",
        ),
        path(
            "cash-ledger/",
            CashLedgerView.as_view(),
            name="cash-ledger",
        ), 
        path(
            "cashbox-balance-report/",
            CashBoxBalanceReportView.as_view(),
            name="cashbox-balance-report",
        ), 
        path(
            "daily-cash-flow-report/",
            DailyCashFlowReportView.as_view(),
            name="daily-cash-flow-report",
        ),        
    ]
)
