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
