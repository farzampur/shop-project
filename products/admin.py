from django.contrib import admin

from .models import Category, Product, Inventory, Supplier, SupplierTransaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "store",
        "is_active",
        "created_at",
    )

    list_filter = (
        "store",
        "is_active",
    )

    search_fields = (
        "name",
        "store__name",
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "barcode",
        "category",
        "unit",
        "purchase_price",
        "sale_price",
        "is_active",
    )

    list_filter = (
        "category",
        "is_active",
    )

    search_fields = (
        "name",
        "barcode",
    )
    
    
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "store",
        "quantity",
        "min_quantity",
        "updated_at",
    )

    list_filter = (
        "store",
    )

    search_fields = (
        "product__name",
        "product__barcode",
        "store__name",
    )


@admin.register(Supplier)
class SupplierAdmin(
    admin.ModelAdmin
):
    """
    مدیریت تأمین‌کنندگان.
    """

    list_display = (
        "id",
        "name",
        "phone",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "phone",
        "address",
    )

    list_filter = (
        "created_at",
    )

    date_hierarchy = "created_at"


@admin.register(
    SupplierTransaction
)
class SupplierTransactionAdmin(
    admin.ModelAdmin
):
    """
    مدیریت تراکنش‌های مالی تأمین‌کنندگان.
    """

    list_display = (
        "id",
        "supplier",
        "transaction_type",
        "amount",
        "reference_id",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "created_at",
    )

    search_fields = (
        "supplier__name",
        "description",
    )

    date_hierarchy = "created_at"

    readonly_fields = (
        "created_at",
    )

    