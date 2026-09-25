from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0003_auditlog_integrity_constraints"),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, verbose_name="کد حساب")),
                ("name", models.CharField(max_length=200, verbose_name="نام حساب")),
                ("account_type", models.CharField(choices=[("asset", "دارایی"), ("liability", "بدهی"), ("equity", "سرمایه"), ("revenue", "درآمد"), ("expense", "هزینه")], max_length=20, verbose_name="نوع حساب")),
                ("is_group", models.BooleanField(default=False, verbose_name="حساب گروه")),
                ("is_system", models.BooleanField(default=False, verbose_name="حساب سیستمی")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")),
                ("parent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="children", to="accounting.account", verbose_name="حساب مادر")),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="accounting_accounts", to="core.store", verbose_name="فروشگاه")),
            ],
            options={"ordering": ["code", "id"], "verbose_name": "حساب", "verbose_name_plural": "حساب‌ها"},
        ),
        migrations.CreateModel(
            name="AccountingPeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="نام دوره")),
                ("start_date", models.DateField(verbose_name="تاریخ شروع")),
                ("end_date", models.DateField(verbose_name="تاریخ پایان")),
                ("is_closed", models.BooleanField(default=False, verbose_name="بسته")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")),
                ("closed_at", models.DateTimeField(blank=True, null=True, verbose_name="زمان بستن")),
                ("closed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="closed_accounting_periods", to=settings.AUTH_USER_MODEL, verbose_name="بسته‌شده توسط")),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="accounting_periods", to="core.store", verbose_name="فروشگاه")),
            ],
            options={"ordering": ["-start_date", "-id"], "verbose_name": "دوره مالی", "verbose_name_plural": "دوره‌های مالی"},
        ),
        migrations.CreateModel(
            name="JournalEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entry_number", models.PositiveIntegerField(verbose_name="شماره سند")),
                ("entry_date", models.DateField(verbose_name="تاریخ سند")),
                ("description", models.CharField(max_length=500, verbose_name="شرح")),
                ("status", models.CharField(choices=[("posted", "ثبت قطعی"), ("reversed", "برگشت‌خورده")], default="posted", max_length=20, verbose_name="وضعیت")),
                ("source_type", models.CharField(blank=True, max_length=80, verbose_name="نوع مرجع")),
                ("source_id", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="شناسه مرجع")),
                ("source_key", models.CharField(blank=True, max_length=180, verbose_name="کلید مرجع")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="accounting_entries_created", to=settings.AUTH_USER_MODEL, verbose_name="ثبت‌کننده")),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entries", to="accounting.accountingperiod", verbose_name="دوره مالی")),
                ("reversal_of", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reversal_entry", to="accounting.journalentry", verbose_name="سند مبنا برای برگشت")),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="accounting_entries", to="core.store", verbose_name="فروشگاه")),
            ],
            options={"ordering": ["-entry_date", "-entry_number", "-id"], "verbose_name": "سند حسابداری", "verbose_name_plural": "اسناد حسابداری"},
        ),
        migrations.CreateModel(
            name="JournalLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(blank=True, max_length=300, verbose_name="شرح")),
                ("debit", models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name="بدهکار")),
                ("credit", models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name="بستانکار")),
                ("party_type", models.CharField(blank=True, choices=[("customer", "مشتری"), ("supplier", "تأمین‌کننده"), ("cashbox", "صندوق"), ("user", "کاربر")], max_length=20, verbose_name="نوع طرف حساب")),
                ("party_id", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="شناسه طرف حساب")),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="journal_lines", to="accounting.account", verbose_name="حساب")),
                ("entry", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lines", to="accounting.journalentry", verbose_name="سند")),
            ],
            options={"ordering": ["id"], "verbose_name": "ردیف سند حسابداری", "verbose_name_plural": "ردیف‌های سند حسابداری"},
        ),
        migrations.AddConstraint(model_name="account", constraint=models.UniqueConstraint(fields=("store", "code"), name="accounting_unique_account_code_per_store")),
        migrations.AddConstraint(model_name="account", constraint=models.CheckConstraint(condition=~models.Q(code=""), name="accounting_account_code_nonempty")),
        migrations.AddConstraint(model_name="account", constraint=models.CheckConstraint(condition=~models.Q(name=""), name="accounting_account_name_nonempty")),
        migrations.AddConstraint(model_name="accountingperiod", constraint=models.UniqueConstraint(fields=("store", "name"), name="accounting_unique_period_name_per_store")),
        migrations.AddConstraint(model_name="accountingperiod", constraint=models.CheckConstraint(condition=models.Q(start_date__lte=models.F("end_date")), name="accounting_period_dates_valid")),
        migrations.AddConstraint(model_name="journalentry", constraint=models.UniqueConstraint(fields=("store", "entry_number"), name="accounting_unique_entry_number_per_store")),
        migrations.AddConstraint(model_name="journalentry", constraint=models.UniqueConstraint(condition=~models.Q(source_key=""), fields=("store", "source_key"), name="accounting_unique_source_key_per_store")),
        migrations.AddConstraint(model_name="journalentry", constraint=models.CheckConstraint(condition=models.Q(entry_number__gt=0), name="accounting_entry_number_positive")),
        migrations.AddConstraint(model_name="journalentry", constraint=models.CheckConstraint(condition=~models.Q(description=""), name="accounting_entry_description_nonempty")),
        migrations.AddConstraint(model_name="journalline", constraint=models.CheckConstraint(condition=models.Q(debit__gte=0), name="accounting_line_debit_nonnegative")),
        migrations.AddConstraint(model_name="journalline", constraint=models.CheckConstraint(condition=models.Q(credit__gte=0), name="accounting_line_credit_nonnegative")),
        migrations.AddConstraint(model_name="journalline", constraint=models.CheckConstraint(condition=(models.Q(debit__gt=0) & models.Q(credit=0)) | (models.Q(credit__gt=0) & models.Q(debit=0)), name="accounting_line_one_side_only")),
    ]
