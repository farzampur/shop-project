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
    SupplierBalanceView,
    SupplierLedgerView,
    DebtorSuppliersView,
    SupplierPurchaseReportView,
    SupplierPaymentReportView,
    SupplierBalanceReportView,
    SupplierComprehensiveReportView,
    PurchaseReturnViewSet,
    SupplierSettleView,
    PurchaseReceiptPDFView,
    ProductBarcodeView,  
    ProductQRCodeView,
    ProductLabelPDFView,
    ProductLabelsPDFView,
    ProductBarcodeSearchView,
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

router.register(
    "purchase-returns",
    PurchaseReturnViewSet,
    basename="purchase-returns"
)

urlpatterns = [
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

    # مسیرهای گزارش تأمین‌کنندگان
    path(
        "suppliers/debtors/",
        DebtorSuppliersView.as_view(),
        name="supplier-debtors",
    ),

    path(
        "suppliers/<int:supplier_id>/balance/",
        SupplierBalanceView.as_view(),
        name="supplier-balance",
    ),

    path(
        "suppliers/<int:supplier_id>/ledger/",
        SupplierLedgerView.as_view(),
        name="supplier-ledger",
    ),
    path(
        "suppliers/purchase-report/",
        SupplierPurchaseReportView.as_view(),
        name="supplier-purchase-report",
    ),    
    path(
        "suppliers/payment-report/",
        SupplierPaymentReportView.as_view(),
        name="supplier-payment-report",
    ),    
    path(
        "suppliers/balance-report/",
        SupplierBalanceReportView.as_view(),
        name="supplier-balance-report",
    ),    
    path(
        "suppliers/comprehensive-report/",
        SupplierComprehensiveReportView.as_view(),
        name="supplier-comprehensive-report",
    ),  
    path(
        "suppliers/<int:supplier_id>/settle/",
        SupplierSettleView.as_view(),
        name="supplier-settle",
    ), 
    path(
        "purchases/<int:purchase_id>/receipt/",
        PurchaseReceiptPDFView.as_view(),
        name="purchase-receipt",
    ),   
    path(
        "products/<int:product_id>/barcode/",
        ProductBarcodeView.as_view(),
        name="product-barcode",
    ),
    path(
        "products/<int:product_id>/qrcode/",
        ProductQRCodeView.as_view(),
        name="product-qrcode",
    ),
    path(
        "products/<int:product_id>/label/",
        ProductLabelPDFView.as_view(),
        name="product-label",
    ),    
    path(
        "products/<int:product_id>/labels/",
        ProductLabelsPDFView.as_view(),
        name="product-labels",
    ),   
    path(
        "products/search-by-barcode/",
        ProductBarcodeSearchView.as_view(),
        name="product-search-by-barcode",
    ),    
]

urlpatterns += router.urls
urlpatterns += purchase_router.urls

