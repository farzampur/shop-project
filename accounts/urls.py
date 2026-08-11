from rest_framework.routers import DefaultRouter

from .views import UserStoreViewSet


router = DefaultRouter()

router.register(
    r"my-stores",
    UserStoreViewSet,
    basename="my-stores"
)

urlpatterns = router.urls