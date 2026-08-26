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
        

       



        