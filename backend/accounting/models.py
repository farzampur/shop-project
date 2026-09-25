from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Account(models.Model):
    TYPE_ASSET = "asset"
    TYPE_LIABILITY = "liability"
    TYPE_EQUITY = "equity"
    TYPE_REVENUE = "revenue"
    TYPE_EXPENSE = "expense"
    TYPE_CHOICES = [
        (TYPE_ASSET, "دارایی"),
        (TYPE_LIABILITY, "بدهی"),
        (TYPE_EQUITY, "سرمایه"),
        (TYPE_REVENUE, "درآمد"),
        (TYPE_EXPENSE, "هزینه"),
    ]

    store = models.ForeignKey(
        "core.Store",
        on_delete=models.PROTECT,
        related_name="accounting_accounts",
        verbose_name="فروشگاه",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="حساب مادر",
    )
    code = models.CharField(max_length=20, verbose_name="کد حساب")
    name = models.CharField(max_length=200, verbose_name="نام حساب")
    account_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="نوع حساب")
    is_group = models.BooleanField(default=False, verbose_name="حساب گروه")
    is_system = models.BooleanField(default=False, verbose_name="حساب سیستمی")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        ordering = ["code", "id"]
        verbose_name = "حساب"
        verbose_name_plural = "حساب‌ها"
        constraints = [
            models.UniqueConstraint(fields=["store", "code"], name="accounting_unique_account_code_per_store"),
            models.CheckConstraint(condition=~Q(code=""), name="accounting_account_code_nonempty"),
            models.CheckConstraint(condition=~Q(name=""), name="accounting_account_name_nonempty"),
        ]

    def clean(self):
        if self.parent_id == self.pk:
            raise ValidationError("حساب نمی‌تواند خودش را به‌عنوان حساب مادر انتخاب کند.")
        if self.parent and self.parent.store_id != self.store_id:
            raise ValidationError("حساب مادر باید متعلق به همان فروشگاه باشد.")
        if not self.is_group and self.children.exists():
            raise ValidationError("حسابی که زیرحساب دارد باید به‌صورت گروهی باشد.")
        if self.is_group and self.journal_lines.exists():
            raise ValidationError("حساب گروهی نباید دارای سند ثبت‌شده باشد.")

    def __str__(self):
        return f"{self.code} - {self.name}"


class AccountingPeriod(models.Model):
    store = models.ForeignKey(
        "core.Store",
        on_delete=models.PROTECT,
        related_name="accounting_periods",
        verbose_name="فروشگاه",
    )
    name = models.CharField(max_length=100, verbose_name="نام دوره")
    start_date = models.DateField(verbose_name="تاریخ شروع")
    end_date = models.DateField(verbose_name="تاریخ پایان")
    is_closed = models.BooleanField(default=False, verbose_name="بسته")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان بستن")
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="closed_accounting_periods",
        verbose_name="بسته‌شده توسط",
    )

    class Meta:
        ordering = ["-start_date", "-id"]
        verbose_name = "دوره مالی"
        verbose_name_plural = "دوره‌های مالی"
        constraints = [
            models.UniqueConstraint(fields=["store", "name"], name="accounting_unique_period_name_per_store"),
            models.CheckConstraint(condition=Q(start_date__lte=models.F("end_date")), name="accounting_period_dates_valid"),
        ]

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError("تاریخ شروع دوره نمی‌تواند بعد از تاریخ پایان باشد.")
        overlapping = AccountingPeriod.objects.filter(
            store=self.store,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError("بازه این دوره مالی با یک دوره دیگر همپوشانی دارد.")

    def __str__(self):
        return f"{self.store.name} - {self.name}"


class JournalEntry(models.Model):
    STATUS_POSTED = "posted"
    STATUS_REVERSED = "reversed"
    STATUS_CHOICES = [
        (STATUS_POSTED, "ثبت قطعی"),
        (STATUS_REVERSED, "برگشت‌خورده"),
    ]

    store = models.ForeignKey(
        "core.Store",
        on_delete=models.PROTECT,
        related_name="accounting_entries",
        verbose_name="فروشگاه",
    )
    period = models.ForeignKey(
        AccountingPeriod,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name="دوره مالی",
    )
    entry_number = models.PositiveIntegerField(verbose_name="شماره سند")
    entry_date = models.DateField(verbose_name="تاریخ سند")
    description = models.CharField(max_length=500, verbose_name="شرح")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_POSTED, verbose_name="وضعیت")
    source_type = models.CharField(max_length=80, blank=True, verbose_name="نوع مرجع")
    source_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="شناسه مرجع")
    source_key = models.CharField(max_length=180, blank=True, verbose_name="کلید مرجع")
    reversal_of = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reversal_entry",
        verbose_name="سند مبنا برای برگشت",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accounting_entries_created",
        verbose_name="ثبت‌کننده",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        ordering = ["-entry_date", "-entry_number", "-id"]
        verbose_name = "سند حسابداری"
        verbose_name_plural = "اسناد حسابداری"
        constraints = [
            models.UniqueConstraint(fields=["store", "entry_number"], name="accounting_unique_entry_number_per_store"),
            models.UniqueConstraint(fields=["store", "source_key"], condition=~Q(source_key=""), name="accounting_unique_source_key_per_store"),
            models.CheckConstraint(condition=Q(entry_number__gt=0), name="accounting_entry_number_positive"),
            models.CheckConstraint(condition=~Q(description=""), name="accounting_entry_description_nonempty"),
        ]

    def clean(self):
        if self.period_id and self.period.store_id != self.store_id:
            raise ValidationError("دوره مالی باید متعلق به همان فروشگاه سند باشد.")
        if self.period_id and not (self.period.start_date <= self.entry_date <= self.period.end_date):
            raise ValidationError("تاریخ سند خارج از بازه دوره مالی است.")
        if self.reversal_of_id and self.reversal_of.store_id != self.store_id:
            raise ValidationError("سند برگشتی باید متعلق به همان فروشگاه باشد.")

    def __str__(self):
        return f"{self.store.name} - سند {self.entry_number}"


class JournalLine(models.Model):
    PARTY_CUSTOMER = "customer"
    PARTY_SUPPLIER = "supplier"
    PARTY_CASHBOX = "cashbox"
    PARTY_USER = "user"
    PARTY_CHOICES = [
        (PARTY_CUSTOMER, "مشتری"),
        (PARTY_SUPPLIER, "تأمین‌کننده"),
        (PARTY_CASHBOX, "صندوق"),
        (PARTY_USER, "کاربر"),
    ]

    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,
        related_name="lines",
        verbose_name="سند",
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="journal_lines",
        verbose_name="حساب",
    )
    description = models.CharField(max_length=300, blank=True, verbose_name="شرح")
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"), verbose_name="بدهکار")
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"), verbose_name="بستانکار")
    party_type = models.CharField(max_length=20, choices=PARTY_CHOICES, blank=True, verbose_name="نوع طرف حساب")
    party_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="شناسه طرف حساب")

    class Meta:
        ordering = ["id"]
        verbose_name = "ردیف سند حسابداری"
        verbose_name_plural = "ردیف‌های سند حسابداری"
        constraints = [
            models.CheckConstraint(condition=Q(debit__gte=0), name="accounting_line_debit_nonnegative"),
            models.CheckConstraint(condition=Q(credit__gte=0), name="accounting_line_credit_nonnegative"),
            models.CheckConstraint(condition=(Q(debit__gt=0) & Q(credit=0)) | (Q(credit__gt=0) & Q(debit=0)), name="accounting_line_one_side_only"),
        ]

    def clean(self):
        if self.account_id and self.entry_id and self.account.store_id != self.entry.store_id:
            raise ValidationError("حساب و سند باید متعلق به یک فروشگاه باشند.")
        if self.account_id and self.account.is_group:
            raise ValidationError("ثبت سند روی حساب گروهی مجاز نیست.")
        if self.party_type and not self.party_id:
            raise ValidationError("برای طرف حساب، شناسه طرف حساب الزامی است.")
        if self.party_id and not self.party_type:
            raise ValidationError("نوع طرف حساب برای شناسه طرف حساب الزامی است.")
