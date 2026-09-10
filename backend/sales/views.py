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
from .models import Cart, CartItem, Order, OrderItem, Expense, Customer, CashDayClose
from .models import CustomerTransaction, CashBox, CashBoxTransaction, CashTransfer, Payment

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
from core.audit import audit
from products.pricing import get_effective_sale_price

class CartViewSet(viewsets.ModelViewSet):

    serializer_class = CartSerializer

    permission_classes = [
        IsAuthenticated,
        CartPermission
    ]

    def get_queryset(self):
        queryset = Cart.objects.filter(
            user=self.request.user
        ).prefetch_related(
            "items__product"
        )

        store_id = self.request.query_params.get("store")
        if store_id:
            queryset = queryset.filter(store_id=store_id)

        return queryset.order_by("-updated_at", "-id")

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

    def create(self, request, *args, **kwargs):
        """Create/update a cart item and always return the full read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        output = CartItemSerializer(
            serializer.instance,
            context=self.get_serializer_context(),
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        output = CartItemSerializer(
            serializer.instance,
            context=self.get_serializer_context(),
        )
        return Response(output.data)

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
                    inventories__store_id=cart.store_id,
                    inventories__store__store_users__user=self.request.user,
                    inventories__store__store_users__is_active=True,
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

        if not product:
            raise ValidationError({"product": "کالا مشخص نشده است."})

        if not product.inventories.filter(store_id=cart.store_id).exists():
            raise ValidationError(
                {"product": "این کالا در فروشگاه انتخاب‌شده تخصیص داده نشده است."}
            )

        # -----------------------------
        # ادامه منطق فعلی
        # -----------------------------

        quantity = serializer.validated_data["quantity"]
        price_type = serializer.validated_data.get("price_type", "retail")

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
                f"موجودی کالای «{product.name}» برای فروش کافی نیست. "
                f"موجودی فعلی: {inventory.quantity} واحد؛ "
                f"مقدار درخواستی: {quantity} واحد."
            )

        unit_price = get_effective_sale_price(product, cart.store_id, price_type=price_type)
        if unit_price is None:
            raise ValidationError({"price_type": "برای این نوع قیمت، قیمت فعال و معتبر وجود ندارد."})

        # نوع قیمت بخشی از هویت آیتم سبد است.
        # بنابراین خرده/عمده/ویژه برای یک کالا باید آیتم‌های جداگانه داشته باشند.
        # قبلاً فقط cart + product در lookup بود و نوع قیمت دوم، آیتم اول را پیدا
        # می‌کرد و به جای ایجاد آیتم جدید، تعداد همان آیتم را افزایش می‌داد.
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            price_type=price_type,
            defaults={
                "quantity": quantity,
                "unit_price": unit_price,
                "discount_percent": discount_percent,
            },
        )

        if not created:
            # همین price_type پیدا شده؛ فقط مقدار همان آیتم افزایش می‌یابد.
            new_quantity = item.quantity + quantity

            if inventory.quantity < new_quantity:
                raise ValidationError(
                    f"موجودی کالای «{product.name}» برای افزودن به سبد کافی نیست. "
                    f"موجودی فعلی: {inventory.quantity} واحد؛ "
                    f"مقدار درخواستی نهایی سبد: {new_quantity} واحد."
                )

            item.quantity = new_quantity
            item.unit_price = unit_price
            item.price_type = price_type
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
                f"موجودی کالای «{item.product.name}» برای فروش کافی نیست. "
                f"موجودی فعلی: {inventory.quantity} واحد؛ "
                f"مقدار درخواستی: {new_quantity} واحد."
            )

        serializer.save(
            unit_price=get_effective_sale_price(item.product, item.cart.store_id, price_type=item.price_type)
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
        queryset = Order.objects.filter(
            store_id__in=user_store_ids(self.request.user)
        ).prefetch_related(
            "items"
        ).select_related(
            "store",
            "user",
        )
        store_id = self.request.query_params.get("store")
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        return queryset.order_by("-id")


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

        new_status = serializer.validated_data["status"]
        reason = serializer.validated_data.get("reason", "")
        order = OrderService.change_status(order, new_status, user=request.user, reason=reason)
        if new_status == "cancelled":
            audit(user=request.user, action="cancel", model_name="Order", object_id=order.id, store=order.store, description=f"لغو فروش #{order.id}", metadata={"reason": reason})

        payload = {"id": order.id, "status": order.status}
        if order.status == "cancelled":
            payload["cashbox_reconciliation"] = OrderService.cashbox_reconciliation(order)
        return Response(payload)       
       
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
    permission_classes = [IsAuthenticated]

    def _orders(self, request, include_cancelled=True):
        allowed_store_ids = set(user_store_ids(request.user))
        qs = Order.objects.filter(store_id__in=allowed_store_ids)
        store_id = request.query_params.get("store")
        if store_id:
            try:
                store_id_int = int(store_id)
            except (TypeError, ValueError):
                raise ValidationError({"store": "شناسه فروشگاه نامعتبر است."})
            if store_id_int not in allowed_store_ids:
                raise PermissionDenied("شما به این فروشگاه دسترسی ندارید.")
            qs = qs.filter(store_id=store_id_int)
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            try: datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError: raise ValidationError({"start_date": "فرمت صحیح YYYY-MM-DD است."})
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            try: datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError: raise ValidationError({"end_date": "فرمت صحیح YYYY-MM-DD است."})
            qs = qs.filter(created_at__date__lte=end_date)
        return qs if include_cancelled else qs.exclude(status="cancelled")

    def list(self, request):
        rows = self._orders(request, False).annotate(day=TruncDate("created_at")).values("day").annotate(order_count=Count("id"), total_sales=Sum("total_price")).order_by("-day")
        return Response(list(rows))

    @action(detail=False, methods=["get"])
    def summary(self, request):
        orders = self._orders(request, False)
        cancelled = self._orders(request, True).filter(status="cancelled")
        sales = orders.aggregate(
            total=Coalesce(Sum("total_price"), Decimal("0.00"), output_field=DecimalField()),
            before_discount=Coalesce(Sum("total_before_discount"), Decimal("0.00"), output_field=DecimalField()),
            discount=Coalesce(Sum("total_discount"), Decimal("0.00"), output_field=DecimalField()),
        )
        profit_rows = OrderItem.objects.filter(order__in=orders).aggregate(
            cost=Coalesce(
                Sum(F("quantity") * F("purchase_price")),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        )
        payment_rows = Payment.objects.filter(order__in=orders).values("method").annotate(
            amount=Coalesce(Sum("amount"), Decimal("0.00"), output_field=DecimalField())
        )
        payment_map = {row["method"]: row["amount"] for row in payment_rows}
        cancelled_total = cancelled.aggregate(
            total=Coalesce(Sum("total_price"), Decimal("0.00"), output_field=DecimalField())
        )["total"]
        total_sales = sales["total"]
        total_cost = profit_rows["cost"]
        return Response({
            "order_count": orders.count(),
            "sales": total_sales,
            "before_discount": sales["before_discount"],
            "discount": sales["discount"],
            "cost": total_cost,
            "gross_profit": total_sales - total_cost,
            "cancelled_count": cancelled.count(),
            "cancelled_sales": cancelled_total,
            "cash": payment_map.get("cash", Decimal("0.00")),
            "card": payment_map.get("card", Decimal("0.00")),
            "credit": payment_map.get("credit", Decimal("0.00")),
        })

    @action(detail=False, methods=["get"])
    def monthly(self, request):
        rows = self._orders(request, False).annotate(month=TruncMonth("created_at")).values("month").annotate(order_count=Count("id"), total_sales=Sum("total_price")).order_by("-month")
        return Response(rows)

    @action(detail=False, methods=["get"])
    def top_products(self, request):
        rows = OrderItem.objects.filter(order__in=self._orders(request, False)).values("product_id", "product_name").annotate(total_quantity=Sum("quantity"), total_sales=Sum("total_price")).order_by("-total_quantity")[:20]
        return Response(rows)

    @action(detail=False, methods=["get"])
    def profit(self, request):
        total_sales = Decimal("0"); total_cost = Decimal("0")
        for item in OrderItem.objects.filter(order__in=self._orders(request, False)).only("quantity", "purchase_price", "total_price"):
            total_sales += item.total_price; total_cost += item.quantity * item.purchase_price
        return Response({"total_sales": total_sales, "total_cost": total_cost, "total_profit": total_sales-total_cost})

    @action(detail=False, methods=["get"])
    def financial(self, request):
        sales = self._orders(request, False).aggregate(total=Sum("total_price"))["total"] or Decimal("0")
        expenses = Expense.objects.filter(store_id__in=user_store_ids(request.user))
        store_id=request.query_params.get("store")
        if store_id: expenses=expenses.filter(store_id=store_id)
        start_date=request.query_params.get("start_date"); end_date=request.query_params.get("end_date")
        if start_date: expenses=expenses.filter(expense_date__gte=start_date)
        if end_date: expenses=expenses.filter(expense_date__lte=end_date)
        expense_total=expenses.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        return Response({"sales":sales,"expenses":expense_total,"balance":sales-expense_total})

    @action(detail=False, methods=["get"])
    def payment_methods(self, request):
        labels={"cash":"نقدی","card":"کارتخوان","credit":"اعتباری"}
        rows=Payment.objects.filter(order__in=self._orders(request, False)).values("method").annotate(amount=Sum("amount"),transaction_count=Count("id")).order_by("method")
        return Response([{**row,"method_name":labels.get(row["method"],row["method"])} for row in rows])

    @action(detail=False, methods=["get"])
    def cancellations(self, request):
        rows=Order.objects.filter(store_id__in=user_store_ids(request.user),status="cancelled").select_related("store","cancellation__cancelled_by").order_by("-updated_at")
        store_id=request.query_params.get("store")
        if store_id: rows=rows.filter(store_id=store_id)
        start_date=request.query_params.get("start_date"); end_date=request.query_params.get("end_date")
        if start_date: rows=rows.filter(updated_at__date__gte=start_date)
        if end_date: rows=rows.filter(updated_at__date__lte=end_date)
        data=[]
        for o in rows[:100]:
            c=getattr(o,"cancellation",None)
            data.append({"order_id":o.id,"store":o.store.name,"cancelled_by":c.cancelled_by.username if c else None,"cancelled_at":c.cancelled_at if c else o.updated_at,"reason":c.reason if c else "","amount":o.total_price})
        return Response(data)

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        from django.http import HttpResponse
        rows = self._orders(request, False).select_related("store", "customer").order_by("created_at")
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="sales-report.csv"'
        response.write("شناسه,تاریخ,فروشگاه,مشتری,مبلغ\n")
        for order in rows:
            response.write(f"{order.id},{order.created_at:%Y-%m-%d %H:%M},{order.store.name},{order.customer or ''},{order.total_price}\n")
        return response

    @action(detail=False, methods=["get"], url_path="cash-reconciliation")
    def cash_reconciliation(self, request):
        store_id=request.query_params.get("store")
        allowed_store_ids = user_store_ids(request.user)
        if not any(has_store_access(request.user, sid, {"manager", "cashier"}) for sid in allowed_store_ids):
            raise PermissionDenied("مشاهده گزارش مغایرت صندوق فقط برای مدیر یا صندوقدار مجاز است.")
        if store_id and not has_store_access(request.user, store_id, {"manager", "cashier"}):
            raise PermissionDenied("شما مجوز مشاهده صندوق این فروشگاه را ندارید.")
        cashboxes=CashBox.objects.filter(store_id__in=user_store_ids(request.user)).select_related("store")
        if store_id: cashboxes=cashboxes.filter(store_id=store_id)
        data=[]
        for cb in cashboxes:
            agg=cb.transactions.aggregate(received=Coalesce(Sum("amount",filter=Q(transaction_type__in=["receive","deposit"])),Decimal("0")),paid=Coalesce(Sum("amount",filter=Q(transaction_type__in=["payment","withdraw"])),Decimal("0")))
            ledger=agg["received"]-agg["paid"]
            data.append({"id":cb.id,"name":cb.name,"store":cb.store.name,"balance":cb.balance,"ledger_balance":ledger,"difference":cb.balance-ledger,"is_balanced":cb.balance==ledger})
        return Response(data)

class DashboardView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        today = timezone.localdate()
        allowed_store_ids = set(user_store_ids(request.user))

        store_id = request.query_params.get("store")
        if store_id:
            try:
                selected_store_id = int(store_id)
            except (TypeError, ValueError):
                raise ValidationError({"store": "شناسه فروشگاه نامعتبر است."})
            if selected_store_id not in allowed_store_ids:
                raise PermissionDenied("شما به این فروشگاه دسترسی ندارید.")
            store_ids = {selected_store_id}
        else:
            store_ids = allowed_store_ids

        today_orders = (
            Order.objects
            .filter(store_id__in=store_ids, created_at__date=today)
            .exclude(status="cancelled")
        )
        month_orders = (
            Order.objects
            .filter(
                store_id__in=store_ids,
                created_at__year=today.year,
                created_at__month=today.month,
            )
            .exclude(status="cancelled")
        )

        today_sales = today_orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")
        month_sales = month_orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

        total_products = Product.objects.filter(category__store_id__in=store_ids).count()
        total_inventory = (
            Inventory.objects.filter(store_id__in=store_ids)
            .aggregate(total=Sum("quantity"))["total"]
            or Decimal("0.00")
        )
        low_stock_products = Inventory.objects.filter(
            store_id__in=store_ids,
            quantity__lte=F("min_quantity"),
        ).count()

        month_items = (
            OrderItem.objects
            .filter(order__in=month_orders)
            .select_related("product")
        )
        month_cost = sum(
            (item.quantity * item.purchase_price for item in month_items),
            Decimal("0.00"),
        )
        gross_profit = month_sales - month_cost

        expense_total = (
            Expense.objects
            .filter(
                store_id__in=store_ids,
                expense_date__year=today.year,
                expense_date__month=today.month,
            )
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        return Response({
            "today_orders": today_orders.count(),
            "month_orders": month_orders.count(),
            "today_sales": today_sales,
            "month_sales": month_sales,
            "total_products": total_products,
            "total_inventory": total_inventory,
            "low_stock_products": low_stock_products,
            "total_profit": gross_profit,
            "expense_total": expense_total,
            "net_profit": gross_profit - expense_total,
        })

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
        audit(user=self.request.user, action="create", model_name="Expense", object_id=expense.id, store=expense.store, description=f"ثبت هزینه: {expense.title}", metadata={"amount": str(expense.amount)})
        
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
        queryset = Customer.objects.filter(
            store_id__in=user_store_ids(self.request.user)
        )
        store_id = self.request.query_params.get("store")
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        return queryset
        
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
        queryset = CashBox.objects.filter(
            store_id__in=user_store_ids(self.request.user)
        ).select_related("store")
        store_id = self.request.query_params.get("store")
        if store_id:
            queryset = queryset.filter(store_id=store_id)
        return queryset.order_by("name")


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

        cashbox.save(update_fields=["balance", "updated_at"])
        audit(user=self.request.user, action="payment" if transaction_type in {"payment", "withdraw"} else "create", model_name="CashBoxTransaction", object_id=transaction_obj.id, store=cashbox.store, description=f"تراکنش صندوق {cashbox.name}", metadata={"type": transaction_type, "amount": str(amount)})
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
        audit(user=self.request.user, action="payment", model_name="CashTransfer", object_id=transfer.id, store=from_cashbox.store, description=f"انتقال {amount} از {from_cashbox.name} به {to_cashbox.name}", metadata={"amount": str(amount)})
        

class CashDayCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = CashDayClose.objects.filter(store_id__in=user_store_ids(request.user)).select_related("cashbox", "store", "closed_by")
        store = request.query_params.get("store")
        if store: qs = qs.filter(store_id=store)
        return Response([{
            "id": x.id, "store": x.store.name, "cashbox": x.cashbox.name, "close_date": x.close_date,
            "opening_balance": x.opening_balance, "expected_balance": x.expected_balance,
            "counted_balance": x.counted_balance, "difference": x.difference, "closed_by": x.closed_by.username,
        } for x in qs[:100]])

    @transaction.atomic
    def post(self, request):
        store_id = request.data.get("store")
        cashbox_id = request.data.get("cashbox")
        close_date = request.data.get("close_date") or timezone.localdate()
        counted = Decimal(str(request.data.get("counted_balance", "0")))
        if not store_id or not cashbox_id: raise ValidationError("فروشگاه و صندوق الزامی است.")
        if not has_store_access(request.user, store_id, {"manager", "cashier"}): raise PermissionDenied("شما مجوز بستن صندوق را ندارید.")
        cashbox = get_object_or_404(CashBox, id=cashbox_id, store_id=store_id)
        if CashDayClose.objects.filter(cashbox=cashbox, close_date=close_date).exists(): raise ValidationError("این صندوق برای این روز قبلاً بسته شده است.")
        tx = cashbox.transactions.filter(created_at__date=close_date)
        net = tx.filter(transaction_type__in=["receive", "deposit"]).aggregate(v=Sum("amount"))["v"] or Decimal("0")
        out = tx.filter(transaction_type__in=["payment", "withdraw"]).aggregate(v=Sum("amount"))["v"] or Decimal("0")
        expected = cashbox.balance
        opening = expected - net + out
        obj = CashDayClose.objects.create(store=cashbox.store, cashbox=cashbox, close_date=close_date, opening_balance=opening, expected_balance=expected, counted_balance=counted, difference=counted-expected, note=request.data.get("note", ""), closed_by=request.user)
        audit(user=request.user, action="close", model_name="CashDayClose", object_id=obj.id, store=cashbox.store, description=f"بستن صندوق {cashbox.name} در تاریخ {close_date}", metadata={"expected": str(expected), "counted": str(counted), "difference": str(obj.difference)})
        return Response({"id": obj.id, "difference": obj.difference, "expected_balance": obj.expected_balance, "counted_balance": obj.counted_balance}, status=status.HTTP_201_CREATED)


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
                "items",
                "payments",
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

        