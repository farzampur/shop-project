from rest_framework.permissions import BasePermission

from accounts.store_access import has_store_access


class AccountingManagerPermission(BasePermission):
    message = "دسترسی حسابداری فقط برای مدیر فروشگاه مجاز است."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        store_id = request.query_params.get("store") or request.data.get("store")
        if store_id is None:
            return request.user.user_stores.filter(
                is_active=True,
                store__is_active=True,
                role="manager",
            ).exists()
        try:
            store_id = int(store_id)
        except (TypeError, ValueError):
            return False
        return has_store_access(request.user, store_id, {"manager"})
