from rest_framework.permissions import BasePermission


class StoreRolePermission(BasePermission):

    ROLE_PERMISSIONS = {
        "manager": {
            "GET": True,
            "POST": True,
            "PUT": True,
            "PATCH": True,
            "DELETE": True,
        },

        "warehouse": {
            "GET": True,
            "POST": True,
            "PUT": True,
            "PATCH": True,
            "DELETE": False,
        },

        "seller": {
            "GET": True,
            "POST": False,
            "PUT": False,
            "PATCH": False,
            "DELETE": False,
        },

        "cashier": {
            "GET": True,
            "POST": False,
            "PUT": False,
            "PATCH": False,
            "DELETE": False,
        },
    }

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        method = request.method

        user_stores = request.user.user_stores.all()

        for user_store in user_stores:

            role = user_store.role

            permissions = self.ROLE_PERMISSIONS.get(
                role,
                {}
            )

            if permissions.get(method, False):
                return True

        return False


class StoreUserPermission(BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        return request.user.user_stores.filter(
            role="manager"
        ).exists()


class InventoryPermission(BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        roles = set(
            request.user.user_stores.values_list(
                "role",
                flat=True
            )
        )

        if request.method == "GET":
            return bool(roles)

        if request.method in ["POST", "PUT", "PATCH"]:
            return bool(
                roles.intersection(
                    {"manager", "warehouse"}
                )
            )

        return False