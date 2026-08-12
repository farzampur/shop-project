from django.db import models
from django.contrib.auth.models import User

from core.models import Store
from products.models import Product


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