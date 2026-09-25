from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.exceptions import PermissionDenied


def user_store_ids(user):
    if user.is_superuser:
        from core.models import Store
        return Store.objects.values_list("id", flat=True)
    return user.user_stores.filter(is_active=True, store__is_active=True).values_list("store_id", flat=True)


def has_store_access(user, store_id, roles=None):
    if user.is_superuser:
        return True
    qs = user.user_stores.filter(store_id=store_id, is_active=True, store__is_active=True)
    if roles:
        qs = qs.filter(role__in=roles)
    return qs.exists()


def require_store_access(user, store_id, roles=None):
    if not has_store_access(user, store_id, roles):
        raise PermissionDenied("شما به این فروشگاه دسترسی ندارید.")


def require_object_store_access(user, store, roles=None):
    require_store_access(user, store.id, roles)


def requested_store_id(request, user, *, required=False):
    """Return the explicitly requested store after validating user access."""
    value = request.query_params.get("store") or request.data.get("store")
    if value in (None, ""):
        if required:
            raise PermissionDenied("فروشگاه مشخص نشده است.")
        return None
    try:
        store_id = int(value)
    except (TypeError, ValueError):
        raise PermissionDenied("شناسه فروشگاه نامعتبر است.")
    if not has_store_access(user, store_id):
        raise PermissionDenied("شما به این فروشگاه دسترسی ندارید.")
    return store_id
