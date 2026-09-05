from django.db.models import Sum, Count, Max, Q, DecimalField, Case, When, Value, F
from django.db.models.functions import TruncDate, TruncMonth, Coalesce
from django.db import transaction
from datetime import datetime
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from decimal import Decimal

from accounts.models import UserStore
from accounts.permissions import StoreRolePermission
from accounts.store_access import has_store_access, require_store_access, user_store_ids
from django.utils import timezone
from .models import Cart, CartItem, Order, OrderItem, Expense, Customer
from .models import CustomerTransaction, CashBox, CashBoxTransaction, CashTransfer

from django.http import FileResponse

from .services import (
    build_invoice_pdf,
    build_thermal_receipt_pdf,
)

from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CheckoutSerializer,
    PaymentSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    OrderPaySerializer,
    ExpenseSerializer,
    CustomerSerializer,
    CustomerTransactionSerializer,
    CashBoxSerializer,
    CashBoxTransactionSerializer,
    CashTransferSerializer,
)

from .services import CheckoutService, OrderService, build_invoice_pdf
from .permissions import CartPermission, get_user_max_discount
from products.models import Product, Inventory

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

        if not has_store_access(
            self.request.user, store_id,
            {"manager", "seller", "cashier"},
        ):
            raise PermissionDenied("شما مجوز فروش در این فروشگاه را ندارید.")

        customer = serializer.validated_data.get("customer")
        if customer and customer.store_id != int(store_id):
            raise ValidationError("مشتری متعلق به این فروشگاه نیست.")
        serializer.save(user=self.request.user, store_id=store_id)              

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

        #product = serializer.validated_data["product"]
        product = (
                serializer.validated_data.get(
                    "product"
                )
            )
        barcode = (
            serializer.validated_data.get(
                "barcode"
            )
        )            
    # -----------------------------
    # پیدا کردن کالا با Barcode
    # -----------------------------

        if not product and barcode:

            product = (
                Product.objects
                .filter(
                    barcode=str(barcode).strip(),
                    category__store_id=cart.store_id,
                    is_active=True,
                )
                .first()
            )

            if not product:

                raise ValidationError(
                    {
                        "barcode":
                            "کالایی با این بارکد پیدا نشد."
                    }
                )

        # -----------------------------
        # ادامه منطق فعلی
        # -----------------------------

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
        serializer.instance = item
        
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
        payments = serializer.validated_data.get("payments", [])

        try:
            cart = Cart.objects.get(id=cart_id, user=request.user)
            if not has_store_access(request.user, cart.store_id, {"manager", "seller", "cashier"}):
                raise PermissionDenied("شما مجوز فروش در این فروشگاه را ندارید.")
            if any(p["method"] in {"cash", "card"} for p in payments) and not has_store_access(
                request.user, cart.store_id, {"manager", "cashier"}
            ):
                raise PermissionDenied("ثبت دریافت نقدی/کارتخوان فقط برای صندوقدار یا مدیر مجاز است.")
            order = CheckoutService.checkout(cart, payments)

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
            store_id__in=user_store_ids(self.request.user)
        ).prefetch_related(
            "items"
        ).select_related(
            "store",
            "user",
        ).order_by("-id")


    @action(detail=True,methods=["post"])
    def change_status(self, request, pk=None):

        order = self.get_object()
        if not has_store_access(request.user, order.store_id, {"manager", "cashier"}):
            raise PermissionDenied("شما مجوز تغییر وضعیت این سفارش را ندارید.")
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
       
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        order = self.get_object()
        if not has_store_access(request.user, order.store_id, {"manager", "cashier"}):
            raise PermissionDenied("شما مجوز دریافت وجه این سفارش را ندارید.")
        serializer = OrderPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.settle(order, serializer.validated_data["payments"])
        return Response({"id": order.id, "status": order.status})


class SalesReportViewSet(viewsets.ViewSet):

    permission_classes = [
        IsAuthenticated
    ]

    def list(self, request):

        queryset = Order.objects.filter(
            store_id__in=user_store_ids(request.user)
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

    @action(detail=False,methods=["get"])
    def monthly(self, request):

        queryset = (
            Order.objects
            .filter(
                store_id__in=user_store_ids(request.user)
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
            
    @action(detail=False,methods=["get"])
    def top_products(self, request):

        queryset = (
            OrderItem.objects
            .filter(order__store_id__in=user_store_ids(request.user))
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
        
    @action(detail=False,methods=["get"])
    def profit(self, request):

        total_sales = Decimal("0")
        total_cost = Decimal("0")
        items = OrderItem.objects.filter(order__store_id__in=user_store_ids(request.user)).select_related("product")

        for item in items:
            sale_amount = item.total_price

            cost_amount = (
                item.quantity *
                item.purchase_price
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

    @action(detail=False,methods=["get"])
    def financial(self, request):

        expense_total = (
            Expense.objects.filter(
                store_id__in=user_store_ids(request.user)
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        total_sales = (
            Order.objects.filter(
                store_id__in=user_store_ids(request.user)
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
        store_ids = user_store_ids(request.user)
        today_orders = Order.objects.filter(
            store_id__in=store_ids,
            created_at__date=today,
        )
        month_orders = Order.objects.filter(
            store_id__in=store_ids,
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

        total_products = Product.objects.filter(category__store_id__in=store_ids).count()
        total_inventory = (
            Inventory.objects.filter(store_id__in=store_ids).aggregate(
                total=Sum("quantity")
            )["total"]
            or 0
        )

        low_stock_products = (
            Inventory.objects.filter(store_id__in=store_ids, quantity__lt=10).count()
        )
        
        total_sales_amount = Decimal("0")
        total_cost_amount = Decimal("0")

        for item in OrderItem.objects.filter(order__store_id__in=store_ids).select_related("product"):
            total_sales_amount += item.total_price
            total_cost_amount += (
                item.quantity *
                item.purchase_price
            )

        total_profit = (
            total_sales_amount -
            total_cost_amount
        )

        expense_total = (
            Expense.objects.filter(
                store_id__in=user_store_ids(request.user)
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

class ExpenseViewSet(viewsets.ModelViewSet):

    allowed_roles_by_method = {
        "GET": {"manager", "cashier"},
        "POST": {"manager", "cashier"},
        "PUT": {"manager", "cashier"},
        "PATCH": {"manager", "cashier"},
        "DELETE": {"manager", "cashier"},
    }

    serializer_class = ExpenseSerializer

    permission_classes = [IsAuthenticated, StoreRolePermission]


    def update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def partial_update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def get_queryset(self):

        return Expense.objects.filter(
            store_id__in=user_store_ids(self.request.user)
        )

    @transaction.atomic
    def perform_create(
        self,
        serializer
    ):
        """
        ثبت هزینه و کسر مبلغ از صندوق
        """

        expense = serializer.save(user=self.request.user)
        if not has_store_access(self.request.user, expense.store_id, {"manager", "cashier"}):
            raise PermissionDenied("شما مجوز ثبت هزینه در این فروشگاه را ندارید.")
        if expense.cashbox.store_id != expense.store_id:
            raise ValidationError("صندوق متعلق به این فروشگاه نیست.")
        cashbox = CashBox.objects.select_for_update().get(pk=expense.cashbox_id)

        if cashbox.balance < expense.amount:

            raise ValidationError(
                "موجودی صندوق کافی نیست."
            )

        cashbox.balance -= expense.amount

        cashbox.save(
            update_fields=[
                "balance",
                "updated_at",
            ]
        )
        
        CashBoxTransaction.objects.create(
            cashbox=cashbox,
            transaction_type="payment",
            amount=expense.amount,
            reference_id=expense.id,
            description=(
                f"Expense: {expense.title}"
            )
        )
        
class CustomerViewSet(viewsets.ModelViewSet):
    allowed_roles_by_method = {
        "GET": {"manager", "seller", "cashier"},
        "POST": {"manager", "seller", "cashier"},
        "PUT": {"manager", "seller", "cashier"},
        "PATCH": {"manager", "seller", "cashier"},
        "DELETE": {"manager"},
    }

    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, StoreRolePermission]

    def get_queryset(self):

        return Customer.objects.filter(
            store_id__in=user_store_ids(self.request.user)
        )
        
class CustomerReportView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        customers = (
            Customer.objects
            .filter(store_id__in=user_store_ids(request.user))
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

class CustomerTransactionViewSet(viewsets.ModelViewSet):
    """
    مدیریت تراکنش‌های مشتری

    sale    : فروش به مشتری
    payment : دریافت وجه از مشتری

    در صورت ثبت payment
    یک دریافت در صندوق نیز ثبت می‌شود.
    """

    allowed_roles_by_method = {
        "GET": {"manager", "cashier"},
        "POST": {"manager", "cashier"},
        "PUT": {"manager", "cashier"},
        "PATCH": {"manager", "cashier"},
        "DELETE": {"manager", "cashier"},
    }

    serializer_class = (
        CustomerTransactionSerializer
    )

    permission_classes = [
        IsAuthenticated,
        StoreRolePermission
    ]

    def update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def partial_update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def get_queryset(self):
        return (
            CustomerTransaction.objects
            .filter(store_id__in=user_store_ids(self.request.user))
            .select_related("customer", "store")
            .order_by("-id")
        )

    @transaction.atomic
    def perform_create(self, serializer):
        customer = serializer.validated_data["customer"]
        if not has_store_access(self.request.user, customer.store_id, {"manager", "cashier"}):
            raise PermissionDenied("شما مجوز ثبت تراکنش مشتری را ندارید.")
        tx_type = serializer.validated_data["transaction_type"]
        if tx_type == "sale" and not has_store_access(self.request.user, customer.store_id, {"manager"}):
            raise PermissionDenied("ثبت دستی بدهی فروش فقط برای مدیر فروشگاه مجاز است.")
        if tx_type == "payment":
            cashbox_id = self.request.data.get("cashbox")
            if not cashbox_id:
                raise ValidationError({"cashbox": "برای دریافت وجه صندوق الزامی است."})
            cashbox = CashBox.objects.select_for_update().filter(
                pk=cashbox_id, store_id=customer.store_id
            ).first()
            if not cashbox:
                raise ValidationError({"cashbox": "صندوق متعلق به این فروشگاه نیست."})
            customer_tx = serializer.save(store=customer.store)
            cashbox.balance += customer_tx.amount
            cashbox.save(update_fields=["balance", "updated_at"])
            CashBoxTransaction.objects.create(
                cashbox=cashbox, transaction_type="receive",
                amount=customer_tx.amount, reference_id=customer_tx.id,
                description=f"دریافت از مشتری {customer_tx.customer}",
            )
        else:
            serializer.save(store=customer.store)

class CustomerBalanceView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, customer_id):

        customer = get_object_or_404(
            Customer.objects.filter(store_id__in=user_store_ids(request.user)),
            id=customer_id,
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

class DebtorCustomersView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        result = []
        for customer in Customer.objects.filter(store_id__in=user_store_ids(request.user)):

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

            balance = sales_amount - payment_amount
            if balance > 0:
                result.append(
                    {
                        "customer_id": customer.id,
                        "customer_name": str(customer),
                        "balance": balance,
                    }
                )

        result.sort(
            key=lambda x: x["balance"],
            reverse=True
        )

        return Response(result)
        
class CreditorCustomersView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        result = []

        for customer in Customer.objects.filter(store_id__in=user_store_ids(request.user)):
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

            balance = sales_amount - payment_amount

            if balance < 0:
                result.append(
                    {
                        "customer_id": customer.id,
                        "customer_name": str(customer),
                        "credit": abs(balance),
                    }
                )

        return Response(result)

class CustomerLedgerView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request, customer_id):

        customer = get_object_or_404(
            Customer.objects.filter(store_id__in=user_store_ids(request.user)),
            id=customer_id,
        )

        transactions = (
            CustomerTransaction.objects
            .filter(
                customer=customer
            )
            .order_by(
                "created_at",
                "id"
            )
        )

        balance = Decimal("0.00")

        result = []
        for tx in transactions:
            if tx.transaction_type == "sale":
                balance += tx.amount
            elif tx.transaction_type == "payment":
                balance -= tx.amount

            result.append(
                {
                    "id": tx.id,
                    "date": tx.created_at,
                    "type": tx.transaction_type,
                    "amount": tx.amount,
                    "description": tx.description,
                    "balance": balance,
                }
            )

        return Response(
            {
                "customer_id": customer.id,
                "customer_name": str(customer),
                "transactions": result,
                "final_balance": balance,
            }
        )
                       
class CashBoxViewSet(
    viewsets.ModelViewSet
):
    """
    مدیریت صندوق‌ها
    """

    allowed_roles_by_method = {
        "GET": {"manager", "cashier"},
        "POST": {"manager", "cashier"},
        "PUT": {"manager", "cashier"},
        "PATCH": {"manager", "cashier"},
        "DELETE": {"manager", "cashier"},
    }

    serializer_class = (
        CashBoxSerializer
    )

    permission_classes = [IsAuthenticated, StoreRolePermission]


    def perform_destroy(self, instance):
        if instance.balance != 0 or instance.transactions.exists() or instance.payments.exists():
            raise ValidationError("صندوق دارای سابقه مالی است و قابل حذف نیست.")
        instance.delete()

    def get_queryset(self):
        return CashBox.objects.filter(
            store_id__in=user_store_ids(self.request.user)
        ).select_related("store").order_by("name")


class CashBoxTransactionViewSet(
    viewsets.ModelViewSet
):
    """
    مدیریت تراکنش‌های صندوق

    deposit  => واریز
    receive  => دریافت
    withdraw => برداشت
    payment  => پرداخت
    """

    allowed_roles_by_method = {
        "GET": {"manager", "cashier"},
        "POST": {"manager", "cashier"},
        "PUT": {"manager", "cashier"},
        "PATCH": {"manager", "cashier"},
        "DELETE": {"manager", "cashier"},
    }

    serializer_class = (
        CashBoxTransactionSerializer
    )

    permission_classes = [IsAuthenticated, StoreRolePermission]


    def update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def partial_update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def get_queryset(self):
        return CashBoxTransaction.objects.filter(
            cashbox__store_id__in=user_store_ids(self.request.user)
        ).select_related("cashbox").order_by("-id")

    @transaction.atomic
    def perform_create(
        self,
        serializer
    ):
        """
        ثبت تراکنش صندوق
        و بروزرسانی موجودی
        """

        cashbox_id = serializer.validated_data["cashbox"].id
        cashbox = CashBox.objects.select_for_update().get(pk=cashbox_id)
        if not has_store_access(self.request.user, cashbox.store_id, {"manager", "cashier"}):
            raise PermissionDenied("شما مجوز عملیات صندوق را ندارید.")

        transaction_type = (
            serializer.validated_data[
                "transaction_type"
            ]
        )

        amount = serializer.validated_data[
            "amount"
        ]

        # اعتبارسنجی قبل از ثبت
        if transaction_type in (
            "withdraw",
            "payment",
        ):

            if cashbox.balance < amount:

                raise ValidationError(
                    "موجودی صندوق کافی نیست."
                )

        # ثبت تراکنش
        transaction_obj = serializer.save()

        # بروزرسانی موجودی
        if transaction_type in (
            "withdraw",
            "payment",
        ):

            cashbox.balance -= amount

        elif transaction_type in (
            "deposit",
            "receive",
        ):

            cashbox.balance += amount

        cashbox.save(
            update_fields=[
                "balance",
                "updated_at",
            ]
        )

        return transaction_obj
        
        
class FinancialReportView(
    APIView
):
    """
    گزارش دریافت و پرداخت
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        receipts = (
            CashBoxTransaction.objects
            .filter(
                cashbox__store_id__in=user_store_ids(request.user),
                transaction_type__in=[
                    "receive",
                    "deposit",
                ]
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        payments = (
            CashBoxTransaction.objects
            .filter(
                cashbox__store_id__in=user_store_ids(request.user),
                transaction_type__in=[
                    "payment",
                    "withdraw",
                ]
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        return Response(
            {
                "receipts": receipts,
                "payments": payments,
                "net_cash_flow": (
                    receipts - payments
                ),
            }
        )


class CashLedgerView(
    APIView
):
    """
    گردش صندوق
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        transactions = (
            CashBoxTransaction.objects
            .filter(cashbox__store_id__in=user_store_ids(request.user))
            .select_related("cashbox")
            .order_by("-id")
        )

        data = []

        for tx in transactions:

            data.append(
                {
                    "id": tx.id,
                    "cashbox": tx.cashbox.name,
                    "type": tx.transaction_type,
                    "amount": tx.amount,
                    "reference_id": tx.reference_id,
                    "description": tx.description,
                }
            )

        return Response(data)




class CashBoxBalanceReportView(
    APIView
):
    """
    گزارش مانده صندوق‌ها

    نمایش:
    - مانده صندوق
    - تعداد کل تراکنش‌ها
    - تعداد دریافت‌ها
    - تعداد پرداخت‌ها
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):
        """
        دریافت گزارش مانده صندوق‌ها
        """

        cashboxes = (
            CashBox.objects
            .filter(store_id__in=user_store_ids(request.user))
            .select_related("store")
            .annotate(
                transaction_count=Count(
                    "transactions"
                ),

                receive_count=Count(
                    "transactions",
                    filter=Q(
                        transactions__transaction_type__in=[
                            "receive",
                            "deposit",
                        ]
                    )
                ),

                payment_count=Count(
                    "transactions",
                    filter=Q(
                        transactions__transaction_type__in=[
                            "payment",
                            "withdraw",
                        ]
                    )
                ),
            )
            .order_by("name")
        )

        data = []

        for cashbox in cashboxes:

            data.append(
                {
                    "id": cashbox.id,

                    "name": (
                        cashbox.name
                    ),

                    "store": (
                        cashbox.store.name
                    ),

                    "balance": (
                        cashbox.balance
                    ),

                    "transaction_count": (
                        cashbox.transaction_count
                    ),

                    "receive_count": (
                        cashbox.receive_count
                    ),

                    "payment_count": (
                        cashbox.payment_count
                    ),
                }
            )

        return Response(data)
        
        

class DailyCashFlowReportView(
    APIView
):
    """
    گزارش گردش مالی روزانه

    Query Params:

    start_date=YYYY-MM-DD
    end_date=YYYY-MM-DD

    Example:

    /api/sales/daily-cash-flow-report/

    /api/sales/daily-cash-flow-report/
    ?start_date=2026-08-01

    /api/sales/daily-cash-flow-report/
    ?start_date=2026-08-01
    &end_date=2026-08-31
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):
        """
        تولید گزارش گردش مالی روزانه
        """

        start_date = request.GET.get(
            "start_date"
        )

        end_date = request.GET.get(
            "end_date"
        )

        queryset = CashBoxTransaction.objects.filter(
            cashbox__store_id__in=user_store_ids(request.user)
        )

        # اعتبارسنجی تاریخ شروع
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
                        "فرمت صحیح YYYY-MM-DD است."
                    }
                )

            queryset = queryset.filter(
                created_at__date__gte=
                start_date
            )

        # اعتبارسنجی تاریخ پایان
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
                        "فرمت صحیح YYYY-MM-DD است."
                    }
                )

            queryset = queryset.filter(
                created_at__date__lte=
                end_date
            )

        report = (
            queryset
            .annotate(
                day=TruncDate(
                    "created_at"
                )
            )
            .values(
                "day"
            )
            .annotate(
                transaction_count=Count(
                    "id"
                ),

                receipts=Coalesce(
                    Sum(
                        Case(
                            When(
                                transaction_type__in=[
                                    "deposit",
                                    "receive",
                                ],
                                then=F(
                                    "amount"
                                )
                            ),
                            default=Value(
                                0,
                                output_field=
                                DecimalField(
                                    max_digits=12,
                                    decimal_places=2
                                )
                            ),
                            output_field=
                            DecimalField(
                                max_digits=12,
                                decimal_places=2
                            )
                        )
                    ),
                    Value(
                        0,
                        output_field=
                        DecimalField(
                            max_digits=12,
                            decimal_places=2
                        )
                    )
                ),

                payments=Coalesce(
                    Sum(
                        Case(
                            When(
                                transaction_type__in=[
                                    "withdraw",
                                    "payment",
                                ],
                                then=F(
                                    "amount"
                                )
                            ),
                            default=Value(
                                0,
                                output_field=
                                DecimalField(
                                    max_digits=12,
                                    decimal_places=2
                                )
                            ),
                            output_field=
                            DecimalField(
                                max_digits=12,
                                decimal_places=2
                            )
                        )
                    ),
                    Value(
                        0,
                        output_field=
                        DecimalField(
                            max_digits=12,
                            decimal_places=2
                        )
                    )
                ),
            )
            .order_by(
                "-day"
            )
        )

        result = []

        for row in report:

            receipts = (
                row["receipts"]
                or 0
            )

            payments = (
                row["payments"]
                or 0
            )

            result.append(
                {
                    "day":
                        row["day"],

                    "transaction_count":
                        row[
                            "transaction_count"
                        ],

                    "receipts":
                        receipts,

                    "payments":
                        payments,

                    "net_cash_flow":
                        receipts -
                        payments,
                }
            )

        return Response(
            result
        )



class CashTransferViewSet(
    viewsets.ModelViewSet
):
    """
    انتقال وجه بین صندوق‌ها
    """

    allowed_roles_by_method = {
        "GET": {"manager", "cashier"},
        "POST": {"manager", "cashier"},
        "PUT": {"manager", "cashier"},
        "PATCH": {"manager", "cashier"},
        "DELETE": {"manager", "cashier"},
    }

    serializer_class = (
        CashTransferSerializer
    )

    permission_classes = [IsAuthenticated, StoreRolePermission]

    def update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def partial_update(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("تغییر یا حذف این سند مالی پس از ثبت مجاز نیست.")

    def get_queryset(self):
        return (
            CashTransfer.objects
            .filter(from_cashbox__store_id__in=user_store_ids(self.request.user))
            .select_related("from_cashbox", "to_cashbox")
            .order_by("-id")
        )

    @transaction.atomic
    def perform_create(self, serializer):
        from_cashbox = serializer.validated_data["from_cashbox"]
        to_cashbox = serializer.validated_data["to_cashbox"]

        amount = serializer.validated_data["amount"]
        if amount <= 0:
            raise ValidationError("مبلغ انتقال باید بیشتر از صفر باشد.")

        if from_cashbox.store_id != to_cashbox.store_id:
            raise ValidationError("انتقال بین دو فروشگاه مجاز نیست.")
        if not has_store_access(self.request.user, from_cashbox.store_id, {"manager", "cashier"}):
            raise PermissionDenied("شما مجوز انتقال صندوق را ندارید.")

        from_cashbox = CashBox.objects.select_for_update().get(pk=from_cashbox.pk)
        to_cashbox = CashBox.objects.select_for_update().get(pk=to_cashbox.pk)

        if (
            from_cashbox.id ==
            to_cashbox.id
        ):
            raise ValidationError(
                "صندوق مبدا و مقصد "
                "نمی‌توانند یکسان باشند."
            )

        if (
            from_cashbox.balance <
            amount
        ):
            raise ValidationError(
                "موجودی صندوق مبدا کافی نیست."
            )

        transfer = serializer.save(
            created_by=
            self.request.user
        )

        # کسر از صندوق مبدا

        from_cashbox.balance -= amount

        from_cashbox.save(
            update_fields=[
                "balance",
                "updated_at",
            ]
        )

        # افزودن به صندوق مقصد

        to_cashbox.balance += amount

        to_cashbox.save(
            update_fields=[
                "balance",
                "updated_at",
            ]
        )

        # ثبت تراکنش خروج

        CashBoxTransaction.objects.create(
            cashbox=from_cashbox,
            transaction_type="withdraw",
            amount=amount,
            reference_id=transfer.id,
            description=(
                f"Transfer To "
                f"{to_cashbox.name}"
            )
        )

        # ثبت تراکنش ورود

        CashBoxTransaction.objects.create(
            cashbox=to_cashbox,
            transaction_type="deposit",
            amount=amount,
            reference_id=transfer.id,
            description=(
                f"Transfer From "
                f"{from_cashbox.name}"
            )
        )
        

class InvoicePDFView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        order_id
    ):

        order = get_object_or_404(
            Order.objects
            .prefetch_related(
                "items"
            )
            .select_related(
                "store",
                "user",
            ),
            id=order_id,
            store_id__in=user_store_ids(request.user),
        )

        pdf_buffer = (
            build_invoice_pdf(order)
        )

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=(
                f"invoice-{order.id}.pdf"
            ),
            content_type="application/pdf",
        )


class ThermalReceiptPDFView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        order_id
    ):

        order = get_object_or_404(
            Order.objects
            .prefetch_related(
                "items"
            )
            .select_related(
                "store",
                "user",
                "customer",
            ),
            id=order_id,
            store_id__in=user_store_ids(request.user),
        )

        pdf_buffer = (
            build_thermal_receipt_pdf(
                order
            )
        )

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=(
                f"receipt-{order.id}.pdf"
            ),
            content_type="application/pdf",
        )

        