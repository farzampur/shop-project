from django.contrib import admin

from .models import Account, AccountingPeriod, JournalEntry, JournalLine


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0
    can_delete = False


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("store", "code", "name", "account_type", "is_group", "is_system", "is_active")
    list_filter = ("store", "account_type", "is_group", "is_active")
    search_fields = ("code", "name")


@admin.register(AccountingPeriod)
class AccountingPeriodAdmin(admin.ModelAdmin):
    list_display = ("store", "name", "start_date", "end_date", "is_closed")
    list_filter = ("store", "is_closed")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("store", "entry_number", "entry_date", "description", "status", "source_type")
    list_filter = ("store", "status", "source_type")
    search_fields = ("description", "source_key")
    readonly_fields = ("entry_number", "created_by", "created_at")
    inlines = [JournalLineInline]
