from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserStore
from .serializers import UserStoreSerializer, StoreUserCreateSerializer, MeSerializer
from .permissions import StoreUserPermission
from core.audit import audit


class UserStoreViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, StoreUserPermission]

    def get_queryset(self):
        if self.request.user.is_superuser:
            qs = UserStore.objects.filter(store__is_active=True)
        else:
            qs = UserStore.objects.filter(
                store__store_users__user=self.request.user,
                store__store_users__role="manager",
                store__store_users__is_active=True,
                store__is_active=True,
            ).select_related("user", "store").distinct()
        store_id = self.request.query_params.get("store")
        if store_id:
            qs = qs.filter(store_id=store_id)
        return qs.order_by("store__name", "user__username")

    def get_serializer_class(self):
        return StoreUserCreateSerializer if self.action == "create" else UserStoreSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user_store = UserStore.objects.get(user=user, store=serializer.validated_data["store"])
        audit(user=request.user, action="create", model_name="UserStore", object_id=user_store.id, description=f"ایجاد کاربر {user.username} در {user_store.store.name}", store=user_store.store, metadata={"role": user_store.role})
        return Response(UserStoreSerializer(user_store).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_role, old_active = instance.role, instance.is_active
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        audit(user=request.user, action="update", model_name="UserStore", object_id=obj.id, description=f"ویرایش دسترسی {obj.user.username} در {obj.store.name}", store=obj.store, metadata={"role_before": old_role, "role_after": obj.role, "active_before": old_active, "active_after": obj.is_active})
        return Response(self.get_serializer(obj).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user_id == request.user.id:
            return Response({"detail": "نمی‌توانید دسترسی خودتان را حذف کنید."}, status=status.HTTP_400_BAD_REQUEST)
        store = instance.store
        username = instance.user.username
        instance.delete()
        audit(user=request.user, action="delete", model_name="UserStore", object_id=None, description=f"حذف دسترسی کاربر {username} از {store.name}", store=store, metadata={"username": username})
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
