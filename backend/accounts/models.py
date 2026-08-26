from django.db import models
from django.contrib.auth.models import User

from core.models import Store


class UserStore(models.Model):

    ROLE_CHOICES = [
        ("manager", "مدیر فروشگاه"),
        ("seller", "فروشنده"),
        ("cashier", "صندوقدار"),
        ("warehouse", "انباردار"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_stores",
        verbose_name="کاربر"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="store_users",
        verbose_name="فروشگاه"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="seller",
        verbose_name="نقش"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "دسترسی کاربر به فروشگاه"
        verbose_name_plural = "دسترسی کاربران به فروشگاه‌ها"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "store"],
                name="unique_user_store"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.store.name} - {self.get_role_display()}"