# Phase 4 — Business Management

- مدیریتی‌تر شدن Dashboard با KPIهای فروش، سود و هزینه
- مدیریت حرفه‌ای موجودی و ثبت تعدیل همراه با گردش کالا
- ماژول مستقل تأمین‌کنندگان و گردش حساب
- توسعه صندوق: واریز/برداشت، انتقال بین صندوق‌ها و ثبت هزینه
- حفظ گزارش‌های حرفه‌ای Phase 3
- حفظ Store Isolation و Role-based navigation
- اصلاح خطای SupplierPaymentViewSet در محاسبه بدهی

## Checkpoint
Phase 3 checkpoint: `a9a124e`
Phase 4 implementation commits: `87a5181`, `03ffed4`


## Phase 4 automated tests

Added `products/test_phase4.py` and `sales/test_phase4.py` with 20 new tests covering:
- inventory store isolation and adjustment ledger
- negative stock adjustment protection and role permission
- purchase receiving idempotency and supplier debt
- supplier payment/cashbox integration and limits
- purchase returns and quantity limits
- cashbox deposits/withdrawals and insufficient-balance protection
- same-store cash transfers and cross-store rejection
- expenses and cashbox reconciliation behavior
- sales summary KPIs, dashboard totals, and inaccessible-store rejection

Expected total test count after these additions: 52 tests (32 existing + 20 Phase 4 tests).


## Final polish
- Dashboard KPIs are now isolated to the active/selected store when `store` is supplied.
- Dashboard gross profit and expenses are calculated for the current month, matching the monthly sales KPI.
- Low-stock detection uses each inventory item's configured `min_quantity` instead of a hard-coded threshold.
- Inventory adjustment uses the typed frontend service layer instead of a page-level Axios call.
- Invalid or inaccessible dashboard store IDs are rejected server-side.
- Frontend build dependencies could not be installed in the isolated validation environment; backend `compileall` passed.



# Phase 5 — Advanced Business & Operations

## Delivered
- Audit log for sensitive operational and financial actions.
- Daily cashbox closing with expected vs counted balance and variance.
- CSV export for sales reporting.
- Audit trail on inventory adjustments, expenses, cash transactions, cash transfers, supplier payments and order cancellation.
- Manager-only activity log screen.
- Manager/cashier daily cash close screen.
- Phase 5 visual polish: RTL layout, glass-like header, refined cards, tables, buttons and form controls.

## Migrations
- `core.0002_auditlog`
- `sales.0014_cashdayclose`

## Security
Audit data is store-isolated through the authenticated user's accessible stores. Daily closing is restricted to manager/cashier roles.

## Validation
- Backend `python -m compileall` passes in the build environment.
- Frontend type/build could not be executed in the isolated build environment because the frontend `node_modules` tree is not installed.

# Phase 6 — 6.1 + 6.2

## 6.1 کاربران و کارکنان
- مدیریت دسترسی کاربران به فروشگاه توسط مدیر همان فروشگاه
- ایجاد کاربر جدید با نقش فروشنده، صندوقدار، انباردار یا مدیر
- تغییر نقش و فعال/غیرفعال کردن دسترسی هر کاربر در همان شعبه
- حذف دسترسی شعبه بدون حذف حساب کاربری اصلی
- جلوگیری از مدیریت شعبه‌ای که مدیر در آن دسترسی مدیریتی ندارد
- جلوگیری از حذف دسترسی خود مدیر
- Audit برای ایجاد/ویرایش/حذف دسترسی‌ها
- فیلتر API بر اساس فروشگاه فعال

## 6.2 مدیریت شعب
- مشاهده شعب در دسترس
- ویرایش اطلاعات شعبه توسط مدیر همان شعبه
- ایجاد شعبه فقط توسط superuser
- فعال/غیرفعال کردن شعبه فقط توسط superuser
- جلوگیری از حذف شعبه دارای سابقه دسترسی کاربران
- نمایش مدیر فعال شعبه
- ثبت Audit برای عملیات مدیریت شعب
- superuser در هویت فعلی سیستم، شعب فعال را با نقش مدیریتی مشاهده می‌کند تا پنل مدیریت شعب و کاربران قابل استفاده باشد.

## تغییرات دیتابیس
- accounts.0003_userstore_is_active

## وضعیت اعتبارسنجی
- `python -m compileall -q backend` موفق اجرا شد.
- تست Django و build فرانت‌اند در این محیط اجرا نشدند؛ وابستگی Django و `node_modules/.bin/tsc` در محیط فعلی موجود نیست.

# Phase 6.3 + 6.4 — انتقال بین شعب و قیمت‌گذاری حرفه‌ای

## 6.3 انتقال کالا
- انتقال بین شعب با وضعیت‌های پیش‌نویس، تأیید، ارسال، دریافت و لغو
- کنترل دسترسی مبدأ و مقصد
- قفل تراکنشی موجودی هنگام ارسال/دریافت
- ثبت گردش موجودی و Audit
- کالای منتقل‌شده در موجودی مقصد قابل فروش است.

## 6.4 قیمت‌گذاری
- قیمت‌های خرده‌فروشی، عمده و ویژه
- تاریخ شروع/پایان اعتبار
- قیمت خرده‌فروشی معتبر به‌صورت خودکار در سبد فروش استفاده می‌شود
- در نبود قیمت ویژه، `Product.sale_price` قیمت پایه باقی می‌ماند
- تغییرات قیمت Audit می‌شوند

## Migration
`python manage.py migrate`

## Frontend
- `/transfers` برای مدیر و انباردار
- `/pricing` برای مدیر


# ShopProject — Phase 6.8

## Final Hardening / Production Readiness

This release is based on `ShopProject-shop123-PHASE6-7-FIX.zip`.

### Included
- Unauthenticated `/api/health/` endpoint for deployment/liveness checks.
- Database connectivity is checked by the health endpoint.
- HTTP 503 is returned when the database is unavailable.
- Existing multi-store isolation, role permissions, pricing, stock transfer, financial summary and concurrency hardening from Phase 6.7 are preserved.
- Added focused Phase 6.8 production-readiness tests.

### Validation
Run from `backend`:

```bash
python manage.py check
python manage.py test core.test_phase6_8
```

For the final release gate, also run the complete backend test suite once:

```bash
python manage.py test
```

### Health endpoint

```text
GET /api/health/
```

Expected healthy response:

```json
{"status":"ok","database":"ok"}
```


# ShopProject — Phase 6.8.2

## هدف
تقویت سناریوی End-to-End و سخت‌گیری بیشتر روی Store Isolation برای عضویت‌های غیرفعال.

## تغییرات

### 1. End-to-End backend workflow test
فایل جدید:
- `backend/core/test_phase6_8_2.py`

سناریوی تست:
1. Purchase + Receive
2. Supplier debt
3. Stock Transfer: approve → ship → receive
4. Destination-store pricing
5. Cash sale
6. Sale cancellation + stock/cash reversal
7. Credit sale
8. Customer payment
9. Supplier payment
10. Financial Summary

### 2. Central Store Isolation hardening
`backend/accounts/store_access.py`
- `user_store_ids()` فقط عضویت‌های `is_active=True` و فروشگاه‌های `is_active=True` را برمی‌گرداند.
- `has_store_access()` نیز فروشگاه غیرفعال را مجاز نمی‌کند.

این تغییر روی endpointهایی که از `user_store_ids()` استفاده می‌کنند، یک لایه‌ی مرکزی برای جلوگیری از نشت اطلاعات عضویت‌های غیرفعال ایجاد می‌کند.

### 3. Purchase queryset hardening
`PurchaseViewSet.get_queryset()` علاوه بر user membership، فقط عضویت فعال و فروشگاه فعال را در نظر می‌گیرد.

## تست پیشنهادی روی پروژه محلی
از:
```bash
cd C:\ShopProject\backend
python manage.py check
python manage.py test core.test_phase6_8_2
```

بعد از موفقیت تست Phase 6.8.2، یک full suite در milestone بعدی اجرا شود.


# Phase 6.8.3 — Concurrency & Financial Integrity

این مرحله روی کاهش ریسک deadlock در عملیات همزمان و جلوگیری از دوباره‌کاری مالی/موجودی تمرکز دارد.

## تغییرات

- قفل‌گذاری موجودی‌های Checkout با ترتیب قطعی `product_id` برای کاهش ریسک deadlock در سبدهای چندکالایی.
- قفل‌گذاری موجودی‌های برگشت سفارش با ترتیب قطعی `product_id`.
- پردازش برگشت پرداخت‌های سفارش با ترتیب قطعی `cashbox_id` و سپس `id`.
- انتقال بین دو صندوق، هر دو صندوق را با ترتیب قطعی `id` قفل می‌کند؛ این کار ریسک deadlock در دو انتقال معکوس همزمان را کاهش می‌دهد.
- همچنان `select_for_update()` و `transaction.atomic()` روی عملیات حساس مالی/موجودی حفظ شده‌اند.
- وضعیت سفارش قبل از settlement دوباره با lock خوانده می‌شود تا پرداخت دوم روی سفارش پرداخت‌شده انجام نشود.
- وضعیت انتقال کالا نیز با lock بررسی می‌شود تا Ship/Receive دوباره انجام نشود.

## تست‌ها

```bash
python manage.py test sales.test_phase6_8_3
```

تست‌های این مرحله موارد زیر را پوشش می‌دهند:

1. جلوگیری از oversell و حفظ موجودی/صندوق در تلاش دوم.
2. جلوگیری از settlement دوباره یک سفارش.
3. جلوگیری از cancellation دوباره و برگشت دوباره موجودی/صندوق.
4. کنترل عدم منفی‌شدن مانده دفتر مشتری.
5. کنترل عدم منفی‌شدن مانده دفتر تأمین‌کننده.

> PASS واقعی باید با اجرای تست روی دیتابیس پروژه محلی تأیید شود.


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

# ShopProject — Price Fix (Backend + Frontend)

این نسخه بر اساس فایل `shop(2).zip` اصلاح شده است.

## Backend
- قیمت فعال/معتبر خرده‌فروشی برای هر فروشگاه از `ProductPrice` محاسبه می‌شود.
- قیمت فقط وقتی Override می‌شود که فعال باشد، تاریخ شروع آن رسیده باشد و تاریخ پایان نگذشته باشد.
- در صورت نبود قیمت معتبر، `Product.sale_price` به عنوان قیمت پایه استفاده می‌شود.
- API محصولات این فیلدها را با توجه به `?store=<id>` برمی‌گرداند:
  - `effective_sale_price`
  - `effective_price_type`
  - `effective_price_type_display`
- API قیمت‌ها فیلد `is_current` دارد تا قیمت معتبر فعلی با قیمت‌های آینده/منقضی‌شده اشتباه نشود.
- ایجاد/ویرایش قیمت فقط برای کالاهایی مجاز است که در همان فروشگاه Inventory داشته باشند.
- قیمت صفر یا منفی پذیرفته نمی‌شود.
- دسترسی superuser به لیست قیمت‌ها نیز درست شده است.
- هنگام افزودن/ویرایش CartItem همچنان قیمت نهایی توسط Backend و با قیمت فعال همان فروشگاه محاسبه می‌شود؛ بنابراین Frontend مرجع قیمت نیست.

## Frontend
- `Product` اکنون اطلاعات قیمت فعال را از API دریافت می‌کند.
- در صفحه فروش، قیمت فعال کالا در لیست انتخاب کالا و بعد از انتخاب کالا نمایش داده می‌شود.
- قیمت واقعی ثبت‌شده در Cart همچنان از `unit_price` برگشتی Backend نمایش داده می‌شود.
- در صفحه قیمت‌گذاری، «قیمت جاری خرده» فقط از قیمت‌هایی انتخاب می‌شود که `is_current=true` هستند؛ قیمت آینده یا منقضی‌شده دیگر به‌اشتباه قیمت جاری نمایش داده نمی‌شود.
- اصلاحات قبلی MUI 9.3.1 و محدودیت نقش‌های منو حفظ شده‌اند.

## Verification
- Backend: `python -m compileall -q backend` با موفقیت اجرا شد.
- اجرای تست Django در این محیط ممکن نبود چون Django در محیط اجرای فعلی نصب نیست.
- اجرای `npm run build` نیز از روی ZIP ممکن نیست، چون `package.json`/toolchain فرانت در این آرشیو وجود ندارد؛ سورس TypeScript اصلاح شده و ساختار پروژه موجود در ZIP حفظ شده است.


