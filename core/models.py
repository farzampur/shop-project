from django.db import models


class Store(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="نام فروشگاه"
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="کد فروشگاه"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="تلفن"
    )

    address = models.TextField(
        blank=True,
        verbose_name="آدرس"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین ویرایش"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "فروشگاه"
        verbose_name_plural = "فروشگاه‌ها"
        ordering = ["name"]
        
        
        