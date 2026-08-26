from rest_framework.permissions import BasePermission


class StoreUserPermission(BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # بررسی اینکه کاربر حداقل در یک فروشگاه Manager است
        return request.user.user_stores.filter(
            role="manager"
        ).exists()