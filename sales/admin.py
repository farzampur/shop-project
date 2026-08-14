from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Customer,
    Expense,
    CashBox,
    CashBoxTransaction,
)

# Register your models here.
class CartItemInline(admin.TabularInline):

    model = CartItem

    extra = 0
    
class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0
    
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "store",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "store__name",
    )

    list_filter = (
        "store",
        "created_at",
    )

    ordering = (
        "-id",
    )

    inlines = [
        CartItemInline
    ]

    list_per_page = 25
    
    
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "expense_type",
        "amount",
        "store",
        "user",
        "expense_date",
    )

    search_fields = (
        "title",
        "description",
    )

    list_filter = (
        "expense_type",
        "store",
        "expense_date",
    )

    date_hierarchy = "expense_date"

    ordering = (
        "-expense_date",
        "-id",
    )

    list_per_page = 25
    
    
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "first_name",
        "last_name",
        "mobile",
        "store",
        "created_at",
    )

    search_fields = (
        "first_name",
        "last_name",
        "mobile",
    )

    list_filter = (
        "store",
        "created_at",
    )

    ordering = (
        "-id",
    )

    list_per_page = 25
    

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "cart",
        "product",
        "quantity",
        "unit_price",
        "discount_percent",
        "created_at",
    )

    search_fields = (
        "product__name",
    )

    list_filter = (
        "created_at",
    )

    ordering = (
        "-id",
    )

    list_per_page = 25
    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "status",
        "customer",
        "user",
        "store",
        "total_price",
        "created_at",
    )

    search_fields = (
        "customer__first_name",
        "customer__last_name",
        "user__username",
    )

    list_filter = (
        "status",
        "store",
        "created_at",
    )

    ordering = (
        "-id",
    )

    readonly_fields = (
        "total_before_discount",
        "total_discount",
        "total_price",
        "created_at",
        "updated_at",
    )

    inlines = [
        OrderItemInline
    ]

    list_per_page = 25


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "product_name",
        "quantity",
        "unit_price",
        "discount_percent",
        "total_price",
    )

    search_fields = (
        "product_name",
    )

    ordering = (
        "-id",
    )

    list_per_page = 25


@admin.register(CashBox)
class CashBoxAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "store",
        "balance",
    )


@admin.register(
    CashBoxTransaction
)
class CashBoxTransactionAdmin(
    admin.ModelAdmin
):

    list_display = (
        "id",
        "cashbox",
        "transaction_type",
        "amount",
        "created_at",
    )

    