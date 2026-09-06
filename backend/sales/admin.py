from django.contrib import admin
from .models import (
    Cart, CartItem, Order, OrderItem, Payment, Customer, CustomerTransaction,
    Expense, CashBox, CashBoxTransaction, CashTransfer, OrderCancellation,
)

MODEL_NAMES = {
    Cart: ("سبد خرید", "سبدهای خرید"),
    CartItem: ("آیتم سبد خرید", "آیتم‌های سبد خرید"),
    Order: ("سفارش", "سفارش‌ها"),
    OrderItem: ("آیتم سفارش", "آیتم‌های سفارش"),
    Payment: ("پرداخت", "پرداخت‌ها"),
    Customer: ("مشتری", "مشتریان"),
    CustomerTransaction: ("تراکنش مشتری", "تراکنش‌های مشتری"),
    Expense: ("هزینه", "هزینه‌ها"),
    CashBox: ("صندوق", "صندوق‌ها"),
    CashBoxTransaction: ("تراکنش صندوق", "تراکنش‌های صندوق"),
    CashTransfer: ("انتقال صندوق", "انتقال‌های صندوق"),
    OrderCancellation: ("تاریخچه لغو فروش", "تاریخچه لغو فروش‌ها"),
}
for model, names in MODEL_NAMES.items():
    model._meta.verbose_name, model._meta.verbose_name_plural = names

class BaseAdmin(admin.ModelAdmin):
    list_per_page = 25

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    show_change_link = True

@admin.register(Cart)
class CartAdmin(BaseAdmin):
    list_display = ("id", "store", "customer", "user", "created_at", "updated_at")
    list_filter = ("store", "created_at", "updated_at")
    search_fields = ("customer__first_name", "customer__last_name", "customer__mobile", "user__username", "store__name")
    ordering = ("-updated_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    inlines = (CartItemInline,)

@admin.register(CartItem)
class CartItemAdmin(BaseAdmin):
    list_display = ("id", "cart", "product", "quantity", "unit_price", "discount_percent", "total_price")
    list_filter = ("cart__store", "discount_percent", "created_at")
    search_fields = ("product__name", "product__barcode", "cart__user__username")
    ordering = ("-id",)
    readonly_fields = ("created_at", "updated_at", "discount_amount", "final_unit_price", "total_price_before_discount", "total_discount_amount", "total_price")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    show_change_link = True

@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = ("id", "store", "customer", "user", "status", "total_before_discount", "total_discount", "total_price", "created_at")
    list_filter = ("store", "status", "created_at")
    search_fields = ("customer__first_name", "customer__last_name", "customer__mobile", "user__username")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    inlines = (OrderItemInline,)

@admin.register(OrderItem)
class OrderItemAdmin(BaseAdmin):
    list_display = ("id", "order", "product", "product_name", "quantity", "unit_price", "purchase_price", "discount_percent", "total_price")
    list_filter = ("order__store", "created_at")
    search_fields = ("product_name", "product__name", "product__barcode")
    ordering = ("-id",)
    readonly_fields = ("created_at",)

@admin.register(OrderCancellation)
class OrderCancellationAdmin(BaseAdmin):
    list_display = ("id", "order", "cancelled_by", "cancelled_at", "reason")
    list_filter = ("cancelled_at", "order__store")
    search_fields = ("order__id", "cancelled_by__username", "reason")
    ordering = ("-cancelled_at", "-id")
    date_hierarchy = "cancelled_at"
    readonly_fields = ("order", "cancelled_by", "cancelled_at", "reason")

@admin.register(Payment)
class PaymentAdmin(BaseAdmin):
    list_display = ("id", "order", "method", "amount", "cashbox", "created_at")
    list_filter = ("method", "order__store", "cashbox", "created_at")
    search_fields = ("order__id", "cashbox__name", "order__customer__first_name", "order__customer__last_name")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

@admin.register(Customer)
class CustomerAdmin(BaseAdmin):
    list_display = ("id", "store", "first_name", "last_name", "mobile", "created_at")
    list_filter = ("store", "created_at")
    search_fields = ("first_name", "last_name", "mobile", "address", "store__name")
    ordering = ("-id",)
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

@admin.register(CustomerTransaction)
class CustomerTransactionAdmin(BaseAdmin):
    list_display = ("id", "customer", "store", "transaction_type", "amount", "reference_id", "created_at")
    list_filter = ("store", "transaction_type", "created_at")
    search_fields = ("customer__first_name", "customer__last_name", "customer__mobile", "description")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

@admin.register(Expense)
class ExpenseAdmin(BaseAdmin):
    list_display = ("id", "store", "title", "expense_type", "cashbox", "amount", "expense_date", "user")
    list_filter = ("store", "expense_type", "cashbox", "expense_date")
    search_fields = ("title", "description", "user__username", "cashbox__name")
    ordering = ("-expense_date", "-id")
    date_hierarchy = "expense_date"
    readonly_fields = ("created_at",)

@admin.register(CashBox)
class CashBoxAdmin(BaseAdmin):
    list_display = ("id", "name", "store", "balance", "created_at", "updated_at")
    list_filter = ("store", "created_at")
    search_fields = ("name", "description", "store__name", "store__code")
    ordering = ("store", "name", "id")
    readonly_fields = ("created_at", "updated_at")

@admin.register(CashBoxTransaction)
class CashBoxTransactionAdmin(BaseAdmin):
    list_display = ("id", "cashbox", "transaction_type", "amount", "reference_id", "created_at")
    list_filter = ("cashbox__store", "cashbox", "transaction_type", "created_at")
    search_fields = ("description", "cashbox__name")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

@admin.register(CashTransfer)
class CashTransferAdmin(BaseAdmin):
    list_display = ("id", "from_cashbox", "to_cashbox", "amount", "created_by", "created_at")
    list_filter = ("from_cashbox__store", "to_cashbox__store", "created_at")
    search_fields = ("description", "created_by__username", "from_cashbox__name", "to_cashbox__name")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
