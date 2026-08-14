from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncMonth
from django.db.models.functions import Coalesce

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from decimal import Decimal

from accounts.models import UserStore
from django.utils import timezone
from django.db.models import   Sum, Count, Max
from .models import Cart, CartItem, Order, OrderItem, Expense, Customer
from .models import CustomerTransaction


from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CheckoutSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    ExpenseSerializer,
    CustomerSerializer,
    CustomerTransactionSerializer,
)

from .services import CheckoutService
from .services import OrderService


from .permissions import (
    CartPermission,
    get_user_max_discount,
)

from products.models import (
    Product,
    Inventory,
)

class CartViewSet(viewsets.ModelViewSet):

    serializer_class = CartSerializer

    permission_classes = [
        IsAuthenticated,
        CartPermission
    ]

    def get_queryset(self):

        return Cart.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "items__product"
        )

    def perform_create(self, serializer):

        store_id = self.request.data.get("store")

        if not store_id:
            raise PermissionDenied(
                "فروشگاه مشخص نشده است."
            )

        has_access = UserStore.objects.filter(
            user=self.request.user,
            store_id=store_id
        ).exists()

        if not has_access:
            raise PermissionDenied(
                "شما به این فروشگاه دسترسی ندارید."
            )

        serializer.save(
            user=self.request.user,
            store_id=store_id
        )
        
        

class CartItemViewSet(viewsets.ModelViewSet):

    permission_classes = [
        IsAuthenticated,
        CartPermission,
    ]

    def get_queryset(self):

        cart_id = self.kwargs.get("cart_pk")

        return CartItem.objects.filter(
            cart_id=cart_id,
            cart__user=self.request.user,
        ).select_related(
            "cart",
            "product",
        )

    def get_serializer_class(self):

        if self.action == "create":
            return CartItemCreateSerializer

        if self.action in ["update", "partial_update"]:
            return CartItemUpdateSerializer

        return CartItemSerializer

    def perform_create(self, serializer):

        cart_id = self.kwargs.get("cart_pk")

        try:
            cart = Cart.objects.get(
                id=cart_id,
                user=self.request.user,
            )
        except Cart.DoesNotExist:
            raise ValidationError(
                "سبد خرید پیدا نشد."
            )

        product = serializer.validated_data["product"]

        quantity = serializer.validated_data["quantity"]

        discount_percent = serializer.validated_data.get(
            "discount_percent",
            0,
        )
        
        max_discount = get_user_max_discount(
            self.request.user,
            cart.store
        )

        if max_discount is None:
            raise ValidationError(
                "شما به این فروشگاه دسترسی ندارید."
            )

        if discount_percent > max_discount:
            raise ValidationError(
                f"حداکثر تخفیف مجاز برای شما "
                f"{max_discount}% است."
            )        

        inventory = product.inventories.filter(
            store=cart.store
        ).first()

        if not inventory:
            raise ValidationError(
                "این کالا در این فروشگاه موجود نیست."
            )

        if inventory.quantity < quantity:
            raise ValidationError(
                f"موجودی کافی نیست. موجودی فعلی: "
                f"{inventory.quantity}"
            )

        unit_price = product.sale_price

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_percent": discount_percent,
            },
        )

        if not created:

            new_quantity = item.quantity + quantity

            if inventory.quantity < new_quantity:
                raise ValidationError(
                    f"موجودی کافی نیست. موجودی فعلی: "
                    f"{inventory.quantity}"
                )

            item.quantity = new_quantity
            item.unit_price = unit_price
            item.discount_percent = discount_percent

            item.save()

    def perform_update(self, serializer):

        item = self.get_object()

        new_quantity = serializer.validated_data.get(
            "quantity",
            item.quantity,
        )

        new_discount = serializer.validated_data.get(
            "discount_percent",
            item.discount_percent,
        )

        max_discount = get_user_max_discount(
            self.request.user,
            item.cart.store
        )

        if max_discount is None:
            raise ValidationError(
                "شما به این فروشگاه دسترسی ندارید."
            )

        if new_discount > max_discount:
            raise ValidationError(
                f"حداکثر تخفیف مجاز برای شما "
                f"{max_discount}% است."
            )

        inventory = item.product.inventories.filter(
            store=item.cart.store
        ).first()

        if not inventory:
            raise ValidationError(
                "این کالا در این فروشگاه موجود نیست."
            )

        if inventory.quantity < new_quantity:
            raise ValidationError(
                f"موجودی کافی نیست. موجودی فعلی: "
                f"{inventory.quantity}"
            )

        serializer.save(
            unit_price=item.product.sale_price
        )
        
        
        
class CheckoutView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]
    def post(self, request):

        serializer = CheckoutSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        cart_id = serializer.validated_data["cart_id"]

        try:
            cart = Cart.objects.get(
                id=cart_id,
                user=request.user
            )

            order = CheckoutService.checkout(cart)

        except Cart.DoesNotExist:
            return Response(
                {
                    "detail": "سبد خرید پیدا نشد."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "id": order.id,
                "status": order.status,
                "total_before_discount": order.total_before_discount,
                "total_discount": order.total_discount,
                "total_price": order.total_price,
            },
            status=status.HTTP_201_CREATED
        )



class OrderViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = OrderSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):

        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "items"
        ).select_related(
            "store",
            "user",
        ).order_by("-id")


    @action(
    detail=True,
    methods=["post"]
    )
    def change_status(self, request, pk=None):

        order = self.get_object()

        serializer = OrderStatusSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        order = OrderService.change_status(
            order,
            serializer.validated_data["status"]
        )

        return Response(
            {
                "id": order.id,
                "status": order.status,
            }
        )       


       
class SalesReportViewSet(
    viewsets.ViewSet
):

    permission_classes = [
        IsAuthenticated
    ]

    def list(self, request):

        queryset = Order.objects.filter(
            user=request.user
        ).annotate(
            day=TruncDate("created_at")
        ).values(
            "day"
        ).annotate(
            order_count=Count("id"),
            total_sales=Sum("total_price")
        ).order_by(
            "-day"
        )

        return Response(
            queryset
        )

    @action(
        detail=False,
        methods=["get"]
    )
    def monthly(self, request):

        queryset = (
            Order.objects
            .filter(
                user=request.user
            )
            .annotate(
                month=TruncMonth(
                    "created_at"
                )
            )
            .values(
                "month"
            )
            .annotate(
                order_count=Count("id"),
                total_sales=Sum(
                    "total_price"
                )
            )
            .order_by(
                "-month"
            )
        )

        return Response(
            queryset
        )
            
    @action(
        detail=False,
        methods=["get"]
    )
    def top_products(self, request):

        queryset = (
            OrderItem.objects
            .values(
                "product_id",
                "product_name"
            )
            .annotate(
                total_quantity=Sum(
                    "quantity"
                ),
                total_sales=Sum(
                    "total_price"
                )
            )
            .order_by(
                "-total_quantity"
            )[:20]
        )

        return Response(
            queryset
        )        
        
    @action(
        detail=False,
        methods=["get"]
    )
    def profit(self, request):

        total_sales = Decimal("0")
        total_cost = Decimal("0")

        items = OrderItem.objects.all()

        for item in items:

            sale_amount = item.total_price

            cost_amount = (
                item.quantity *
                item.product.purchase_price
            )

            total_sales += sale_amount
            total_cost += cost_amount

        total_profit = (
            total_sales -
            total_cost
        )

        return Response(
            {
                "total_sales": total_sales,
                "total_cost": total_cost,
                "total_profit": total_profit,
            }
        )        

    @action(
        detail=False,
        methods=["get"]
    )
    def financial(self, request):

        expense_total = (
            Expense.objects.filter(
                user=request.user
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        total_sales = (
            Order.objects.filter(
                user=request.user
            ).aggregate(
                total=Sum("total_price")
            )["total"]
            or 0
        )

        return Response(
            {
                "sales": total_sales,
                "expenses": expense_total,
                "balance":
                    total_sales -
                    expense_total,
            }
        )
    
        
        
class DashboardView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        today = timezone.now().date()

        today_orders = Order.objects.filter(
            created_at__date=today
        )

        month_orders = Order.objects.filter(
            created_at__year=today.year,
            created_at__month=today.month,
        )

        today_sales = (
            today_orders.aggregate(
                total=Sum("total_price")
            )["total"]
            or 0
        )

        month_sales = (
            month_orders.aggregate(
                total=Sum("total_price")
            )["total"]
            or 0
        )

        total_products = Product.objects.count()

        total_inventory = (
            Inventory.objects.aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )

        low_stock_products = (
            Inventory.objects.filter(
                quantity__lt=10
            ).count()
        )
        
        from decimal import Decimal

        total_sales_amount = Decimal("0")
        total_cost_amount = Decimal("0")

        for item in OrderItem.objects.all():

            total_sales_amount += item.total_price

            total_cost_amount += (
                item.quantity *
                item.product.purchase_price
            )

        total_profit = (
            total_sales_amount -
            total_cost_amount
        )

        expense_total = (
            Expense.objects.filter(
                user=request.user
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        net_profit = (
            total_profit -
            expense_total
        )

        return Response(
            {
                "today_orders": today_orders.count(),
                "month_orders": month_orders.count(),
                "today_sales": today_sales,
                "month_sales": month_sales,
                
                "total_products": total_products,
                "total_inventory": total_inventory,
                "low_stock_products": low_stock_products,
                
                "total_profit": total_profit,
                
                "expense_total": expense_total,
                "net_profit": net_profit,                
            }
        )



class ExpenseViewSet(
    viewsets.ModelViewSet
):

    serializer_class = ExpenseSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return Expense.objects.filter(
            user=self.request.user
        )

    def perform_create(
        self,
        serializer
    ):

        serializer.save(
            user=self.request.user
        )
        
class CustomerViewSet(
    viewsets.ModelViewSet
):

    serializer_class = CustomerSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return Customer.objects.all()

        
        

class CustomerReportView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        customers = (
            Customer.objects
            .annotate(
                order_count=Count(
                    "orders"
                ),

                total_purchase=Sum(
                    "orders__total_price"
                ),

                last_order_date=Max(
                    "orders__created_at"
                ),
            )
            .filter(
                order_count__gt=0
            )
            .order_by(
                "-total_purchase"
            )[:10]
        )

        result = []

        for customer in customers:

            result.append(
                {
                    "id": customer.id,

                    "name": str(
                        customer
                    ),

                    "mobile":
                        customer.mobile,

                    "order_count":
                        customer.order_count,

                    "total_purchase":
                        customer.total_purchase
                        or 0,

                    "last_order_date":
                        customer.last_order_date,
                }
            )

        return Response(
            result
        )



class CustomerTransactionViewSet(
    viewsets.ModelViewSet
):

    serializer_class = (
        CustomerTransactionSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    queryset = (
        CustomerTransaction.objects
        .select_related(
            "customer"
        )
        .order_by("-id")
    )


class CustomerBalanceView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, customer_id):

        customer = Customer.objects.get(
            id=customer_id
        )

        sales_amount = (
            CustomerTransaction.objects
            .filter(
                customer=customer,
                transaction_type="sale"
            )
            .aggregate(
                total=Coalesce(
                    Sum("amount"),
                    Decimal("0.00"),
                    output_field=DecimalField()
                )
            )["total"]
        )

        payment_amount = (
            CustomerTransaction.objects
            .filter(
                customer=customer,
                transaction_type="payment"
            )
            .aggregate(
                total=Coalesce(
                    Sum("amount"),
                    Decimal("0.00"),
                    output_field=DecimalField()
                )
            )["total"]
        )

        balance = (
            sales_amount -
            payment_amount
        )

        return Response(
            {
                "customer_id": customer.id,
                "customer_name": str(customer),
                "sales": sales_amount,
                "payments": payment_amount,
                "balance": balance,
            }
        )


        