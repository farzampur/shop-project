from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserStoreViewSet


router = DefaultRouter()

router.register(
    r"store-users",
    UserStoreViewSet,
    basename="store-users"
)

urlpatterns = [
    path("", include(router.urls)),
]