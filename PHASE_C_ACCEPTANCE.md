# Phase C — Integration / Acceptance

این بسته هر سه مرحله Phase C را یکجا پوشش می‌دهد.

## C1 — Main User Scenarios

سناریوهای اصلی کاربر:

1. Login → Dashboard → انتخاب Store فعال → مشاهده منوی مجاز بر اساس Role
2. Product → Purchase → Receive → ایجاد/به‌روزرسانی Batch و موجودی
3. Inventory → Sale → مصرف FIFO Batch و ثبت مبلغ/قیمت همان Batch
4. Sale → Return/Cancel → برگشت موجودی و آثار مالی مرتبط
5. Customer → Payment → CashBox → Customer Ledger
6. Transfer → انتخاب مبدأ/مقصد → انتقال موجودی با حفظ Batch/Cost/Sale Price
7. Reports → مشاهده فروش، موجودی، سود و گزارش‌های مالی Store فعال
8. Logout/Login مجدد → حفظ Session صحیح و Store فعال مجاز

## C2 — Cross-module Integration

نقاط اتصال اصلی:

- Authentication ↔ ProtectedRoute ↔ Identity/StoreContext
- StoreContext ↔ RoleRoute ↔ Smart Menu
- Purchase ↔ Receive ↔ Batch ↔ Inventory
- Inventory/Batches ↔ Sales/FIFO ↔ Order/Payment
- Sales ↔ Customer Ledger ↔ CashBox
- Transfer ↔ Source/Destination Inventory ↔ Batch history
- Business modules ↔ Reports
- API errors ↔ AppErrorBoundary / Loading / Empty / Feedback UI
- RTL ↔ Layout ↔ Forms ↔ Tables ↔ Responsive breakpoints

## C3 — Final Acceptance

### Frontend

- `npm run build` باید بدون خطا سبز شود.
- Login و Logout بدون برگشت ناخواسته به صفحه یا Session خراب کار کند.
- Roleها فقط منو و Route مجاز خود را ببینند.
- Store فعال در همه صفحات یکسان بماند.
- صفحات اصلی در Desktop / Tablet / Mobile قابل استفاده باشند.
- جدول‌های عریض Layout را خراب نکنند.
- Dialog و Form در عرض کم از صفحه خارج نشوند.
- RTL در کل برنامه حفظ شود.
- Loading، Empty و Error state قابل فهم باشند.

### Business integration

- خرید دریافت‌شده باید در موجودی و Batch قابل مشاهده باشد.
- فروش باید FIFO را رعایت کند.
- برگشت/لغو فروش باید موجودی و آثار مالی را صحیح برگرداند.
- پرداخت مشتری باید فقط به Store مجاز و CashBox همان Store متصل باشد.
- انتقال باید بین Storeهای متفاوت انجام شود و اطلاعات Batch حفظ شود.
- گزارش‌ها باید با داده‌های عملیاتی همان Store همخوان باشند.

### خروجی نهایی

پس از تأیید سناریوهای بالا و Build، Phase C بسته و Phase D آغاز می‌شود.

> طبق نقشه فریز‌شده پروژه، Phase C دقیقاً شامل C1، C2 و C3 است و مرحله دیگری به آن اضافه نمی‌شود.
