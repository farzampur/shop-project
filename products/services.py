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
    def receive_purchase(
        purchase
    ):

        for item in purchase.items.all():

            inventory, _ = (
                Inventory.objects
                .get_or_create(
                    product=item.product,
                    store=purchase.store,
                    defaults={
                        "quantity": 0
                    }
                )
            )

            inventory.quantity += item.quantity

            inventory.save()

            InventoryTransaction.objects.create(
                product=item.product,
                store=purchase.store,
                transaction_type="purchase",
                quantity=item.quantity,
                reference_id=purchase.id,
                description=(
                    f"Purchase #{purchase.id}"
                )
            )

        return purchase
        
        
        