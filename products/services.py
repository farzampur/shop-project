from django.db import transaction

from .models import (
    Purchase,
    PurchaseItem,
    Inventory,
    InventoryTransaction,
)

class PurchaseService:

    @staticmethod
    @transaction.atomic
    def receive_purchase(purchase):

        purchase = (
            Purchase.objects
            .select_for_update()
            .get(pk=purchase.pk)
        )

        if purchase.received:
            raise ValueError(
                "این خرید قبلاً دریافت شده است."
            )

        for item in purchase.items.all():

            # ---------------------------------
            # بررسی تراکنش قبلی این قلم خرید
            # ---------------------------------

            inventory_transaction = (
                InventoryTransaction.objects
                .filter(
                    product=item.product,
                    store=purchase.store,
                    transaction_type=(
                        InventoryTransaction.TYPE_PURCHASE
                    ),
                    reference_id=purchase.id,
                )
                .first()
            )

            # اگر قبلاً ثبت شده، نباید موجودی
            # دوباره افزایش پیدا کند.
            if inventory_transaction:
                continue

            # ---------------------------------
            # پیدا کردن موجودی
            # ---------------------------------

            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(
                    product=item.product,
                    store=purchase.store,
                )
                .first()
            )

            # ---------------------------------
            # ایجاد / افزایش موجودی
            # ---------------------------------

            if inventory is None:

                inventory = Inventory.objects.create(
                    product=item.product,
                    store=purchase.store,
                    quantity=item.quantity,
                    min_quantity=0,
                )

            else:

                inventory.quantity += (
                    item.quantity
                )

                inventory.save(
                    update_fields=[
                        "quantity",
                        "updated_at",
                    ]
                )

            # ---------------------------------
            # ثبت گردش انبار
            # ---------------------------------

            InventoryTransaction.objects.create(
                product=item.product,
                store=purchase.store,
                transaction_type=(
                    InventoryTransaction.TYPE_PURCHASE
                ),
                quantity=item.quantity,
                reference_id=purchase.id,
                description=(
                    f"Purchase #{purchase.id}"
                ),
            )

        # -------------------------------------
        # دریافت خرید
        # -------------------------------------

        purchase.received = True

        purchase.save(
            update_fields=[
                "received",
                "updated_at",
            ]
        )

        return purchase