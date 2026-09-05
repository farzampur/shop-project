from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.exceptions import PermissionDenied


def user_store_ids(user):
    if user.is_superuser:
        from core.models import Store
        return Store.objects.values_list("id", flat=True)
    return user.user_stores.values_list("store_id", flat=True)


def has_store_access(user, store_id, roles=None):
    if user.is_superuser:
        return True
    qs = user.user_stores.filter(store_id=store_id)
    if roles:
        qs = qs.filter(role__in=roles)
    return qs.exists()


def require_store_access(user, store_id, roles=None):
    if not has_store_access(user, store_id, roles):
        raise PermissionDenied("شما به این فروشگاه دسترسی ندارید.")


def require_object_store_access(user, store, roles=None):
    require_store_access(user, store.id, roles)
