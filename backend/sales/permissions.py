from rest_framework.permissions import BasePermission

from accounts.models import UserStore
from .models import Cart



MAX_DISCOUNT_BY_ROLE = {
    "seller": 10,
    "cashier": 15,
    "manager": 30,
    "warehouse": 0,
}


def get_user_max_discount(user, store):

    user_store = UserStore.objects.filter(
        user=user,
        store=store
    ).first()

    if not user_store:
        return None

    return MAX_DISCOUNT_BY_ROLE.get(
        user_store.role,
        0
    )



class CartPermission(BasePermission):

    message = "شما به این فروشگاه دسترسی ندارید."

    ALLOWED_ROLES = {"manager", "seller", "cashier"}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        # Cart endpoints are sales operations; warehouse users must not
        # be able to create/read another employee's sales carts.
        if request.method == "GET":
            return UserStore.objects.filter(
                user=request.user,
                role__in=self.ALLOWED_ROLES,
            ).exists()

        store_id = request.data.get("store")
        if store_id is not None:
            return UserStore.objects.filter(
                user=request.user,
                store_id=store_id,
                role__in=self.ALLOWED_ROLES,
            ).exists()

        # Nested CartItem routes are resolved by the parent cart.
        cart_id = getattr(view, "kwargs", {}).get("cart_pk")
        if cart_id is not None:
            return UserStore.objects.filter(
                user=request.user,
                role__in=self.ALLOWED_ROLES,
                store__carts__id=cart_id,
            ).exists()

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if isinstance(obj, Cart):
            store = obj.store
        else:
            store = obj.cart.store

        return UserStore.objects.filter(
            user=request.user,
            store=store,
            role__in=self.ALLOWED_ROLES,
        ).exists()
        

       



        