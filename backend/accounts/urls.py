from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MeView, UserStoreViewSet


router = DefaultRouter()

router.register(
    r"store-users",
    UserStoreViewSet,
    basename="store-users"
)

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]