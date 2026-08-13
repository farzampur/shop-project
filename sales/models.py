from django.db import models
from django.contrib.auth.models import User

from core.models import Store
from products.models import Product

class Customer(models.Model):

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="customers"
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    mobile = models.CharField(
        max_length=20,
        unique=True
    )

    address = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.first_name} "
            f"{self.last_name}"
        )
        
        
        
class Cart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="carts",
        verbose_name="کاربر"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="carts",
        verbose_name="فروشگاه"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self):
        return f"{self.user.username} - {self.store.name}"


class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سبد خرید"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="cart_items",
        verbose_name="محصول"
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=1,
        verbose_name="تعداد"
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="قیمت واحد قبل از تخفیف"
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="درصد تخفیف"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "آیتم سبد خرید"
        verbose_name_plural = "آیتم‌های سبد خرید"

        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_cart_product"
            )
        ]

    @property
    def discount_amount(self):
        return self.unit_price * self.discount_percent / 100

    @property
    def final_unit_price(self):
        return self.unit_price - self.discount_amount

    @property
    def total_price_before_discount(self):
        return self.unit_price * self.quantity

    @property
    def total_discount_amount(self):
        return self.discount_amount * self.quantity

    @property
    def total_price(self):
        return self.final_unit_price * self.quantity

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"
        
        
        
class Order(models.Model):

    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("confirmed", "تایید شده"),
        ("paid", "پرداخت شده"),
        ("cancelled", "لغو شده"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="کاربر"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="فروشگاه"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت"
    )

    total_before_discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ قبل از تخفیف"
    )

    total_discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ تخفیف"
    )

    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ نهایی"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders"
    )

    def __str__(self):
        return f"سفارش {self.id} - {self.user.username}"

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"        
        
        
        
class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="سفارش"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="کالا"
    )

    product_name = models.CharField(
        max_length=200,
        verbose_name="نام کالا"
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        verbose_name="تعداد"
    )

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="قیمت واحد"
    )

    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="درصد تخفیف"
    )

    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ تخفیف واحد"
    )

    total_price_before_discount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ قبل از تخفیف"
    )

    total_discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="کل تخفیف"
    )

    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ نهایی"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.product_name} - سفارش {self.order_id}"

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"



class Expense(models.Model):

    EXPENSE_TYPES = [
        ("rent", "اجاره"),
        ("salary", "حقوق"),
        ("transport", "حمل و نقل"),
        ("utility", "آب و برق و گاز"),
        ("purchase", "هزینه خرید"),
        ("other", "سایر"),
    ]

    store = models.ForeignKey(
        "core.Store",
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_TYPES
    )

    title = models.CharField(
        max_length=200
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    expense_date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-expense_date"]

    def __str__(self):
        return self.title        
        





        