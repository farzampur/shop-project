from django.db import models
from django.contrib.auth.models import User

class Store(models.Model):
    name = models.CharField(max_length=150, verbose_name="نام فروشگاه")
    code = models.CharField(max_length=50, unique=True, verbose_name="کد فروشگاه")
    phone = models.CharField(max_length=20, blank=True, verbose_name="تلفن")
    address = models.TextField(blank=True, verbose_name="آدرس")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    def __str__(self): return self.name
    class Meta:
        verbose_name = "فروشگاه"; verbose_name_plural = "فروشگاه‌ها"; ordering = ["name"]

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "ایجاد"), ("update", "ویرایش"), ("delete", "حذف"),
        ("adjust", "تعدیل"), ("payment", "پرداخت"), ("cancel", "لغو"),
        ("close", "بستن صندوق"), ("login", "ورود"), ("other", "سایر"),
    ]
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="audit_logs")
    store = models.ForeignKey(Store, on_delete=models.PROTECT, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "گزارش فعالیت"
        verbose_name_plural = "گزارش فعالیت‌ها"
    def __str__(self): return f"{self.user} - {self.action} - {self.model_name}"
