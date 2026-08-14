from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Customer,
    CustomerTransaction,
    Expense,
    CashBox,
    CashBoxTransaction,
    CashTransfer,
)


# =========================
# Cart
# =========================

class CartItemInline(
    admin.TabularInline
):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "store",
        "customer",
        "user",
        "created_at",
    )

    list_filter = (
        "store",
        "created_at",
    )

    search_fields = (
        "customer__first_name",
        "customer__last_name",
        "user__username",
    )

    inlines = [
        CartItemInline
    ]


# =========================
# Cart Item
# =========================

@admin.register(CartItem)
class CartItemAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "cart",
        "product",
        "quantity",
        "unit_price",
        "discount_percent",
    )

    list_filter = (
        "discount_percent",
    )

    search_fields = (
        "product__name",
    )


# =========================
# Order
# =========================

class OrderItemInline(
    admin.TabularInline
):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "customer",
        "store",
        "status",
        "total_price",
        "created_at",
    )

    list_filter = (
        "status",
        "store",
        "created_at",
    )

    search_fields = (
        "customer__first_name",
        "customer__last_name",
    )

    date_hierarchy = (
        "created_at"
    )

    inlines = [
        OrderItemInline
    ]


# =========================
# Order Item
# =========================

@admin.register(OrderItem)
class OrderItemAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "order",
        "product_name",
        "quantity",
        "unit_price",
        "total_price",
    )

    search_fields = (
        "product_name",
    )


# =========================
# Customer
# =========================

@admin.register(Customer)
class CustomerAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "mobile",
        "created_at",
    )

    search_fields = (
        "first_name",
        "last_name",
        "mobile",
    )

    date_hierarchy = (
        "created_at"
    )


# =========================
# Customer Transaction
# =========================

@admin.register(CustomerTransaction)
class CustomerTransactionAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "customer",
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
        "customer__first_name",
        "customer__last_name",
    )

    date_hierarchy = (
        "created_at"
    )


# =========================
# Expense
# =========================

@admin.register(Expense)
class ExpenseAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "title",
        "expense_type",
        "cashbox",
        "amount",
        "expense_date",
    )

    list_filter = (
        "expense_type",
        "expense_date",
    )

    search_fields = (
        "title",
    )

    date_hierarchy = (
        "expense_date"
    )


# =========================
# Cash Box
# =========================

@admin.register(CashBox)
class CashBoxAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "name",
        "store",
        "balance",
        "created_at",
    )

    list_filter = (
        "store",
    )

    search_fields = (
        "name",
    )


# =========================
# Cash Box Transaction
# =========================

@admin.register(CashBoxTransaction)
class CashBoxTransactionAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "cashbox",
        "transaction_type",
        "amount",
        "reference_id",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "cashbox",
        "created_at",
    )

    search_fields = (
        "description",
    )

    date_hierarchy = (
        "created_at"
    )


# =========================
# Cash Transfer
# =========================

@admin.register(CashTransfer)
class CashTransferAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "from_cashbox",
        "to_cashbox",
        "amount",
        "created_by",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "description",
    )

    date_hierarchy = (
        "created_at"
    )

