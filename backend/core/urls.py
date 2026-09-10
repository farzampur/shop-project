from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import StoreViewSet, AuditLogViewSet, HealthCheckView
router = DefaultRouter()
router.register(r"stores", StoreViewSet, basename="store")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
urlpatterns = router.urls

urlpatterns += [path("health/", HealthCheckView.as_view(), name="health")]
