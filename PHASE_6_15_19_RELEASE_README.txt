SHOPPROJECT — PHASE 6.15 TO 6.19 RELEASE HARDENING BUNDLE

این بسته مراحل 6.15 تا 6.19 را در یک Bundle تجمیع می‌کند.

6.15 Security & Abuse Hardening
- StockTransfer و ProductPrice دیگر فقط با IsAuthenticated محافظت نمی‌شوند؛ ماتریس نقش فروشگاه به permission متصل شد.
- دسترسی mutation برای ProductPrice فقط manager است.
- دسترسی mutation انتقال موجودی برای manager/warehouse و حذف فقط manager است.

6.16 Financial & Inventory Integrity
- مسیرهای حساس موجودی/مالی قبلی حفظ شده‌اند؛ این بسته regression/security checks تکمیلی را اضافه می‌کند.
- هیچ endpoint عمومی برای ساخت تراکنش مالی حساس ایجاد نشده است.

6.17 Frontend Production Audit
- Axios API و Auth client دارای timeout پانزده‌ثانیه‌ای شدند تا درخواست‌های شبکه بی‌نهایت معلق نمانند.
- refresh token همچنان فقط در HttpOnly cookie باقی می‌ماند و access token در حافظه است.

6.18 Backend Production Readiness
- SameSite برای session/CSRF صریح شد.
- Cross-Origin-Opener-Policy و Cross-Origin-Resource-Policy اضافه شد.
- تنظیمات secure در حالت DEBUG=False فعال باقی می‌مانند.

6.19 Final Regression
- تست‌های release در products/test_phase6_15_19_release.py قرار گرفته‌اند.
- فول‌تست نهایی باید فقط در محیط توسعه خود پروژه اجرا شود؛ این بسته به‌جای اجرای مجدد فول‌تست، تست‌های متمرکز release را فراهم می‌کند.

تست متمرکز:
python manage.py test products.test_phase6_15_19_release

بررسی Production:
python manage.py check --deploy

Frontend:
npm run build

نکته:
این ZIP فقط فایل‌های پروژه موجود در Snapshot فعلی را شامل می‌شود و فایل‌های frontend/package.json و تنظیمات Vite در Snapshot ضمیمه‌شده موجود نبودند. بنابراین npm run build باید در همان working tree کامل پروژه کاربر اجرا شود.

Commit message پیشنهادی:
harden release security and production readiness
