"""Compatibility exports for product endpoints.

Store-aware authorization lives in accounts.permissions so every module uses
the same store/role resolution and object-level isolation rules.
"""
from accounts.permissions import InventoryPermission, StoreRolePermission

__all__ = ["InventoryPermission", "StoreRolePermission"]
