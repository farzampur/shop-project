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
