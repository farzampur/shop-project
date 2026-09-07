from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User, Group
from .models import UserStore

UserStore._meta.verbose_name = "دسترسی کاربر به فروشگاه"
UserStore._meta.verbose_name_plural = "دسترسی کاربران به فروشگاه‌ها"

@admin.register(UserStore)
class UserStoreAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "store", "role", "is_active", "created_at")
    list_filter = ("store", "role", "is_active", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "store__name", "store__code")
    ordering = ("-id",)
    readonly_fields = ("created_at",)
    list_per_page = 25

# فارسی‌سازی و مدیریت کاربران و گروه‌های خود جنگو
User._meta.verbose_name = "کاربر"
User._meta.verbose_name_plural = "کاربران"
Group._meta.verbose_name = "گروه دسترسی"
Group._meta.verbose_name_plural = "گروه‌های دسترسی"

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "username", "first_name", "last_name", "is_staff", "is_active", "last_login", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    list_per_page = 25

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    filter_horizontal = ("permissions",)
    ordering = ("name",)
