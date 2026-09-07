from django.contrib import admin
from .models import Store, AuditLog

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "phone", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "code", "phone", "address")
    ordering = ("name", "id")
    readonly_fields = ("created_at", "updated_at")

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "user", "store", "action", "model_name", "object_id", "description")
    list_filter = ("action", "model_name", "store", "created_at")
    search_fields = ("user__username", "description", "model_name", "object_id")
    readonly_fields = ("user", "store", "action", "model_name", "object_id", "description", "metadata", "created_at")
    ordering = ("-created_at", "-id")

admin.site.site_header = "مدیریت فروشگاه"
admin.site.site_title = "مدیریت فروشگاه"
admin.site.index_title = "پنل مدیریت سیستم فروشگاه"
