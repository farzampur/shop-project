from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from django.db.models import Count, Q, Sum, F, DecimalField, ExpressionWrapper

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

        queryset = (
            Purchase.objects
            .select_related(
                "supplier",
                "store",
                "user"
            )
            .prefetch_related(
                "items",
                "items__product"
            )
            .order_by("-id")
        )

        supplier_id = self.request.query_params.get(
            "supplier"
        )

        if supplier_id:
            queryset = queryset.filter(
                supplier_id=supplier_id
            )

        store_id = self.request.query_params.get(
            "store"
        )

        if store_id:
            queryset = queryset.filter(
                store_id=store_id
            )

        return queryset

    def perform_create(self, serializer):

        serializer.save(
            user=self.request.user
        )

    @action(
        detail=True,
        methods=["post"]
    )
    def receive(self, request, pk=None):

        purchase = self.get_object()

        try:

            purchase = PurchaseService.receive_purchase(
                purchase
            )

        except ValueError as e:

            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "id": purchase.id,
                "received": purchase.received
            },
            status=status.HTTP_200_OK
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

        