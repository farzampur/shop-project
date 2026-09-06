from django.contrib import admin
from .models import Store

Store._meta.verbose_name = "فروشگاه"
Store._meta.verbose_name_plural = "فروشگاه‌ها"

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "phone", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "code", "phone", "address")
    ordering = ("name", "id")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 25

admin.site.site_header = "مدیریت فروشگاه"
admin.site.site_title = "مدیریت فروشگاه"
admin.site.index_title = "پنل مدیریت سیستم فروشگاه"
