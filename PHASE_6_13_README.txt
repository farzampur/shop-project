Phase 6.13 — Integrity Constraint Reconciliation (fixed)

این بسته با migration graph فعلی پروژه هماهنگ شده است.

علت خطای قبلی:
- در پروژه فعلی migration شماره 0022 از قبل وجود دارد.
- بسته قبلی یک migration دیگر با همان شماره 0022 اضافه کرده بود.
- بنابراین Django دو leaf migration دید و خطای Conflicting migrations داد.
- همچنین migration 0024 به‌صورت صریح constraint مربوط به مثبت بودن ProductPrice.amount را حذف می‌کند؛
  بنابراین تست قدیمی «amount=0 باید رد شود» دیگر با وضعیت فعلی پروژه سازگار نیست.

این نسخه:
1) migration جدید 0022 اضافه نمی‌کند.
2) تست قدیمی 6.9.4 را با قانون source/destination متفاوت هماهنگ می‌کند.
3) تست قدیمی 6.9.10 را با constraint واقعی فعلی ProductPrice هماهنگ می‌کند.
4) تست‌های Phase 6.13 را روی constraintهای موجود و migration graph فعلی اجرا می‌کند.

فقط این فایل‌ها را روی پروژه فعلی جایگزین/اضافه کنید.

تست هدفمند:
python manage.py test products.test_phase6_9_4_f products.test_phase6_9_10 products.test_phase6_13

فعلاً full test نزن.
