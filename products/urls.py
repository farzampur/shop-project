from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    CategoryViewSet,
    ProductViewSet,
    InventoryViewSet,
    InventoryTransactionViewSet,   
    InventoryReportViewSet,
    SupplierViewSet,
    PurchaseViewSet,   
    PurchaseItemViewSet    
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


urlpatterns = (
    router.urls
    + purchase_router.urls
)


