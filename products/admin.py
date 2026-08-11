from django.contrib import admin

from .models import Category, Product, Inventory


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


    