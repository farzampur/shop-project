from rest_framework.routers import DefaultRouter
from .views import StoreViewSet, AuditLogViewSet
router = DefaultRouter()
router.register(r"stores", StoreViewSet, basename="store")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
urlpatterns = router.urls
