from rest_framework.permissions import BasePermission
from accounts.models import UserStore


ROLE_PERMISSIONS = {
    "manager": {"GET": True, "POST": True, "PUT": True, "PATCH": True, "DELETE": True},
    "warehouse": {"GET": True, "POST": True, "PUT": True, "PATCH": True, "DELETE": False},
    "seller": {"GET": True, "POST": False, "PUT": False, "PATCH": False, "DELETE": False},
    "cashier": {"GET": True, "POST": True, "PUT": False, "PATCH": False, "DELETE": False},
}


def get_store_from_request(request, view=None):
    """Resolve the target store for both direct and related-object requests."""
    store_id = request.query_params.get("store") or request.data.get("store")
    if store_id:
        return store_id

    # Some financial/purchase endpoints identify the store indirectly via a
    # related object. Resolve those IDs before applying role checks.
    relation_fields = {
        "cashbox": ("sales.models", "CashBox"),
        "from_cashbox": ("sales.models", "CashBox"),
        "to_cashbox": ("sales.models", "CashBox"),
        "customer": ("sales.models", "Customer"),
        "supplier": ("products.models", "Supplier"),
        "purchase": ("products.models", "Purchase"),
    }
    for field, (module_name, model_name) in relation_fields.items():
        value = request.data.get(field)
        if value in (None, ""):
            continue
        try:
            module = __import__(module_name, fromlist=[model_name])
            obj = getattr(module, model_name).objects.only("store_id").get(pk=value)
            return obj.store_id
        except Exception:
            continue

    kwargs = getattr(view, "kwargs", {}) if view is not None else {}
    if kwargs.get("supplier_id"):
        from products.models import Supplier
        return Supplier.objects.filter(pk=kwargs["supplier_id"]).values_list("store_id", flat=True).first()
    if kwargs.get("purchase_pk"):
        from products.models import Purchase
        return Purchase.objects.filter(pk=kwargs["purchase_pk"]).values_list("store_id", flat=True).first()
    if kwargs.get("cart_pk"):
        from sales.models import Cart
        return Cart.objects.filter(pk=kwargs["cart_pk"]).values_list("store_id", flat=True).first()
    return None


def get_user_store_role(user, store_id):
    if user.is_superuser:
        return "manager"
    relation = UserStore.objects.filter(user=user, store_id=store_id).first()
    return relation.role if relation else None


class StoreRolePermission(BasePermission):
    """Permission is evaluated against the store targeted by the request/object."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        store_id = get_store_from_request(request, view)
        if store_id is None:
            allowed_roles_by_method = getattr(view, "allowed_roles_by_method", None)
            if allowed_roles_by_method is not None:
                allowed_roles = allowed_roles_by_method.get(request.method, set())
                return request.user.user_stores.filter(role__in=allowed_roles).exists()

            allowed_roles = getattr(view, "allowed_roles", None)
            if allowed_roles is not None:
                return request.user.user_stores.filter(role__in=allowed_roles).exists() and (
                    request.method in getattr(
                        view, "allowed_methods", {"GET", "POST", "PUT", "PATCH", "DELETE"}
                    )
                )

            # For generic list/read actions the queryset is already store-scoped.
            return request.method == "GET"

        role = get_user_store_role(request.user, store_id)
        allowed_roles_by_method = getattr(view, "allowed_roles_by_method", None)
        if allowed_roles_by_method is not None:
            return role in allowed_roles_by_method.get(request.method, set())
        allowed_roles = getattr(view, "allowed_roles", None)
        if allowed_roles is not None:
            allowed_methods = getattr(
                view, "allowed_methods", {"GET", "POST", "PUT", "PATCH", "DELETE"}
            )
            return request.method in allowed_methods and role in set(allowed_roles)
        return ROLE_PERMISSIONS.get(role, {}).get(request.method, False)

    def has_object_permission(self, request, view, obj):
        store = getattr(obj, "store", None)
        if store is None and hasattr(obj, "cart"):
            store = obj.cart.store
        if store is None and hasattr(obj, "category"):
            store = obj.category.store
        if store is None:
            return False
        role = get_user_store_role(request.user, store.id)
        allowed_roles_by_method = getattr(view, "allowed_roles_by_method", None)
        if allowed_roles_by_method is not None:
            return request.user.is_superuser or role in allowed_roles_by_method.get(request.method, set())
        allowed_roles = getattr(view, "allowed_roles", None)
        if allowed_roles is not None:
            allowed_methods = getattr(
                view, "allowed_methods", {"GET", "POST", "PUT", "PATCH", "DELETE"}
            )
            return request.user.is_superuser or (
                request.method in allowed_methods and role in set(allowed_roles)
            )
        return request.user.is_superuser or ROLE_PERMISSIONS.get(role, {}).get(request.method, False)


class StoreUserPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        store_id = get_store_from_request(request, view)
        if store_id is None:
            return request.user.user_stores.filter(role="manager").exists()
        return request.user.user_stores.filter(store_id=store_id, role="manager").exists()


class InventoryPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        store_id = get_store_from_request(request, view)
        if store_id is None:
            return request.method == "GET"
        qs = request.user.user_stores.filter(store_id=store_id)
        if request.method == "GET":
            return qs.exists()
        if request.method in {"POST", "PUT", "PATCH"}:
            return qs.filter(role__in={"manager", "warehouse"}).exists()
        return False
