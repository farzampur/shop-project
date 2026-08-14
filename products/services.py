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

            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(
                    product=item.product,
                    store=purchase.store
                )
                .first()
            )

            if inventory is None:

                inventory = Inventory.objects.create(
                    product=item.product,
                    store=purchase.store,
                    quantity=item.quantity
                )

            else:

                inventory.quantity += item.quantity

                inventory.save(
                    update_fields=[
                        "quantity",
                        "updated_at",
                    ]
                )

            InventoryTransaction.objects.create(
                product=item.product,
                store=purchase.store,
                transaction_type="purchase",
                quantity=item.quantity,
                reference_id=purchase.id,
                description=f"Purchase #{purchase.id}"
            )

        purchase.received = True

        purchase.save(
            update_fields=[
                "received",
                "updated_at",
            ]
        )

        return purchase        
        