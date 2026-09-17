Phase 6.16 — Financial & Inventory End-to-End Integrity

هدف:
این مرحله فقط روی یک مجموعه کوچک از سناریوهای حیاتی انتها‌به‌انتها تمرکز دارد و قرار نیست کل تست‌های قبلی دوباره اجرا شوند.

موارد پوشش‌داده‌شده:
1) Purchase -> Receive -> Inventory + ProductBatch + purchase value
2) Retail Sale -> FIFO across multiple batches + immutable cost/sale snapshots
3) Cash Sale -> Cancellation -> inventory/batch/cashbox reversal
4) Credit Sale -> Cancellation -> customer receivable reversal
5) Purchase Return -> inventory/batch + supplier ledger
6) Failed payment -> transaction rollback with no stock/cash/order side effects
7) Purchase Return after sale -> cannot return stock that has already been consumed

تست هدفمند:
python manage.py test products.test_phase6_16

نکته:
Full Regression در این مرحله عمداً اجرا نمی‌شود. فقط همین 7 تست هدفمند برای اعتبارسنجی Phase 6.16 کافی است؛ Full Regression برای Phase 6.19 نگه داشته می‌شود.
