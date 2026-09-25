# ماژول حسابداری مستقل ShopProject

این ماژول یک هسته حسابداری مستقل و Store-scoped است. منطق قدیمی فروش، خرید، موجودی، مشتری، تأمین‌کننده و صندوق مالکیت داده‌های خود را حفظ می‌کند.

## وضعیت اتصال خودکار

`ACCOUNTING_AUTO_POSTING` در تنظیمات پیش‌فرض `False` است. بنابراین نصب و اجرای این ماژول به‌خودی‌خود هیچ تراکنش قدیمی را تغییر نمی‌دهد و روی مسیرهای قبلی اثر رفتاری ندارد.

پس از تکمیل تست Backend و سپس تست Frontend می‌توان این گزینه را فعال کرد تا Signalهای idempotent ثبت‌های حسابداری را برای عملیات جدید ایجاد کنند.

## API

- `/api/accounting/setup/`
- `/api/accounting/sync/`
- `/api/accounting/accounts/`
- `/api/accounting/periods/`
- `/api/accounting/entries/`
- `/api/accounting/trial-balance/`
- `/api/accounting/general-ledger/`
- `/api/accounting/profit-loss/`
- `/api/accounting/balance-sheet/`

تمام مسیرها بر اساس فروشگاه مورد درخواست Scope می‌شوند و نقش مدیر فروشگاه را می‌خواهند.
