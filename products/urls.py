from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ProductViewSet,
    InventoryViewSet,
    InventoryTransactionViewSet,   
    InventoryReportViewSet,
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


urlpatterns = router.urls