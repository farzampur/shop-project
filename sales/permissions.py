from rest_framework.permissions import BasePermission

from accounts.models import UserStore
from .models import Cart

class CartPermission(BasePermission):

    message = "شما به این فروشگاه دسترسی ندارید."

    def has_permission(self, request, view):

        return (
            request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):

        if isinstance(obj, Cart):
            store = obj.store
        else:
            store = obj.cart.store

        return UserStore.objects.filter(
            user=request.user,
            store=store,
        ).exists()