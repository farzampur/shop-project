from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from accounts.models import UserStore

from .models import Cart, CartItem

from .models import Order, OrderItem

from .serializers import (
    CartSerializer,
    CartItemSerializer,
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CheckoutSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)

from .services import CheckoutService
from .services import OrderService


from .permissions import (
    CartPermission,
    get_user_max_discount,
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


        