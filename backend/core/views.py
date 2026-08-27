#from django.shortcuts import render
from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated 
from .models import Store
from .serializers import StoreSerializer
from rest_framework.exceptions import PermissionDenied



class StoreViewSet(viewsets.ModelViewSet):

    serializer_class = StoreSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        return Store.objects.filter(
            store_users__user=self.request.user
        ).distinct()

    def _is_manager(self, store=None):
        user = self.request.user

        if user.is_superuser:
            return True

        user_stores = user.user_stores.all()

        if store is not None:
            return user_stores.filter(
                store=store,
                role="manager"
            ).exists()

        return user_stores.filter(
            role="manager"
        ).exists()

    def perform_create(self, serializer):

        if not self._is_manager():
            raise PermissionDenied(
                "فقط مدیر فروشگاه می‌تواند فروشگاه ایجاد کند."
            )

        serializer.save()

    def perform_update(self, serializer):

        store = self.get_object()

        if not self._is_manager(store):
            raise PermissionDenied(
                "فقط مدیر این فروشگاه می‌تواند اطلاعات آن را ویرایش کند."
            )

        serializer.save()

    def perform_destroy(self, instance):

        if not self._is_manager(instance):
            raise PermissionDenied(
                "فقط مدیر این فروشگاه می‌تواند آن را حذف کند."
            )

        instance.delete()