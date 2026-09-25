from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, F, Sum, DecimalField, ExpressionWrapper
from rest_framework.exceptions import ValidationError


def get_valid_product_prices(product, store_id, price_type=None, at=None):
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
        raise ValidationError({"price_type": f"برای کالای «{product.name}» بیش از یک قیمت فعال از نوع انتخاب‌شده وجود دارد."})
    return prices[0] if prices else None


def get_active_batch(product, store_id, at=None):
    if not store_id:
        return None
    from .models import ProductBatch
    moment = at or timezone.now()
    return (ProductBatch.objects
            .filter(product=product, store_id=store_id, remaining_quantity__gt=0, received_at__lte=moment)
            .order_by("received_at", "id")
            .first())


def get_effective_sale_price(product, store_id, price_type="retail", at=None):
    """Return the effective selling price for a store.

    Retail is determined exclusively by the oldest sellable batch (FIFO).
    Wholesale/special prices come from ProductPrice. Product-level legacy
    purchase/sale prices are intentionally not supported.
    """
    if price_type == "retail":
        batch = get_active_batch(product, store_id, at=at)
        return Decimal(batch.sale_price) if batch is not None else None

    price = get_active_price(product, store_id, price_type=price_type, at=at)
    return Decimal(price.amount) if price is not None else None


def get_batch_valuation_map(store_ids, product_ids=None, at=None):
    """Aggregate the remaining value/profit of batch-controlled stock.

    Values are grouped per (store, product) so reports can remain batch-aware
    without falling back to deprecated Product price fields.
    """
    moment = at or timezone.now()
    from .models import ProductBatch

    qs = ProductBatch.objects.filter(
        store_id__in=set(store_ids),
        remaining_quantity__gt=0,
        received_at__lte=moment,
    )
    if product_ids is not None:
        qs = qs.filter(product_id__in=set(product_ids))

    value_field = DecimalField(max_digits=24, decimal_places=4)
    rows = (
        qs.values("store_id", "product_id")
        .annotate(
            quantity=Sum("remaining_quantity"),
            inventory_value=Sum(
                ExpressionWrapper(
                    F("remaining_quantity") * F("purchase_price"),
                    output_field=value_field,
                )
            ),
            sale_value=Sum(
                ExpressionWrapper(
                    F("remaining_quantity") * F("sale_price"),
                    output_field=value_field,
                )
            ),
            potential_profit=Sum(
                ExpressionWrapper(
                    F("remaining_quantity") * (F("sale_price") - F("purchase_price")),
                    output_field=value_field,
                )
            ),
        )
    )

    result = {}
    for row in rows:
        quantity = row["quantity"] or Decimal("0")
        inventory_value = row["inventory_value"] or Decimal("0")
        sale_value = row["sale_value"] or Decimal("0")
        result[(row["store_id"], row["product_id"])] = {
            "quantity": quantity,
            "inventory_value": inventory_value,
            "sale_value": sale_value,
            "potential_profit": row["potential_profit"] or Decimal("0"),
            "purchase_price": (inventory_value / quantity) if quantity else None,
            "sale_price": (sale_value / quantity) if quantity else None,
        }
    return result
