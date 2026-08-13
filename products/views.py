from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .services import PurchaseService

from .models import (
    Category,
    Product,
    Inventory,
    InventoryTransaction,
    Supplier,
    Purchase,
    PurchaseItem,
)

from .serializers import (
    CategorySerializer,
    ProductSerializer,
    InventorySerializer,
    InventoryTransactionSerializer,
    InventoryReportSerializer,
    SupplierSerializer,
    PurchaseSerializer,
    PurchaseItemSerializer,    
)
from .permissions import (
    StoreRolePermission,
    InventoryPermission,
)

class CategoryViewSet(viewsets.ModelViewSet):

    serializer_class = CategorySerializer

    permission_classes = [
        IsAuthenticated,
        StoreRolePermission,
    ]

    def get_queryset(self):
        return Category.objects.filter(
            store__store_users__user=self.request.user
        ).distinct()


class ProductViewSet(viewsets.ModelViewSet):

    serializer_class = ProductSerializer

    permission_classes = [
        IsAuthenticated,
        StoreRolePermission,
    ]

    def get_queryset(self):
        return Product.objects.filter(
            category__store__store_users__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        category = serializer.validated_data["category"]

        has_access = category.store.store_users.filter(
            user=self.request.user
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()

    def perform_update(self, serializer):

        product = self.get_object()

        has_access = product.category.store.store_users.filter(
            user=self.request.user
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()

    def perform_destroy(self, instance):

        has_access = instance.category.store.store_users.filter(
            user=self.request.user
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        instance.delete()




class InventoryViewSet(viewsets.ModelViewSet):

    serializer_class = InventorySerializer

    permission_classes = [
        IsAuthenticated,
        InventoryPermission,
    ]

    def get_queryset(self):

        return Inventory.objects.filter(
            store__store_users__user=self.request.user
        ).select_related(
            "product",
            "store",
        )

    def perform_create(self, serializer):

        store = serializer.validated_data["store"]

        has_access = store.store_users.filter(
            user=self.request.user
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()

    def perform_update(self, serializer):

        inventory = self.get_object()

        has_access = inventory.store.store_users.filter(
            user=self.request.user
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()
        

class InventoryTransactionViewSet(
    viewsets.ReadOnlyModelViewSet
):

    serializer_class = (
        InventoryTransactionSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        queryset = (
            InventoryTransaction.objects
            .select_related(
                "product",
                "store"
            )
            .order_by("-id")
        )

        product_id = (
            self.request.query_params.get(
                "product"
            )
        )

        if product_id:
            queryset = queryset.filter(
                product_id=product_id
            )

        return queryset


class InventoryReportViewSet(
    viewsets.ReadOnlyModelViewSet
):

    serializer_class = (
        InventoryReportSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        queryset = (
            Inventory.objects
            .select_related(
                "product",
                "store"
            )
            .filter(
                store__store_users__user=self.request.user
            )
        )

        store_id = self.request.query_params.get(
            "store"
        )

        if store_id:
            queryset = queryset.filter(
                store_id=store_id
            )

        return queryset


class SupplierViewSet(
    viewsets.ModelViewSet
):

    serializer_class = SupplierSerializer

    permission_classes = [
        IsAuthenticated
    ]

    queryset = Supplier.objects.all()


class PurchaseViewSet(
    viewsets.ModelViewSet
):

    serializer_class = PurchaseSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return (
            Purchase.objects
            .select_related(
                "supplier",
                "store",
                "user"
            )
            .prefetch_related(
                "items"
            )
        )

    def perform_create(
        self,
        serializer
    ):

        serializer.save(
            user=self.request.user
        )

    @action(
        detail=True,
        methods=["post"]
    )
    def receive(self, request, pk=None):

        purchase = self.get_object()

        if purchase.received:
            return Response(
                {
                    "detail":
                    "این خرید قبلاً دریافت شده است."
                },
                status=400
            )

        PurchaseService.receive_purchase(
            purchase
        )

        purchase.received = True
        purchase.save(
            update_fields=["received"]
        )

        return Response(
            {
                "id": purchase.id,
                "received": True
            }
        )        
        
        
class PurchaseItemViewSet(
    viewsets.ModelViewSet
):

    serializer_class = PurchaseItemSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        purchase_id = self.kwargs.get(
            "purchase_pk"
        )

        return PurchaseItem.objects.filter(
            purchase_id=purchase_id
        ).select_related(
            "purchase",
            "product"
        )

    def perform_create(self, serializer):

        purchase_id = self.kwargs.get(
            "purchase_pk"
        )

        purchase = Purchase.objects.get(
            id=purchase_id
        )

        serializer.save(
            purchase=purchase
        )
        
        
        
    