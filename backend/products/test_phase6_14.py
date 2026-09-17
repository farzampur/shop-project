from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import UserStore
from core.models import Store
from products.models import (
    Category,
    Inventory,
    InventoryTransaction,
    Product,
    ProductBatch,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    Supplier,
    SupplierTransaction,
)
from products.services import PurchaseService
from products.views import PurchaseReturnViewSet, PurchaseViewSet


class Phase614ApiValidationStateTransitionIntegrityTests(TestCase):
    """Phase 6.14: API validation and business-state transition integrity."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.manager = User.objects.create_user(
            username="phase614_manager", password="x"
        )

        self.store = Store.objects.create(
            name="Phase 6.14 Store", code="P614-A"
        )
        self.other_store = Store.objects.create(
            name="Phase 6.14 Other Store", code="P614-B"
        )
        UserStore.objects.create(
            user=self.manager,
            store=self.store,
            role="manager",
            is_active=True,
        )

        self.supplier = Supplier.objects.create(
            store=self.store, name="Phase 6.14 Supplier"
        )
        self.other_supplier = Supplier.objects.create(
            store=self.other_store, name="Phase 6.14 Other Supplier"
        )

        self.category = Category.objects.create(
            name="Phase 6.14 Category", store=self.store
        )
        self.other_category = Category.objects.create(
            name="Phase 6.14 Other Category", store=self.other_store
        )
        self.product = Product.objects.create(
            name="Phase 6.14 Product",
            barcode="6140000000001",
            category=self.category,
        )
        self.other_product = Product.objects.create(
            name="Phase 6.14 Other Product",
            barcode="6140000000002",
            category=self.other_category,
        )

    def _purchase(self, *, quantity="5", unit_price="100", received=False):
        purchase = Purchase.objects.create(
            supplier=self.supplier,
            store=self.store,
            user=self.manager,
        )
        PurchaseItem.objects.create(
            purchase=purchase,
            product=self.product,
            quantity=Decimal(quantity),
            unit_price=Decimal(unit_price),
            sale_price=Decimal("150"),
        )
        if received:
            purchase = PurchaseService.receive_purchase(purchase)
            SupplierTransaction.objects.create(
                supplier=self.supplier,
                transaction_type="purchase",
                amount=purchase.total_amount,
                reference_id=purchase.id,
            )
        return Purchase.objects.get(pk=purchase.pk)

    def _purchase_patch(self, purchase, data):
        request = self.factory.patch(
            f"/api/purchases/{purchase.pk}/", data, format="json"
        )
        force_authenticate(request, user=self.manager)
        return PurchaseViewSet.as_view({"patch": "partial_update"})(
            request, pk=purchase.pk
        )

    def _purchase_delete(self, purchase):
        request = self.factory.delete(f"/api/purchases/{purchase.pk}/")
        force_authenticate(request, user=self.manager)
        return PurchaseViewSet.as_view({"delete": "destroy"})(
            request, pk=purchase.pk
        )

    def _return_create(self, data):
        request = self.factory.post(
            "/api/purchase-returns/", data, format="json"
        )
        force_authenticate(request, user=self.manager)
        return PurchaseReturnViewSet.as_view({"post": "create"})(request)

    def test_received_purchase_cannot_be_mutated(self):
        purchase = self._purchase(received=True)
        old_invoice = purchase.invoice_number
        old_total = purchase.total_amount

        response = self._purchase_patch(
            purchase, {"invoice_number": "TAMPERED-614"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase.refresh_from_db()
        self.assertEqual(purchase.invoice_number, old_invoice)
        self.assertEqual(purchase.total_amount, old_total)

    def test_received_true_cannot_be_injected_through_generic_update(self):
        purchase = self._purchase(received=False)
        self.assertFalse(purchase.received)

        response = self._purchase_patch(purchase, {"received": True})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        purchase.refresh_from_db()
        self.assertFalse(purchase.received)
        self.assertFalse(
            Inventory.objects.filter(
                store=self.store, product=self.product
            ).exists()
        )
        self.assertFalse(
            ProductBatch.objects.filter(purchase_item__purchase=purchase).exists()
        )

    def test_purchase_store_cannot_be_tampered_during_update(self):
        purchase = self._purchase(received=False)

        response = self._purchase_patch(
            purchase, {"store": self.other_store.pk}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        purchase.refresh_from_db()
        self.assertEqual(purchase.store_id, self.store.id)

    def test_delete_does_not_remove_unrelated_supplier_ledger_entry(self):
        purchase = self._purchase(received=False)
        unrelated = SupplierTransaction.objects.create(
            supplier=self.other_supplier,
            transaction_type="purchase",
            amount=Decimal("777"),
            reference_id=purchase.id,
            description="Unrelated ledger row with colliding reference id",
        )

        response = self._purchase_delete(purchase)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Purchase.objects.filter(pk=purchase.pk).exists())
        self.assertTrue(
            SupplierTransaction.objects.filter(pk=unrelated.pk).exists()
        )

    def test_return_requires_received_purchase_and_makes_no_changes(self):
        purchase = self._purchase(received=False)
        item = purchase.items.get()

        before_returns = PurchaseReturn.objects.count()
        before_transactions = InventoryTransaction.objects.count()

        response = self._return_create(
            {
                "purchase": purchase.pk,
                "product": item.product_id,
                "quantity": "1",
                "unit_price": "1",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PurchaseReturn.objects.count(), before_returns)
        self.assertEqual(InventoryTransaction.objects.count(), before_transactions)

    def test_return_cannot_cross_store_by_product_tampering(self):
        purchase = self._purchase(received=True)

        # Deliberately create an inconsistent legacy purchase item directly;
        # the API must still refuse to turn it into a financial/stock return.
        PurchaseItem.objects.create(
            purchase=purchase,
            product=self.other_product,
            quantity=Decimal("1"),
            unit_price=Decimal("50"),
            sale_price=Decimal("60"),
        )
        Inventory.objects.create(
            product=self.other_product,
            store=self.store,
            quantity=Decimal("1"),
            min_quantity=Decimal("0"),
        )

        before_returns = PurchaseReturn.objects.count()
        response = self._return_create(
            {
                "purchase": purchase.pk,
                "product": self.other_product.pk,
                "quantity": "1",
                "unit_price": "1",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PurchaseReturn.objects.count(), before_returns)
        self.assertFalse(
            SupplierTransaction.objects.filter(
                supplier=self.supplier,
                transaction_type="return",
            ).exists()
        )

    def test_return_cannot_exceed_remaining_purchase_quantity(self):
        purchase = self._purchase(quantity="2", received=True)
        item = purchase.items.get()

        # Consume one unit from the batch/stock so only one remains returnable.
        inventory = Inventory.objects.get(store=self.store, product=self.product)
        inventory.quantity = Decimal("1")
        inventory.save(update_fields=["quantity", "updated_at"])
        batch = ProductBatch.objects.get(purchase_item=item)
        batch.remaining_quantity = Decimal("1")
        batch.save(update_fields=["remaining_quantity", "updated_at"])

        before_returns = PurchaseReturn.objects.count()
        before_supplier_returns = SupplierTransaction.objects.filter(
            supplier=self.supplier, transaction_type="return"
        ).count()

        response = self._return_create(
            {
                "purchase": purchase.pk,
                "product": self.product.pk,
                "quantity": "2",
                "unit_price": "1",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PurchaseReturn.objects.count(), before_returns)
        self.assertEqual(
            SupplierTransaction.objects.filter(
                supplier=self.supplier, transaction_type="return"
            ).count(),
            before_supplier_returns,
        )
        self.assertEqual(
            Inventory.objects.get(pk=inventory.pk).quantity, Decimal("1")
        )
        self.assertEqual(
            ProductBatch.objects.get(pk=batch.pk).remaining_quantity,
            Decimal("1"),
        )

    def test_existing_purchase_return_is_immutable(self):
        purchase = self._purchase(quantity="2", received=True)
        item = purchase.items.get()
        response = self._return_create(
            {
                "purchase": purchase.pk,
                "product": item.product_id,
                "quantity": "1",
                "unit_price": "999999",
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = PurchaseReturn.objects.get(purchase=purchase)
        self.assertEqual(created.unit_price, item.unit_price)
        self.assertEqual(created.total_amount, item.unit_price)

        patch = self.factory.patch(
            f"/api/purchase-returns/{created.pk}/",
            {"quantity": "999"},
            format="json",
        )
        force_authenticate(patch, user=self.manager)
        patch_response = PurchaseReturnViewSet.as_view(
            {"patch": "partial_update"}
        )(patch, pk=created.pk)
        self.assertEqual(patch_response.status_code, status.HTTP_400_BAD_REQUEST)

        delete = self.factory.delete(
            f"/api/purchase-returns/{created.pk}/"
        )
        force_authenticate(delete, user=self.manager)
        delete_response = PurchaseReturnViewSet.as_view(
            {"delete": "destroy"}
        )(delete, pk=created.pk)
        self.assertEqual(delete_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(PurchaseReturn.objects.filter(pk=created.pk).exists())
