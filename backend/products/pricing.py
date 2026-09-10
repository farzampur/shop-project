from decimal import Decimal
from django.utils import timezone
from django.db.models import Q
from rest_framework.exceptions import ValidationError


def get_valid_product_prices(product, store_id, price_type=None, at=None):
    """Prices that are active and valid at `at` for one product/store."""
    moment = at or timezone.now()
    qs = product.prices.filter(
        store_id=store_id,
        is_active=True,
        effective_from__lte=moment,
    ).filter(Q(effective_to__isnull=True) | Q(effective_to__gte=moment))
    if price_type:
        qs = qs.filter(price_type=price_type)
    return qs.order_by("-effective_from", "-id")


def get_active_price(product, store_id, price_type="retail", at=None):
    prices = list(get_valid_product_prices(product, store_id, price_type=price_type, at=at)[:2])
    if len(prices) > 1:
        raise ValidationError(
            {"price_type": f"برای کالای «{product.name}» بیش از یک قیمت فعال از نوع انتخاب‌شده وجود دارد."}
        )
    return prices[0] if prices else None


def get_effective_sale_price(product, store_id, price_type="retail", at=None):
    """Configured active price; only retail may fall back to Product.sale_price."""
    price = get_active_price(product, store_id, price_type=price_type, at=at)
    if price is not None:
        return Decimal(price.amount)
    if price_type != "retail":
        return None
    return Decimal(product.sale_price)
