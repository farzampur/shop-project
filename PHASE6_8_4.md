# Phase 6.8.4 — Production Configuration & Final Release Hardening

## تغییرات

- `SECRET_KEY` از environment خوانده می‌شود و دیگر secret واقعی داخل settings نیست.
- `DJANGO_DEBUG`، `DJANGO_ALLOWED_HOSTS` و CORS/CSRF origins قابل تنظیم از environment هستند.
- رمز دیتابیس دیگر مقدار پیش‌فرض hard-coded ندارد.
- تنظیمات HTTPS، Secure Cookie، HSTS و reverse-proxy به‌صورت environment-driven اضافه شد.
- `X-Frame-Options=DENY`، `X-Content-Type-Options=nosniff` و Referrer Policy فعال شدند.
- تنظیمات ایمیل از ساختار نامعتبر `MAILERS` به تنظیمات استاندارد Django Email تبدیل شد.
- فایل `backend/.env.example` برای deployment اضافه شد.

## نکته

این patch بر اساس آخرین artifact فاز 6.8.3 ساخته شده است؛ آن artifact شامل backend بود و frontend در آن موجود نبود، بنابراین build واقعی frontend را در این ZIP ادعا نمی‌کنیم.

## بررسی

```bash
cd C:\ShopProject\backend
python manage.py check
python manage.py test core.test_phase6_8_4
python manage.py check --deploy
```

`check --deploy` در محیط production ممکن است warningهای deployment وابسته به زیرساخت (HTTPS/domain/proxy) نشان دهد؛ این موارد باید با مقادیر واقعی `.env` تنظیم شوند.
