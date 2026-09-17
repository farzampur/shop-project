# API Coverage Audit — Frontend Execution Map

## هدف
پوشش APIهای Backend در زنجیره زیر:

`Backend API → Service → Page → Button/Action → Role → Responsive`

## این خروجی
این نسخه یک صفحه جدید به نام «گزارش‌های تکمیلی» اضافه می‌کند و APIهای گزارش‌دهی زیر را از UI در دسترس می‌کند:

### موجودی
- inventory-low-stock
- inventory-out-of-stock
- inventory-value-report
- inventory-slow-moving
- inventory-potential-profit
- store-inventory-summary
- inventory-report-full
- inventory-dashboard

### تأمین‌کنندگان
- suppliers/debtors
- suppliers/purchase-report
- suppliers/payment-report
- suppliers/balance-report
- suppliers/comprehensive-report

### مشتریان
- customer-report
- customers/debtors
- customers/creditors

### مالی و صندوق
- financial-summary
- financial-report
- cash-ledger
- cashbox-balance-report
- daily-cash-flow-report

## ساختار UI
- `/reports`: گزارش‌های عملیاتی فعلی فروش
- `/advanced-reports`: گزارش‌های تکمیلی Backend
- دسترسی صفحه گزارش‌های تکمیلی: فقط manager، مطابق routePermissions فعلی
- فیلتر فروشگاه و بازه تاریخ
- چهار گروه: موجودی، تأمین‌کنندگان، مشتریان، مالی و صندوق
- جدول‌ها RTL و قابل اسکرول افقی در موبایل

## گام بعدی Coverage
1. افزودن Actionهای تأمین‌کننده: مانده، پرداخت و تسویه
2. افزودن Barcode / QR / Label به صفحه محصولات
3. افزودن Purchase Receipt به صفحه خرید
4. افزودن Customer Ledger/Settlement actions به صفحه مشتریان
5. افزودن Export CSV فروش
6. تکمیل CRUDهای APIهایی که Service دارند ولی Action UI ندارند

## نکته
این مرحله فقط Frontend را تغییر می‌دهد و Backend را دستکاری نمی‌کند. تست‌های گسترده Backend در این مرحله لازم نیست.
