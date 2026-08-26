from django.contrib import admin

from .models import UserStore


@admin.register(UserStore)
class UserStoreAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "store",
        "role",
        "created_at",
    )

    list_filter = (
        "store",
        "role",
    )

    search_fields = (
        "user__username",
        "store__name",
        "store__code",
    )