from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Count, Avg, Max, Sum, Q, F, DecimalField, ExpressionWrapper, Value
from django.db.models.functions import Coalesce
from decimal import Decimal
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.http import HttpResponse
from django.db.models import ProtectedError
from .services import (
    PurchaseService, 
    build_purchase_receipt_pdf, 
    build_product_barcode_png,       
    build_product_qrcode_png,
    build_product_label_pdf,
    build_product_labels_pdf,
)

from .models import (
    Category,
    Product,
    Inventory,
    InventoryTransaction,
    Supplier,
    Purchase,
    PurchaseItem,
    PurchaseReturn,
    SupplierTransaction,
)
from sales.models import (
    CashBox,
    CashBoxTransaction,
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
    SupplierTransactionSerializer, 
    SupplierPaymentSerializer,    
    PurchaseReturnSerializer,
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

        queryset = Category.objects.filter(
            store__store_users__user=self.request.user
        ).distinct()

        store_id = self.request.query_params.get("store")

        if store_id:
            queryset = queryset.filter(
                store_id=store_id
            )

        return queryset

    def perform_create(self, serializer):
        store = serializer.validated_data["store"]

        has_access = self.request.user.user_stores.filter(
            store=store
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()

    def perform_update(self, serializer):
        category = self.get_object()
        store = serializer.validated_data.get(
            "store",
            category.store
        )

        has_access = self.request.user.user_stores.filter(
            store=store
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()

    def perform_destroy(self, instance):
        try:
            instance.delete()

        except ProtectedError:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "این دسته‌بندی دارای محصول است و قابل حذف نیست."
            )

class ProductViewSet(viewsets.ModelViewSet):

    serializer_class = ProductSerializer

    permission_classes = [
        IsAuthenticated,
        StoreRolePermission,
    ]


    def get_queryset(self):

        queryset = Product.objects.filter(
            category__store__store_users__user=self.request.user
        ).distinct()

        store_id = self.request.query_params.get("store")

        if store_id:
            queryset = queryset.filter(
                category__store_id=store_id
            )

        return queryset



    def perform_create(self, serializer):

        category = serializer.validated_data["category"]

        store_id = self.request.query_params.get("store")

        if not store_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "فروشگاه انتخاب نشده است."
            )

        if str(category.store_id) != str(store_id):
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "دسته‌بندی انتخاب‌شده متعلق به فروشگاه فعال نیست."
            )

        has_access = self.request.user.user_stores.filter(
            store_id=store_id
        ).exists()

        if not has_access:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()



    def perform_update(self, serializer):

        product = self.get_object()

        store_id = self.request.query_params.get("store")

        if not store_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "فروشگاه انتخاب نشده است."
            )

        category = serializer.validated_data.get(
            "category",
            product.category
        )

        if str(category.store_id) != str(store_id):
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                "دسته‌بندی انتخاب‌شده متعلق به فروشگاه فعال نیست."
            )

        has_access = self.request.user.user_stores.filter(
            store_id=store_id
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

        from django.db.models.deletion import ProtectedError
        from rest_framework.exceptions import ValidationError

        try:
            instance.delete()

        except ProtectedError:
            raise ValidationError(
                "این محصول دارای سابقه خرید، فروش یا برگشت است و قابل حذف نیست. "
                "در صورت نیاز، محصول را غیرفعال کنید."
            )




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

    serializer_class = (
        SupplierSerializer
    )

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):

        queryset = (
            Supplier.objects
            .filter(
                store__store_users__user=
                self.request.user
            )
            .distinct()
        )

        store_id = (
            self.request.query_params.get(
                "store"
            )
        )

        if store_id:
            queryset = queryset.filter(
                store_id=store_id
            )

        return queryset

    def perform_create(
        self,
        serializer
    ):

        store = serializer.validated_data.get(
            "store"
        )

        if not store:
            from rest_framework.exceptions import (
                ValidationError
            )

            raise ValidationError(
                "فروشگاه الزامی است."
            )

        has_access = (
            store.store_users
            .filter(
                user=self.request.user
            )
            .exists()
        )

        if not has_access:
            from rest_framework.exceptions import (
                PermissionDenied
            )

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()

    def perform_update(
        self,
        serializer
    ):

        supplier = self.get_object()

        store = (
            serializer.validated_data.get(
                "store",
                supplier.store
            )
        )

        has_access = (
            store.store_users
            .filter(
                user=self.request.user
            )
            .exists()
        )

        if not has_access:
            from rest_framework.exceptions import (
                PermissionDenied
            )

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save()

    def perform_destroy(
        self,
        instance
    ):

        has_access = (
            instance.store
            .store_users
            .filter(
                user=self.request.user
            )
            .exists()
        )

        if not has_access:
            from rest_framework.exceptions import (
                PermissionDenied
            )

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        instance.delete()


class PurchaseViewSet(
    viewsets.ModelViewSet
):
    """
    مدیریت خرید از تأمین‌کنندگان.
    """

    serializer_class = PurchaseSerializer

    permission_classes = [
        IsAuthenticated
    ]

    queryset = (
        Purchase.objects
        .select_related(
            "supplier",
            "store",
            "user",
        )
        .prefetch_related(
            "items__product"
        )
        .order_by(
            "-created_at",
            "-id",
        )
    )

    def get_queryset(self):

        queryset = (
            Purchase.objects
            .select_related(
                "supplier",
                "store",
                "user",
            )
            .prefetch_related(
                "items__product"
            )
            .filter(
                store__store_users__user=self.request.user
            )
            .distinct()
            .order_by(
                "-created_at",
                "-id",
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

    @transaction.atomic
    def perform_create(
        self,
        serializer
    ):

        store = serializer.validated_data["store"]

        has_access = (
            self.request.user.user_stores
            .filter(store=store)
            .exists()
        )

        if not has_access:

            from rest_framework.exceptions import (
                PermissionDenied
            )

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        purchase = serializer.save(
            user=self.request.user
        )

        if (
            purchase.received
            and purchase.total_amount > 0
        ):
            self._create_supplier_debt(
                purchase
            )

    @transaction.atomic
    def perform_update(
        self,
        serializer
    ):

        purchase = self.get_object()

        old_received = (
            purchase.received
        )

        store = serializer.validated_data.get(
            "store",
            purchase.store
        )

        has_access = (
            self.request.user.user_stores
            .filter(store=store)
            .exists()
        )

        if not has_access:

            from rest_framework.exceptions import (
                PermissionDenied
            )

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        purchase = serializer.save()

        if (
            not old_received
            and purchase.received
            and purchase.total_amount > 0
        ):
            self._create_supplier_debt(
                purchase
            )

    def _create_supplier_debt(
        self,
        purchase
    ):

        exists = (
            SupplierTransaction.objects
            .filter(
                supplier=purchase.supplier,
                transaction_type="purchase",
                reference_id=purchase.id,
            )
            .exists()
        )

        if exists:
            return

        SupplierTransaction.objects.create(
            supplier=purchase.supplier,
            transaction_type="purchase",
            amount=purchase.total_amount,
            reference_id=purchase.id,
            description=(
                f"بدهی بابت خرید "
                f"شماره {purchase.id}"
            ),
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

        return (
            PurchaseItem.objects
            .filter(
                purchase_id=purchase_id,
                purchase__store__store_users__user=
                self.request.user
            )
            .select_related(
                "purchase",
                "product"
            )
            .distinct()
        )

    def perform_create(self, serializer):

        purchase_id = self.kwargs.get(
            "purchase_pk"
        )

        try:
            purchase = (
                Purchase.objects
                .select_related("store")
                .get(
                    id=purchase_id
                )
            )
        except Purchase.DoesNotExist:

            from rest_framework.exceptions import (
                NotFound
            )

            raise NotFound(
                "خرید موردنظر پیدا نشد."
            )

        # بررسی دسترسی کاربر به فروشگاه خرید
        has_access = (
            purchase.store
            .store_users
            .filter(
                user=self.request.user
            )
            .exists()
        )

        if not has_access:

            from rest_framework.exceptions import (
                PermissionDenied
            )

            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        product = serializer.validated_data[
            "product"
        ]

        # بررسی تعلق محصول به همان فروشگاه
        if product.category.store_id != purchase.store_id:

            from rest_framework.exceptions import (
                ValidationError
            )

            raise ValidationError(
                {
                    "product": (
                        "محصول انتخاب‌شده متعلق "
                        "به فروشگاه این خرید نیست."
                    )
                }
            )

        serializer.save(
            purchase=purchase
        )
        
        
class LowStockReportView(
    APIView
):
    """
    گزارش کالاهای کم موجود
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        inventories = (
            Inventory.objects
            .select_related(
                "product",
                "store"
            )
            .filter(
                quantity__lte=
                F("min_quantity")
            )
            .order_by(
                "product__name"
            )
        )

        data = []

        for item in inventories:

            data.append(
                {
                    "inventory_id":
                        item.id,

                    "product_id":
                        item.product.id,

                    "product":
                        item.product.name,

                    "store":
                        item.store.name,

                    "quantity":
                        item.quantity,

                    "min_quantity":
                        item.min_quantity,

                    "shortage":
                        (
                            item.min_quantity -
                            item.quantity
                        ),
                }
            )

        return Response(
            data
        )    
        
        
class OutOfStockReportView(APIView):
    """
    گزارش کالاهایی که موجودی آنها به صفر رسیده است.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        دریافت لیست کالاهای اتمام‌یافته.
        """

        inventories = (
            Inventory.objects
            .select_related(
                "product",
                "store"
            )
            .filter(
                quantity=0
            )
            .order_by(
                "product__name"
            )
        )

        data = []

        for item in inventories:
            data.append(
                {
                    "inventory_id": item.id,
                    "product_id": item.product.id,
                    "product": item.product.name,
                    "store": item.store.name,
                    "quantity": item.quantity,
                    "min_quantity": item.min_quantity,
                }
            )

        return Response(data)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import InventoryTransaction


class InventoryLedgerView(APIView):
    """
    گزارش گردش یک کالا در انبار.

    انواع تراکنش:
    - purchase    خرید
    - sale        فروش
    - return      برگشت
    - adjustment  اصلاح موجودی
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        product_id
    ):
        """
        دریافت تمام تراکنش‌های یک کالا
        به ترتیب جدیدترین تراکنش.
        """

        transactions = (
            InventoryTransaction.objects
            .filter(
                product_id=product_id
            )
            .select_related(
                "product",
                "store",
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

        result = []

        for tx in transactions:

            result.append(
                {
                    "id": tx.id,

                    "product_id":
                        tx.product_id,

                    "product":
                        tx.product.name,

                    "store_id":
                        tx.store_id,

                    "store":
                        tx.store.name,

                    "transaction_type":
                        tx.transaction_type,

                    "quantity":
                        tx.quantity,

                    "reference_id":
                        tx.reference_id,

                    "description":
                        tx.description,

                    "created_at":
                        tx.created_at,
                }
            )

        return Response(result)

        
        
from django.db.models import (
    F,
    Sum,
    DecimalField,
    ExpressionWrapper,
)


class InventoryValueReportView(APIView):
    """
    گزارش ارزش موجودی انبار.

    ارزش موجودی هر رکورد:
        quantity × purchase_price

    همچنین مجموع ارزش کل انبار
    محاسبه می‌شود.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        محاسبه ارزش موجودی کالاها
        و مجموع ارزش کل انبار.
        """

        inventories = (
            Inventory.objects
            .select_related(
                "product",
                "store",
            )
            .annotate(
                inventory_value=ExpressionWrapper(
                    F("quantity")
                    * F("product__purchase_price"),
                    output_field=DecimalField(
                        max_digits=20,
                        decimal_places=2,
                    ),
                )
            )
            .order_by(
                "product__name"
            )
        )

        total_value = (
            inventories.aggregate(
                total=Sum(
                    "inventory_value"
                )
            )["total"]
            or 0
        )

        data = []

        for item in inventories:

            data.append(
                {
                    "inventory_id":
                        item.id,

                    "product_id":
                        item.product_id,

                    "product":
                        item.product.name,

                    "store_id":
                        item.store_id,

                    "store":
                        item.store.name,

                    "quantity":
                        item.quantity,

                    "purchase_price":
                        item.product.purchase_price,

                    "inventory_value":
                        item.inventory_value,
                }
            )

        return Response(
            {
                "total_inventory_value":
                    total_value,

                "items":
                    data,
            }
        )
        
        

class SlowMovingInventoryReportView(APIView):
    """
    گزارش کالاهای راکد یا کم‌گردش.

    کالاهایی که در بازه مشخص‌شده
    تراکنش انباری نداشته‌اند، نمایش داده می‌شوند.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        دریافت گزارش کالاهای کم‌گردش.

        پارامترهای اختیاری:

        days:
            تعداد روزهایی که اگر کالا در این مدت
            گردش نداشته باشد، راکد در نظر گرفته شود.

        پیش‌فرض: 30 روز
        """

        from datetime import timedelta
        from django.utils import timezone
        from django.db.models import Max

        try:
            days = int(
                request.GET.get(
                    "days",
                    30
                )
            )

        except ValueError:
            raise ValidationError(
                {
                    "days":
                    "تعداد روز باید عدد صحیح باشد."
                }
            )

        if days <= 0:
            raise ValidationError(
                {
                    "days":
                    "تعداد روز باید بیشتر از صفر باشد."
                }
            )

        cutoff_date = (
            timezone.now()
            - timedelta(
                days=days
            )
        )

        inventories = (
            Inventory.objects
            .select_related(
                "product",
                "store",
            )
            .annotate(
                last_transaction=Max(
                    "product__inventorytransaction__created_at"
                )
            )
        )

        result = []

        for item in inventories:

            last_transaction = (
                item.last_transaction
            )

            # کالایی که هیچ تراکنشی نداشته است
            # یا آخرین تراکنش آن قدیمی است.
            if (
                last_transaction is None
                or
                last_transaction < cutoff_date
            ):

                result.append(
                    {
                        "inventory_id":
                            item.id,

                        "product_id":
                            item.product_id,

                        "product":
                            item.product.name,

                        "store_id":
                            item.store_id,

                        "store":
                            item.store.name,

                        "quantity":
                            item.quantity,

                        "min_quantity":
                            item.min_quantity,

                        "last_transaction":
                            last_transaction,

                        "days_without_transaction":
                            (
                                None
                                if last_transaction is None
                                else (
                                    timezone.now()
                                    - last_transaction
                                ).days
                            ),
                    }
                )

        result.sort(
            key=lambda x: (
                x[
                    "days_without_transaction"
                ]
                if x[
                    "days_without_transaction"
                ] is not None
                else 999999
            ),
            reverse=True
        )

        return Response(
            result
        )

class InventoryPotentialProfitReportView(APIView):
    """
    گزارش سود بالقوه موجودی انبار.

    سود بالقوه بر اساس قیمت‌های فعلی Product
    و مقدار موجودی فعلی Inventory محاسبه می‌شود.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        محاسبه سود بالقوه هر موجودی
        و مجموع سود بالقوه کل انبار.
        """

        from django.db.models import (
            F,
            Sum,
            DecimalField,
            ExpressionWrapper,
        )

        inventories = (
            Inventory.objects
            .select_related(
                "product",
                "store",
            )
            .annotate(
                unit_potential_profit=ExpressionWrapper(
                    F("product__sale_price")
                    - F("product__purchase_price"),
                    output_field=DecimalField(
                        max_digits=20,
                        decimal_places=2,
                    ),
                ),
                potential_profit=ExpressionWrapper(
                    F("quantity")
                    * (
                        F("product__sale_price")
                        - F("product__purchase_price")
                    ),
                    output_field=DecimalField(
                        max_digits=20,
                        decimal_places=2,
                    ),
                ),
            )
            .order_by(
                "product__name"
            )
        )

        total_potential_profit = (
            inventories.aggregate(
                total=Sum(
                    "potential_profit"
                )
            )["total"]
            or 0
        )

        data = []

        for item in inventories:

            data.append(
                {
                    "inventory_id": item.id,

                    "product_id":
                        item.product_id,

                    "product":
                        item.product.name,

                    "store_id":
                        item.store_id,

                    "store":
                        item.store.name,

                    "quantity":
                        item.quantity,

                    "purchase_price":
                        item.product.purchase_price,

                    "sale_price":
                        item.product.sale_price,

                    "unit_potential_profit":
                        item.unit_potential_profit,

                    "potential_profit":
                        item.potential_profit,
                }
            )

        return Response(
            {
                "total_potential_profit":
                    total_potential_profit,

                "items":
                    data,
            }
        )


class StoreInventorySummaryView(APIView):
    """
    گزارش خلاصه موجودی به تفکیک فروشگاه.

    نمایش:
    - تعداد رکوردهای موجودی
    - کالاهای دارای موجودی
    - کالاهای کم‌موجود
    - کالاهای اتمام‌یافته
    - ارزش کل موجودی
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        محاسبه خلاصه موجودی هر فروشگاه.
        """

        inventories = (
            Inventory.objects
            .select_related(
                "store",
                "product",
            )
            .annotate(
                inventory_value=ExpressionWrapper(
                    F("quantity")
                    * F(
                        "product__purchase_price"
                    ),
                    output_field=DecimalField(
                        max_digits=20,
                        decimal_places=2,
                    ),
                )
            )
        )

        stores = (
            inventories
            .values(
                "store_id",
                "store__name",
            )
            .annotate(
                inventory_count=Count(
                    "id"
                ),

                in_stock_count=Count(
                    "id",
                    filter=Q(
                        quantity__gt=0
                    )
                ),

                low_stock_count=Count(
                    "id",
                    filter=Q(
                        quantity__gt=0,
                        quantity__lte=F(
                            "min_quantity"
                        ),
                    )
                ),

                out_of_stock_count=Count(
                    "id",
                    filter=Q(
                        quantity=0
                    )
                ),

                inventory_value=Sum(
                    "inventory_value"
                ),
            )
            .order_by(
                "store__name"
            )
        )

        result = []

        for store in stores:

            result.append(
                {
                    "store_id":
                        store["store_id"],

                    "store":
                        store["store__name"],

                    "inventory_count":
                        store["inventory_count"],

                    "in_stock_count":
                        store["in_stock_count"],

                    "low_stock_count":
                        store["low_stock_count"],

                    "out_of_stock_count":
                        store[
                            "out_of_stock_count"
                        ],

                    "inventory_value":
                        store[
                            "inventory_value"
                        ] or 0,
                }
            )

        return Response(
            result
        )


class InventoryReportView(APIView):
    """
    گزارش کامل موجودی کالاها.

    فیلترها:
    - store_id
    - product_id
    - only_low_stock=true
    - only_out_of_stock=true
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        دریافت گزارش موجودی و اعمال فیلترهای درخواست.
        """

        queryset = (
            Inventory.objects
            .select_related(
                "product",
                "store",
            )
            .filter(
                    store__store_users__user=request.user
                )            
        )

        store_id = request.query_params.get(
            "store_id"
        )        

        product_id = request.query_params.get(
            "product_id"
        )

        only_low_stock = (
            request.query_params.get(
                "only_low_stock"
            )
        )

        only_out_of_stock = (
            request.query_params.get(
                "only_out_of_stock"
            )
        )

        # فیلتر فروشگاه
        if store_id:
            queryset = queryset.filter(
                store_id=store_id
            )

        # فیلتر کالا
        if product_id:
            queryset = queryset.filter(
                product_id=product_id
            )

        # فقط کم‌موجود
        if only_low_stock == "true":
            queryset = queryset.filter(
                quantity__gt=0,
                quantity__lte=F(
                    "min_quantity"
                )
            )

        # فقط اتمام‌یافته
        if only_out_of_stock == "true":
            queryset = queryset.filter(
                quantity=0
            )

        queryset = (
            queryset
            .annotate(
                inventory_value=ExpressionWrapper(
                    F("quantity")
                    * F(
                        "product__purchase_price"
                    ),
                    output_field=DecimalField(
                        max_digits=20,
                        decimal_places=2,
                    ),
                )
            )
            .order_by(
                "store__name",
                "product__name",
            )
        )

        result = []

        for item in queryset:

            if item.quantity == 0:

                stock_status = "out_of_stock"

            elif (
                item.quantity
                <= item.min_quantity
            ):

                stock_status = "low_stock"

            else:

                stock_status = "normal"

            result.append(
                {
                    "inventory_id": item.id,
                    "product_id": item.product_id,
                    "product": item.product.name,
                    "store_id": item.store_id,
                    "store": item.store.name,
                    "quantity": item.quantity,
                    "min_quantity": item.min_quantity,
                    "purchase_price":
                        item.product.purchase_price,
                    "sale_price":
                        item.product.sale_price,
                    "inventory_value":
                        item.inventory_value,
                    "stock_status":
                        stock_status,
                }
            )

        return Response(
            {
                "filters": {
                    "store_id": store_id,
                    "product_id": product_id,
                    "only_low_stock":
                        only_low_stock,
                    "only_out_of_stock":
                        only_out_of_stock,
                },
                "count": len(result),
                "items": result,
            }
        )

        
class InventoryDashboardView(APIView):
    """
    داشبورد مدیریتی انبار.

    نمایش:
    - تعداد کل موجودی‌ها
    - تعداد کالاهای دارای موجودی
    - تعداد کالاهای کم‌موجود
    - تعداد کالاهای اتمام‌یافته
    - ارزش کل موجودی
    - سود بالقوه کل موجودی
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        محاسبه شاخص‌های اصلی انبار
        برای فروشگاه‌های مجاز کاربر.
        """

        inventories = (
            Inventory.objects
            .filter(
                store__store_users__user=request.user
            )
            .select_related(
                "product",
                "store",
            )
            .annotate(
                inventory_value=ExpressionWrapper(
                    F("quantity")
                    * F(
                        "product__purchase_price"
                    ),
                    output_field=DecimalField(
                        max_digits=20,
                        decimal_places=2,
                    ),
                ),

                potential_profit=ExpressionWrapper(
                    F("quantity")
                    * (
                        F("product__sale_price")
                        -
                        F("product__purchase_price")
                    ),
                    output_field=DecimalField(
                        max_digits=20,
                        decimal_places=2,
                    ),
                ),
            )
        )

        summary = inventories.aggregate(
            inventory_count=Count("id"),

            in_stock_count=Count(
                "id",
                filter=Q(
                    quantity__gt=0
                )
            ),

            low_stock_count=Count(
                "id",
                filter=Q(
                    quantity__gt=0,
                    quantity__lte=F(
                        "min_quantity"
                    ),
                )
            ),

            out_of_stock_count=Count(
                "id",
                filter=Q(
                    quantity=0
                )
            ),

            total_inventory_value=Sum(
                "inventory_value"
            ),

            total_potential_profit=Sum(
                "potential_profit"
            ),
        )

        return Response(
            {
                "inventory_count":
                    summary[
                        "inventory_count"
                    ] or 0,

                "in_stock_count":
                    summary[
                        "in_stock_count"
                    ] or 0,

                "low_stock_count":
                    summary[
                        "low_stock_count"
                    ] or 0,

                "out_of_stock_count":
                    summary[
                        "out_of_stock_count"
                    ] or 0,

                "total_inventory_value":
                    summary[
                        "total_inventory_value"
                    ] or 0,

                "total_potential_profit":
                    summary[
                        "total_potential_profit"
                    ] or 0,
            }
        )


class SupplierTransactionViewSet(
    viewsets.ModelViewSet
):
    """
    مدیریت تراکنش‌های تأمین‌کننده.
    """

    serializer_class = (
        SupplierTransactionSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    queryset = (
        SupplierTransaction.objects
        .select_related("supplier")
        .order_by(
            "-created_at",
            "-id"
        )
    )


class SupplierPaymentViewSet(
    viewsets.ModelViewSet
):
    """
    ثبت و مدیریت پرداخت به تأمین‌کننده.

    هنگام ثبت پرداخت:
    1- بدهی تأمین‌کننده بررسی می‌شود.
    2- تراکنش payment برای تأمین‌کننده ثبت می‌شود.
    3- تراکنش payment برای صندوق ثبت می‌شود.
    4- موجودی صندوق کاهش پیدا می‌کند.
    """

    serializer_class = (
        SupplierPaymentSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    queryset = (
        SupplierTransaction.objects
        .filter(
            transaction_type="payment"
        )
        .select_related(
            "supplier"
        )
        .order_by(
            "-created_at",
            "-id",
        )
    )

    @transaction.atomic
    def perform_create(
        self,
        serializer
    ):
        """
        ثبت پرداخت به تأمین‌کننده
        و کسر مبلغ از صندوق.
        """

        supplier = (
            serializer.validated_data[
                "supplier"
            ]
        )

        amount = (
            serializer.validated_data[
                "amount"
            ]
        )

        # --------------------------------
        # محاسبه بدهی فعلی تأمین‌کننده
        # --------------------------------

        purchase_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="purchase",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        payment_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="payment",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        return_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="return",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        current_debt = (
            purchase_total
            - payment_total
            - return_total
        )

        # --------------------------------
        # کنترل مبلغ پرداخت
        # --------------------------------

        if amount <= 0:
            raise ValidationError(
                "مبلغ پرداخت باید بیشتر از صفر باشد."
            )

        if amount > current_debt:
            raise ValidationError(
                "مبلغ پرداخت بیشتر از بدهی تأمین‌کننده است."
            )

        # --------------------------------
        # انتخاب صندوق
        # --------------------------------

        cashbox = (
            CashBox.objects
            .filter(
                store__store_users__user=
                self.request.user
            )
            .order_by("id")
            .first()
        )

        if not cashbox:
            raise ValidationError(
                "صندوقی برای پرداخت پیدا نشد."
            )

        # --------------------------------
        # کنترل موجودی صندوق
        # --------------------------------

        if cashbox.balance < amount:
            raise ValidationError(
                "موجودی صندوق برای این پرداخت کافی نیست."
            )

        # --------------------------------
        # ثبت تراکنش تأمین‌کننده
        # --------------------------------

        supplier_tx = serializer.save(
            transaction_type="payment"
        )

        # --------------------------------
        # کاهش موجودی صندوق
        # --------------------------------

        cashbox.balance -= amount

        cashbox.save(
            update_fields=[
                "balance",
                "updated_at",
            ]
        )

        # --------------------------------
        # ثبت تراکنش صندوق
        # --------------------------------

        CashBoxTransaction.objects.create(
            cashbox=cashbox,
            transaction_type="payment",
            amount=amount,
            reference_id=supplier_tx.id,
            description=(
                f"پرداخت به تأمین‌کننده "
                f"{supplier.name}"
            ),
        )
        
        
        
class SupplierBalanceView(APIView):
    """
    نمایش مانده حساب یک تأمین‌کننده.

    purchase:
        افزایش بدهی به تأمین‌کننده

    payment:
        کاهش بدهی

    return:
        کاهش بدهی
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        supplier_id
    ):
        """
        محاسبه مانده حساب تأمین‌کننده.
        """

        supplier = get_object_or_404(
            Supplier,
            id=supplier_id
        )

        purchase_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="purchase",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        payment_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="payment",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        return_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="return",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        balance = (
            purchase_total
            - payment_total
            - return_total
        )

        return Response(
            {
                "supplier_id":
                    supplier.id,

                "supplier_name":
                    supplier.name,

                "purchases":
                    purchase_total,

                "payments":
                    payment_total,

                "returns":
                    return_total,

                "balance":
                    balance,
            }
        )

class SupplierLedgerView(APIView):
    """
    گردش حساب تأمین‌کننده.

    خرید:
        افزایش مانده بدهی

    پرداخت:
        کاهش مانده بدهی

    برگشت:
        کاهش مانده بدهی
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        supplier_id
    ):
        """
        نمایش تمام تراکنش‌های تأمین‌کننده
        همراه با مانده لحظه‌ای.
        """

        supplier = get_object_or_404(
            Supplier,
            id=supplier_id
        )

        transactions = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier
            )
            .order_by(
                "created_at",
                "id"
            )
        )

        balance = Decimal("0.00")

        result = []

        for tx in transactions:

            if tx.transaction_type == "purchase":
                balance += tx.amount

            elif tx.transaction_type in (
                "payment",
                "return",
            ):
                balance -= tx.amount

            result.append(
                {
                    "id": tx.id,
                    "date": tx.created_at,
                    "type": tx.transaction_type,
                    "amount": tx.amount,
                    "reference_id":
                        tx.reference_id,
                    "description":
                        tx.description,
                    "balance": balance,
                }
            )

        return Response(
            {
                "supplier_id":
                    supplier.id,

                "supplier_name":
                    supplier.name,

                "transactions":
                    result,

                "final_balance":
                    balance,
            }
        )
        
class DebtorSuppliersView(APIView):
    """
    لیست تأمین‌کنندگانی که از فروشگاه طلب دارند.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):
        """
        محاسبه مانده حساب تمام تأمین‌کنندگان.
        """

        suppliers = (
            Supplier.objects
            .prefetch_related(
                "transactions"
            )
        )

        result = []

        for supplier in suppliers:

            purchase_total = Decimal(
                "0.00"
            )

            payment_total = Decimal(
                "0.00"
            )

            return_total = Decimal(
                "0.00"
            )

            for tx in (
                supplier.transactions.all()
            ):

                if (
                    tx.transaction_type
                    == "purchase"
                ):
                    purchase_total += (
                        tx.amount
                    )

                elif (
                    tx.transaction_type
                    == "payment"
                ):
                    payment_total += (
                        tx.amount
                    )

                elif (
                    tx.transaction_type
                    == "return"
                ):
                    return_total += (
                        tx.amount
                    )

            balance = (
                purchase_total
                - payment_total
                - return_total
            )

            if balance > 0:

                result.append(
                    {
                        "supplier_id":
                            supplier.id,

                        "supplier_name":
                            supplier.name,

                        "purchases":
                            purchase_total,

                        "payments":
                            payment_total,

                        "returns":
                            return_total,

                        "balance":
                            balance,
                    }
                )

        result.sort(
            key=lambda item:
                item["balance"],
            reverse=True
        )

        return Response(
            result
        )

class SupplierPurchaseReportView(APIView):
    """
    گزارش خرید هر تأمین‌کننده.

    اطلاعات:
    - تعداد خرید
    - مجموع خرید
    - میانگین مبلغ خرید
    - تاریخ آخرین خرید

    فیلترها:
    - supplier_id
    - start_date=YYYY-MM-DD
    - end_date=YYYY-MM-DD
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        تولید گزارش خرید تأمین‌کنندگان.
        """

        supplier_id = request.query_params.get(
            "supplier_id"
        )

        start_date = request.query_params.get(
            "start_date"
        )

        end_date = request.query_params.get(
            "end_date"
        )

        # -------------------------
        # اعتبارسنجی تاریخ شروع
        # -------------------------

        if start_date:
            try:
                datetime.strptime(
                    start_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                raise ValidationError(
                    {
                        "start_date":
                        "فرمت تاریخ باید YYYY-MM-DD باشد."
                    }
                )

        # -------------------------
        # اعتبارسنجی تاریخ پایان
        # -------------------------

        if end_date:
            try:
                datetime.strptime(
                    end_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                raise ValidationError(
                    {
                        "end_date":
                        "فرمت تاریخ باید YYYY-MM-DD باشد."
                    }
                )

        # -------------------------
        # بررسی ترتیب تاریخ‌ها
        # -------------------------

        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            raise ValidationError(
                {
                    "date":
                    "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد."
                }
            )

        # -------------------------
        # Query خریدها
        # -------------------------

        purchases = Purchase.objects.all()

        if supplier_id:
            purchases = purchases.filter(
                supplier_id=supplier_id
            )

        if start_date:
            purchases = purchases.filter(
                created_at__date__gte=start_date
            )

        if end_date:
            purchases = purchases.filter(
                created_at__date__lte=end_date
            )

        # -------------------------
        # گزارش تأمین‌کنندگان
        # -------------------------

        suppliers = (
            Supplier.objects
            .filter(
                purchases__in=purchases
            )
            .annotate(
                purchase_count=Count(
                    "purchases",
                    distinct=True
                ),

                total_purchase=Coalesce(
                    Sum(
                        "purchases__total_amount",
                    ),
                    Value(
                        0,
                        output_field=DecimalField(
                            max_digits=20,
                            decimal_places=2,
                        )
                    ),
                ),

                average_purchase=Coalesce(
                    Avg(
                        "purchases__total_amount",
                    ),
                    Value(
                        0,
                        output_field=DecimalField(
                            max_digits=20,
                            decimal_places=2,
                        )
                    ),
                ),

                last_purchase_date=Max(
                    "purchases__created_at"
                ),
            )
            .order_by(
                "-total_purchase",
                "name",
            )
        )

        result = []

        for supplier in suppliers:

            result.append(
                {
                    "supplier_id":
                        supplier.id,

                    "supplier_name":
                        supplier.name,

                    "purchase_count":
                        supplier.purchase_count,

                    "total_purchase":
                        supplier.total_purchase,

                    "average_purchase":
                        supplier.average_purchase,

                    "last_purchase_date":
                        supplier.last_purchase_date,
                }
            )

        return Response(
            {
                "filters": {
                    "supplier_id":
                        supplier_id,

                    "start_date":
                        start_date,

                    "end_date":
                        end_date,
                },

                "count":
                    len(result),

                "items":
                    result,
            }
        )

class SupplierPaymentReportView(APIView):
    """
    گزارش پرداخت‌های تأمین‌کنندگان.

    اطلاعات:
    - تعداد پرداخت
    - مجموع پرداخت
    - میانگین پرداخت
    - آخرین پرداخت

    فیلترها:
    - supplier_id
    - start_date=YYYY-MM-DD
    - end_date=YYYY-MM-DD
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        supplier_id = request.query_params.get(
            "supplier_id"
        )

        start_date = request.query_params.get(
            "start_date"
        )

        end_date = request.query_params.get(
            "end_date"
        )

        # اعتبارسنجی تاریخ‌ها
        if start_date:
            try:
                datetime.strptime(
                    start_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                raise ValidationError(
                    {
                        "start_date":
                        "فرمت تاریخ باید YYYY-MM-DD باشد."
                    }
                )

        if end_date:
            try:
                datetime.strptime(
                    end_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                raise ValidationError(
                    {
                        "end_date":
                        "فرمت تاریخ باید YYYY-MM-DD باشد."
                    }
                )

        if (
            start_date
            and end_date
            and start_date > end_date
        ):
            raise ValidationError(
                {
                    "date":
                    "تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد."
                }
            )

        # فقط تراکنش‌های پرداخت
        transactions = (
            SupplierTransaction.objects
            .filter(
                transaction_type="payment"
            )
        )

        if supplier_id:
            transactions = transactions.filter(
                supplier_id=supplier_id
            )

        if start_date:
            transactions = transactions.filter(
                created_at__date__gte=start_date
            )

        if end_date:
            transactions = transactions.filter(
                created_at__date__lte=end_date
            )

        # گزارش به تفکیک تأمین‌کننده
        suppliers = (
            Supplier.objects
            .filter(
                transactions__in=transactions
            )
            .annotate(
                payment_count=Count(
                    "transactions",
                    filter=Q(
                        transactions__transaction_type="payment"
                    ),
                    distinct=True
                ),

                total_payment=Coalesce(
                    Sum(
                        "transactions__amount",
                        filter=Q(
                            transactions__transaction_type="payment"
                        ),
                    ),
                    Value(
                        0,
                        output_field=DecimalField(
                            max_digits=20,
                            decimal_places=2,
                        )
                    ),
                ),

                average_payment=Coalesce(
                    Avg(
                        "transactions__amount",
                        filter=Q(
                            transactions__transaction_type="payment"
                        ),
                    ),
                    Value(
                        0,
                        output_field=DecimalField(
                            max_digits=20,
                            decimal_places=2,
                        )
                    ),
                ),

                last_payment_date=Max(
                    "transactions__created_at",
                    filter=Q(
                        transactions__transaction_type="payment"
                    ),
                ),
            )
            .order_by(
                "-total_payment",
                "name",
            )
        )

        result = []

        for supplier in suppliers:

            result.append(
                {
                    "supplier_id":
                        supplier.id,

                    "supplier_name":
                        supplier.name,

                    "payment_count":
                        supplier.payment_count,

                    "total_payment":
                        supplier.total_payment,

                    "average_payment":
                        supplier.average_payment,

                    "last_payment_date":
                        supplier.last_payment_date,
                }
            )

        return Response(
            {
                "filters": {
                    "supplier_id":
                        supplier_id,

                    "start_date":
                        start_date,

                    "end_date":
                        end_date,
                },

                "count":
                    len(result),

                "items":
                    result,
            }
        )

class SupplierBalanceReportView(APIView):
    """
    گزارش مانده حساب تمام تأمین‌کنندگان.

    وضعیت‌ها:
    - debtor     : فروشگاه به تأمین‌کننده بدهکار است
    - settled    : حساب تسویه است
    - creditor   : در صورت وجود بستانکاری تأمین‌کننده
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        """
        گزارش مانده همه تأمین‌کنندگان.

        Query Params:
        ?only_debtors=true
        ?only_settled=true
        ?only_creditors=true
        """

        only_debtors = (
            request.query_params.get(
                "only_debtors"
            ) == "true"
        )

        only_settled = (
            request.query_params.get(
                "only_settled"
            ) == "true"
        )

        only_creditors = (
            request.query_params.get(
                "only_creditors"
            ) == "true"
        )

        suppliers = (
            Supplier.objects
            .prefetch_related(
                "transactions"
            )
            .order_by("name")
        )

        result = []

        for supplier in suppliers:

            purchases = Decimal("0.00")
            payments = Decimal("0.00")
            returns = Decimal("0.00")
            adjustments = Decimal("0.00")

            for tx in supplier.transactions.all():

                if tx.transaction_type == "purchase":
                    purchases += tx.amount

                elif tx.transaction_type == "payment":
                    payments += tx.amount

                elif tx.transaction_type == "return":
                    returns += tx.amount

                elif tx.transaction_type == "adjustment":
                    adjustments += tx.amount

            balance = (
                purchases
                - payments
                - returns
                + adjustments
            )

            if balance > 0:
                status = "debtor"
            elif balance < 0:
                status = "creditor"
            else:
                status = "settled"

            if only_debtors and status != "debtor":
                continue

            if only_settled and status != "settled":
                continue

            if only_creditors and status != "creditor":
                continue

            result.append(
                {
                    "supplier_id": supplier.id,
                    "supplier_name": supplier.name,
                    "purchases": purchases,
                    "payments": payments,
                    "returns": returns,
                    "adjustments": adjustments,
                    "balance": abs(balance),
                    "status": status,
                }
            )

        result.sort(
            key=lambda item: item["balance"],
            reverse=True
        )

        return Response(
            {
                "count": len(result),
                "items": result,
            }
        )
               

class SupplierComprehensiveReportView(APIView):
    """
    گزارش جامع تأمین‌کنندگان.

    اطلاعات:
    - تعداد خرید
    - مجموع خرید
    - آخرین خرید
    - تعداد پرداخت
    - مجموع پرداخت
    - مجموع برگشت
    - آخرین پرداخت
    - مانده حساب
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        suppliers = (
            Supplier.objects
            .prefetch_related(
                "purchases",
                "transactions",
            )
            .order_by("name")
        )

        result = []

        for supplier in suppliers:

            # -------------------------
            # خریدها
            # -------------------------

            purchases = (
                supplier.purchases.all()
            )

            purchase_count = (
                purchases.count()
            )

            total_purchase = (
                purchases.aggregate(
                    total=Coalesce(
                        Sum(
                            "total_amount"
                        ),
                        Value(
                            0,
                            output_field=DecimalField(
                                max_digits=20,
                                decimal_places=2,
                            )
                        )
                    )
                )["total"]
            )

            last_purchase = (
                purchases.aggregate(
                    last=Max(
                        "created_at"
                    )
                )["last"]
            )

            # -------------------------
            # تراکنش‌های تأمین‌کننده
            # -------------------------

            transactions = (
                supplier.transactions.all()
            )

            payment_transactions = [
                tx
                for tx in transactions
                if tx.transaction_type == "payment"
            ]

            return_transactions = [
                tx
                for tx in transactions
                if tx.transaction_type == "return"
            ]

            payment_count = len(
                payment_transactions
            )

            total_payment = sum(
                (
                    tx.amount
                    for tx in payment_transactions
                ),
                Decimal("0.00")
            )

            total_return = sum(
                (
                    tx.amount
                    for tx in return_transactions
                ),
                Decimal("0.00")
            )

            last_payment = (
                max(
                    (
                        tx.created_at
                        for tx in payment_transactions
                    ),
                    default=None
                )
            )

            # -------------------------
            # مانده
            # -------------------------

            balance = (
                total_purchase
                - total_payment
                - total_return
            )

            if balance > 0:
                status = "debtor"

            elif balance < 0:
                status = "creditor"

            else:
                status = "settled"

            result.append(
                {
                    "supplier_id":
                        supplier.id,

                    "supplier_name":
                        supplier.name,

                    "purchase_count":
                        purchase_count,

                    "total_purchase":
                        total_purchase,

                    "payment_count":
                        payment_count,

                    "total_payment":
                        total_payment,

                    "total_return":
                        total_return,

                    "balance":
                        abs(balance),

                    "status":
                        status,

                    "last_purchase":
                        last_purchase,

                    "last_payment":
                        last_payment,
                }
            )

        return Response(
            {
                "count": len(result),
                "items": result,
            }
        )
        


class PurchaseReturnViewSet(
    viewsets.ModelViewSet
):
    """
    ثبت برگشت خرید به تأمین‌کننده.

    همزمان:
    1. موجودی انبار کم می‌شود.
    2. InventoryTransaction ثبت می‌شود.
    3. SupplierTransaction(return) ثبت می‌شود.
    """

    serializer_class = (
        PurchaseReturnSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    queryset = (
        PurchaseReturn.objects
        .select_related(
            "purchase",
            "purchase__supplier",
            "purchase__store",
            "product",
            "created_by",
        )
        .order_by(
            "-created_at",
            "-id",
        )
    )

    @transaction.atomic
    def perform_create(
        self,
        serializer
    ):
        """
        ثبت برگشت خرید.
        """

        purchase = (
            serializer.validated_data[
                "purchase"
            ]
        )

        product = (
            serializer.validated_data[
                "product"
            ]
        )

        quantity = (
            serializer.validated_data[
                "quantity"
            ]
        )

        unit_price = (
            serializer.validated_data[
                "unit_price"
            ]
        )

        if quantity <= 0:
            raise ValidationError(
                "مقدار برگشتی باید بیشتر از صفر باشد."
            )

        if not purchase.received:
            raise ValidationError(
                "فقط خرید دریافت‌شده قابل برگشت است."
            )

        # -------------------------
        # پیدا کردن قلم خرید
        # -------------------------

        purchase_item = (
            PurchaseItem.objects
            .filter(
                purchase=purchase,
                product=product,
            )
            .first()
        )

        if not purchase_item:
            raise ValidationError(
                "این کالا در خرید موردنظر وجود ندارد."
            )

        # -------------------------
        # میزان قبلاً برگشت‌داده‌شده
        # -------------------------

        returned_quantity = (
            PurchaseReturn.objects
            .filter(
                purchase=purchase,
                product=product,
            )
            .aggregate(
                total=Sum("quantity")
            )["total"]
            or Decimal("0.000")
        )

        available_for_return = (
            purchase_item.quantity
            - returned_quantity
        )

        if quantity > available_for_return:
            raise ValidationError(
                "مقدار برگشتی بیشتر از مقدار خریداری‌شده است."
            )

        # -------------------------
        # موجودی انبار
        # -------------------------

        inventory = (
            Inventory.objects
            .select_for_update()
            .filter(
                product=product,
                store=purchase.store,
            )
            .first()
        )

        if not inventory:
            raise ValidationError(
                "موجودی این کالا در فروشگاه پیدا نشد."
            )

        if inventory.quantity < quantity:
            raise ValidationError(
                "موجودی انبار برای این برگشت کافی نیست."
            )

        # -------------------------
        # ثبت برگشت
        # -------------------------

        purchase_return = serializer.save(
            created_by=self.request.user,
            unit_price=unit_price,
        )

        # -------------------------
        # کاهش موجودی
        # -------------------------

        inventory.quantity -= quantity

        inventory.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        # -------------------------
        # ثبت گردش انبار
        # -------------------------

        InventoryTransaction.objects.create(
            product=product,
            store=purchase.store,
            transaction_type=(
                InventoryTransaction.TYPE_RETURN
            ),
            quantity=quantity,
            reference_id=purchase_return.id,
            description=(
                f"برگشت خرید #{purchase.id}"
            ),
        )

        # -------------------------
        # کاهش بدهی تأمین‌کننده
        # -------------------------

        SupplierTransaction.objects.create(
            supplier=purchase.supplier,
            transaction_type="return",
            amount=purchase_return.total_amount,
            reference_id=purchase_return.id,
            description=(
                f"برگشت خرید #{purchase.id}"
            ),
        )


class SupplierSettleView(APIView):
    """
    تسویه کامل بدهی یک تأمین‌کننده.

    مبلغ بدهی به صورت خودکار محاسبه می‌شود.
    """

    permission_classes = [
        IsAuthenticated
    ]

    @transaction.atomic
    def post(
        self,
        request,
        supplier_id
    ):
        supplier = get_object_or_404(
            Supplier,
            id=supplier_id
        )

        # -------------------------
        # محاسبه بدهی
        # -------------------------

        purchase_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="purchase",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        payment_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="payment",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        return_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="return",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        adjustment_total = (
            SupplierTransaction.objects
            .filter(
                supplier=supplier,
                transaction_type="adjustment",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        balance = (
            purchase_total
            - payment_total
            - return_total
            + adjustment_total
        )

        # -------------------------
        # حساب تسویه است
        # -------------------------

        if balance <= 0:
            return Response(
                {
                    "detail":
                        "حساب این تأمین‌کننده تسویه است.",
                    "balance":
                        balance,
                }
            )

        # -------------------------
        # انتخاب صندوق مجاز کاربر
        # -------------------------

        cashbox = (
            CashBox.objects
            .select_for_update()
            .filter(
                store__store_users__user=
                request.user
            )
            .order_by("id")
            .first()
        )

        if not cashbox:
            raise ValidationError(
                "صندوقی برای پرداخت پیدا نشد."
            )

        # -------------------------
        # کنترل موجودی صندوق
        # -------------------------

        if cashbox.balance < balance:
            raise ValidationError(
                {
                    "detail":
                        "موجودی صندوق برای تسویه کامل کافی نیست.",
                    "cashbox_balance":
                        cashbox.balance,
                    "required_amount":
                        balance,
                }
            )

        # -------------------------
        # ثبت تراکنش تأمین‌کننده
        # -------------------------

        supplier_tx = (
            SupplierTransaction.objects.create(
                supplier=supplier,
                transaction_type="payment",
                amount=balance,
                description=(
                    f"تسویه کامل حساب "
                    f"تأمین‌کننده {supplier.name}"
                ),
            )
        )

        # -------------------------
        # کاهش موجودی صندوق
        # -------------------------

        cashbox.balance -= balance

        cashbox.save(
            update_fields=[
                "balance",
                "updated_at",
            ]
        )

        # -------------------------
        # ثبت تراکنش صندوق
        # -------------------------

        CashBoxTransaction.objects.create(
            cashbox=cashbox,
            transaction_type="payment",
            amount=balance,
            reference_id=supplier_tx.id,
            description=(
                f"تسویه کامل تأمین‌کننده "
                f"{supplier.name}"
            ),
        )

        return Response(
            {
                "supplier_id":
                    supplier.id,

                "supplier_name":
                    supplier.name,

                "settled_amount":
                    balance,

                "remaining_balance":
                    Decimal("0.00"),

                "cashbox_id":
                    cashbox.id,

                "cashbox_name":
                    cashbox.name,
            }
        )
        
        
class PurchaseReceiptPDFView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        purchase_id
    ):

        purchase = get_object_or_404(
            Purchase.objects
            .prefetch_related(
                "items__product"
            )
            .select_related(
                "supplier",
                "store",
                "user",
            ),
            id=purchase_id,
        )

        pdf_buffer = (
            build_purchase_receipt_pdf(
                purchase
            )
        )

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=(
                f"purchase-receipt-"
                f"{purchase.id}.pdf"
            ),
            content_type="application/pdf",
        )


class ProductBarcodeView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        product_id
    ):

        product = get_object_or_404(
            Product,
            id=product_id,
        )

        try:

            png_buffer = (
                build_product_barcode_png(
                    product
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return FileResponse(
            png_buffer,
            as_attachment=False,
            filename=(
                f"barcode-{product.id}.png"
            ),
            content_type="image/png",
        )


class ProductQRCodeView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        product_id
    ):

        product = get_object_or_404(
            Product,
            id=product_id,
        )

        png_buffer = build_product_qrcode_png(
            product
        )

        return HttpResponse(
            png_buffer.getvalue(),
            content_type="image/png",
        )
        
        
class ProductLabelPDFView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        product_id
    ):

        product = get_object_or_404(
            Product,
            id=product_id,
        )

        try:
            pdf_buffer = (
                build_product_label_pdf(
                    product
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return FileResponse(
            pdf_buffer,
            as_attachment=False,
            filename=(
                f"label-{product.id}.pdf"
            ),
            content_type="application/pdf",
        )

        
class ProductLabelsPDFView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        product_id
    ):

        product = get_object_or_404(
            Product,
            id=product_id,
        )

        count = request.query_params.get(
            "count",
            9,
        )

        try:

            pdf_buffer = (
                build_product_labels_pdf(
                    product,
                    count=count,
                )
            )

        except ValueError as exc:

            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return FileResponse(
            pdf_buffer,
            as_attachment=False,
            filename=(
                f"labels-{product.id}.pdf"
            ),
            content_type="application/pdf",
        )


class ProductBarcodeSearchView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        barcode = request.query_params.get(
            "barcode"
        )

        store_id = request.query_params.get(
            "store"
        )

        if not barcode:
            return Response(
                {
                    "detail":
                        "بارکد ارسال نشده است."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not store_id:
            return Response(
                {
                    "detail":
                        "فروشگاه مشخص نشده است."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        barcode = str(
            barcode
        ).strip()

        product = (
            Product.objects
            .select_related(
                "category",
                "category__store",
            )
            .filter(
                barcode=barcode,
                is_active=True,
            )
            .first()
        )

        if not product:
            return Response(
                {
                    "detail":
                        "کالایی با این بارکد پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        inventory = (
            product.inventories
            .filter(
                store_id=store_id
            )
            .first()
        )

        if not inventory:
            return Response(
                {
                    "detail":
                        "این کالا در این فروشگاه موجود نیست.",
                    "product_id":
                        product.id,
                    "barcode":
                        product.barcode,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "barcode": product.barcode,
                    "unit": product.unit,
                    "purchase_price":
                        product.purchase_price,
                    "sale_price":
                        product.sale_price,
                    "is_active":
                        product.is_active,
                },

                "store": int(store_id),

                "inventory": {
                    "id": inventory.id,
                    "quantity":
                        inventory.quantity,
                },

                "can_sell":
                    inventory.quantity > 0,
            },
            status=status.HTTP_200_OK,
        )
        
        
        