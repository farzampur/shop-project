from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Store, AuditLog
from .serializers import StoreSerializer, AuditLogSerializer
from accounts.models import UserStore
from accounts.store_access import user_store_ids
from core.audit import audit


class StoreViewSet(viewsets.ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Store.objects.all().order_by("name")
        return Store.objects.filter(id__in=user_store_ids(self.request.user), is_active=True).order_by("name")

    def create(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"detail": "فقط مدیر سیستم می‌تواند شعبه جدید ایجاد کند."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        audit(user=request.user, action="create", model_name="Store", object_id=obj.id, description=f"ایجاد فروشگاه {obj.name}", store=obj, metadata={"code": obj.code})
        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.is_superuser:
            relation = UserStore.objects.filter(user=request.user, store=obj, role="manager", is_active=True).first()
            if relation is None:
                return Response({"detail": "شما مدیر این فروشگاه نیستید."}, status=status.HTTP_403_FORBIDDEN)
            if "is_active" in request.data and bool(request.data.get("is_active")) is False:
                return Response({"detail": "مدیر شعبه نمی‌تواند شعبه را غیرفعال کند."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(obj, data=request.data, partial=request.method == "PATCH")
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        audit(user=request.user, action="update", model_name="Store", object_id=updated.id, description=f"ویرایش فروشگاه {updated.name}", store=updated, metadata={"code": updated.code})
        return Response(self.get_serializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response({"detail": "فقط مدیر سیستم می‌تواند شعبه را حذف کند."}, status=status.HTTP_403_FORBIDDEN)
        obj = self.get_object()
        if UserStore.objects.filter(store=obj).exists():
            return Response({"detail": "شعبه‌ای که کاربر یا سابقه دسترسی دارد قابل حذف نیست؛ آن را غیرفعال کنید."}, status=status.HTTP_400_BAD_REQUEST)
        store_id, name = obj.id, obj.name
        obj.delete()
        audit(user=request.user, action="delete", model_name="Store", object_id=store_id, description=f"حذف فروشگاه {name}", store=None, metadata={"store_id": store_id})
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        qs = AuditLog.objects.filter(store_id__in=user_store_ids(self.request.user)).select_related("user", "store")
        store = self.request.query_params.get("store")
        action = self.request.query_params.get("action")
        if store: qs = qs.filter(store_id=store)
        if action: qs = qs.filter(action=action)
        return qs[:500]


class HealthCheckView(APIView):
    """Minimal unauthenticated liveness/readiness endpoint for deployment checks."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from django.db import connection

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response(
                {"status": "error", "database": "unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"status": "ok", "database": "ok"}, status=status.HTTP_200_OK)
