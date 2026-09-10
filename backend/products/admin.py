from django.contrib import admin
from .models import (
    Category, Product, Inventory, InventoryTransaction,
    Supplier, Purchase, PurchaseItem, SupplierTransaction, PurchaseReturn,
    StockTransfer, StockTransferItem, ProductPrice,
)

MODEL_NAMES = {
    Category: ("دسته‌بندی", "دسته‌بندی‌ها"),
    Product: ("کالا", "کالاها"),
    Inventory: ("موجودی کالا", "موجودی کالاها"),
    InventoryTransaction: ("تراکنش موجودی", "تراکنش‌های موجودی"),
    Supplier: ("تأمین‌کننده", "تأمین‌کنندگان"),
    Purchase: ("خرید", "خریدها"),
    PurchaseItem: ("آیتم خرید", "آیتم‌های خرید"),
    SupplierTransaction: ("تراکنش تأمین‌کننده", "تراکنش‌های تأمین‌کنندگان"),
    PurchaseReturn: ("برگشت خرید", "برگشت‌های خرید"),
    StockTransfer: ("انتقال کالا", "انتقال کالاها"),
    StockTransferItem: ("آیتم انتقال", "آیتم‌های انتقال"),
    ProductPrice: ("قیمت کالا", "قیمت‌های کالا"),
}
for model, names in MODEL_NAMES.items():
    model._meta.verbose_name, model._meta.verbose_name_plural = names

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "store", "is_active", "created_at")
    list_filter = ("store", "is_active", "created_at")
    search_fields = ("name", "store__name", "store__code")
    ordering = ("store", "name", "id")
    readonly_fields = ("created_at",)
    list_per_page = 25

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "barcode", "category", "unit", "purchase_price", "sale_price", "is_active", "updated_at")
    list_filter = ("category__store", "category", "is_active", "unit", "created_at")
    search_fields = ("name", "barcode", "category__name")
    ordering = ("name", "id")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "store", "quantity", "min_quantity", "updated_at")
    list_filter = ("store", "updated_at")
    search_fields = ("product__name", "product__barcode", "store__name", "store__code")
    ordering = ("store", "product__name", "id")
    readonly_fields = ("updated_at",)
    list_per_page = 25

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "store", "transaction_type", "quantity", "reference_id", "created_at")
    list_filter = ("store", "transaction_type", "created_at")
    search_fields = ("product__name", "product__barcode", "description")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    list_per_page = 25

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "store", "phone", "created_at", "updated_at")
    list_filter = ("store", "created_at")
    search_fields = ("name", "phone", "address", "description", "store__name")
    ordering = ("store", "name", "id")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    show_change_link = True

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "store", "invoice_number", "total_amount", "received", "user", "created_at")
    list_filter = ("store", "supplier", "received", "created_at")
    search_fields = ("invoice_number", "supplier__name", "user__username")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    inlines = (PurchaseItemInline,)
    list_per_page = 25

@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ("id", "purchase", "product", "quantity", "unit_price", "total_price")
    list_filter = ("purchase__store", "product__category")
    search_fields = ("product__name", "product__barcode", "purchase__invoice_number")
    ordering = ("-id",)
    list_per_page = 25

@admin.register(SupplierTransaction)
class SupplierTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "transaction_type", "amount", "reference_id", "created_at")
    list_filter = ("supplier__store", "transaction_type", "created_at")
    search_fields = ("supplier__name", "description")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
    list_per_page = 25

@admin.register(PurchaseReturn)
class PurchaseReturnAdmin(admin.ModelAdmin):
    list_display = ("id", "purchase", "product", "quantity", "unit_price", "total_amount", "created_by", "created_at")
    list_filter = ("purchase__store", "created_at")
    search_fields = ("product__name", "product__barcode", "purchase__invoice_number", "description")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "total_amount")
    list_per_page = 25


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ("id", "source_store", "destination_store", "status", "created_by", "created_at")
    list_filter = ("status", "source_store", "destination_store", "created_at")
    search_fields = ("id", "notes", "created_by__username")
    readonly_fields = ("created_at", "updated_at", "shipped_at", "received_at")


@admin.register(StockTransferItem)
class StockTransferItemAdmin(admin.ModelAdmin):
    list_display = ("id", "transfer", "product", "quantity")
    search_fields = ("product__name", "product__barcode")


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "store", "price_type", "amount", "effective_from", "effective_to", "is_active")
    list_filter = ("store", "price_type", "is_active", "effective_from")
    search_fields = ("product__name", "product__barcode", "store__name")
    readonly_fields = ("created_at", "updated_at")
