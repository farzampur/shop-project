from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.urls import path

from .views import (
    CategoryViewSet,
    ProductViewSet,
    InventoryViewSet,
    InventoryTransactionViewSet,   
    InventoryReportViewSet,
    SupplierViewSet,
    PurchaseViewSet,   
    PurchaseItemViewSet,
    LowStockReportView,
    OutOfStockReportView,
    InventoryLedgerView,
    InventoryValueReportView,
    SlowMovingInventoryReportView,
    InventoryPotentialProfitReportView,
    StoreInventorySummaryView,
    InventoryReportView,
    InventoryDashboardView,
    SupplierTransactionViewSet,
    SupplierPaymentViewSet,

)


router = DefaultRouter()

router.register(
    r"categories",
    CategoryViewSet,
    basename="category"
)

router.register(
    r"products",
    ProductViewSet,
    basename="product"
)

router.register(
    r"inventory",
    InventoryViewSet,
    basename="inventory"
)

router.register(
    "transactions",
    InventoryTransactionViewSet,
    basename="transactions"
)

router.register(
    "inventory-report",
    InventoryReportViewSet,
    basename="inventory-report"
)

router.register(
    "suppliers",
    SupplierViewSet,
    basename="suppliers"
)

router.register(
    "purchases",
    PurchaseViewSet,
    basename="purchases"
)

purchase_router = routers.NestedDefaultRouter(
    router,
    "purchases",
    lookup="purchase"
)

purchase_router.register(
    "items",
    PurchaseItemViewSet,
    basename="purchase-items"
)

router.register(
    "supplier-transactions",
    SupplierTransactionViewSet,
    basename="supplier-transactions"
)

router.register(
    "supplier-payments",
    SupplierPaymentViewSet,
    basename="supplier-payments"
)

urlpatterns = (
    router.urls
    + purchase_router.urls
    + [
        path(
            "inventory-low-stock/",
            LowStockReportView.as_view(),
            name="inventory-low-stock",
        ),
        path(
            "inventory-out-of-stock/",
            OutOfStockReportView.as_view(),
            name="inventory-out-of-stock",
        ),   
        path(
            "inventory-ledger/<int:product_id>/",
            InventoryLedgerView.as_view(),
            name="inventory-ledger",
        ),
        path(
            "inventory-value-report/",
            InventoryValueReportView.as_view(),
            name="inventory-value-report",
        ),        
        path(
            "inventory-slow-moving/",
            SlowMovingInventoryReportView.as_view(),
            name="inventory-slow-moving",
        ),     
        path(
            "inventory-potential-profit/",
            InventoryPotentialProfitReportView.as_view(),
            name="inventory-potential-profit",
        ),       
        path(
            "store-inventory-summary/",
            StoreInventorySummaryView.as_view(),
            name="store-inventory-summary",
        ),      
        path(
            "inventory-report-full/",
            InventoryReportView.as_view(),
            name="inventory-report-full",
        ),    
        path(
            "inventory-dashboard/",
            InventoryDashboardView.as_view(),
            name="inventory-dashboard",
        ),        
    ]  
)


