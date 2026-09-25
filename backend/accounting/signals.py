from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


def _enabled():
    return bool(getattr(settings, "ACCOUNTING_AUTO_POSTING", False))


@receiver(post_save, sender="sales.Order")
def order_saved(sender, instance, **kwargs):
    if not _enabled():
        return
    from .services import post_sale, reverse_order_accounting
    if instance.status == "paid":
        post_sale(instance)
    elif instance.status == "cancelled":
        reverse_order_accounting(instance)


@receiver(post_save, sender="products.Purchase")
def purchase_saved(sender, instance, created=False, **kwargs):
    # PurchaseViewSet may create a row with received=True and then execute the
    # dedicated receive workflow. Only post on the final transition.
    if _enabled() and instance.received and not created:
        from .services import post_purchase
        post_purchase(instance)


@receiver(post_save, sender="products.SupplierTransaction")
def supplier_transaction_saved(sender, instance, **kwargs):
    if _enabled():
        from .services import post_supplier_transaction
        post_supplier_transaction(instance)


@receiver(post_save, sender="sales.CustomerTransaction")
def customer_transaction_saved(sender, instance, **kwargs):
    if _enabled():
        from .services import post_customer_transaction
        post_customer_transaction(instance)


@receiver(post_save, sender="sales.Expense")
def expense_saved(sender, instance, **kwargs):
    if _enabled():
        from .services import post_expense
        post_expense(instance)


@receiver(post_save, sender="sales.CashTransfer")
def cash_transfer_saved(sender, instance, **kwargs):
    if _enabled():
        from .services import post_cash_transfer
        post_cash_transfer(instance)


@receiver(post_save, sender="sales.CashBoxTransaction")
def cashbox_transaction_saved(sender, instance, **kwargs):
    if not _enabled():
        return
    if instance.reference_type == "customer_transaction":
        from sales.models import CustomerTransaction
        from .services import post_customer_transaction
        tx = CustomerTransaction.objects.filter(pk=instance.reference_id).select_related("customer", "store").first()
        if tx:
            post_customer_transaction(tx)
        return
    if instance.reference_type == "supplier_transaction":
        from products.models import SupplierTransaction
        from .services import post_supplier_transaction
        tx = SupplierTransaction.objects.filter(pk=instance.reference_id).select_related("supplier", "supplier__store").first()
        if tx:
            post_supplier_transaction(tx)
        return
    from .services import post_manual_cashbox_transaction
    post_manual_cashbox_transaction(instance)
