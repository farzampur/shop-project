from rest_framework import serializers

from .models import Cart, CartItem, Order, OrderItem, Product
from .models import Expense, Customer, CustomerTransaction
from .models import CashBox, CashBoxTransaction, CashTransfer

from core.fields import JalaliDateTimeField

class CartItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    discount_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    final_unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    total_price_before_discount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    total_discount_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    created_at = JalaliDateTimeField(
        with_time=True
    ) 
    updated_at = JalaliDateTimeField(
        with_time=True
    )    
    
    class Meta:
        model = CartItem

        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "discount_percent",
            "discount_amount",
            "final_unit_price",
            "total_price_before_discount",
            "total_discount_amount",
            "total_price",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "discount_amount",
            "final_unit_price",
            "total_price_before_discount",
            "total_discount_amount",
            "total_price",
            "created_at",
            "updated_at",
        ]


class CartSerializer(serializers.ModelSerializer):

    items = CartItemSerializer(
        many=True,
        read_only=True
    )

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    total_before_discount = serializers.SerializerMethodField()

    total_discount = serializers.SerializerMethodField()

    total_price = serializers.SerializerMethodField()

    created_at = JalaliDateTimeField(
        with_time=True
    )
    updated_at = JalaliDateTimeField(
        with_time=True
    )    
        
    class Meta:
        model = Cart
        

        
        fields = [
            "id",
            "user",
            "username",
            "store",
            "store_name",
            "items",
            "total_before_discount",
            "total_discount",
            "total_price",
            "created_at",
            "updated_at",
            "customer",
        ]

        read_only_fields = [
            "id",
            "user",
            "username",
            "store_name",
            "items",
            "total_before_discount",
            "total_discount",
            "total_price",
            "created_at",
            "updated_at",
        ]

    def get_total_before_discount(self, obj):
        return sum(
            item.total_price_before_discount
            for item in obj.items.all()
        )

    def get_total_discount(self, obj):
        return sum(
            item.total_discount_amount
            for item in obj.items.all()
        )

    def get_total_price(self, obj):
        return sum(
            item.total_price
            for item in obj.items.all()
        )
        
        
        
class CartItemCreateSerializer(
    serializers.ModelSerializer
):

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(
            is_active=True
        ),
        required=False,
        allow_null=True,
    )

    barcode = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = CartItem

        fields = [
            "product",
            "barcode",
            "quantity",
            "discount_percent",
        ]

        extra_kwargs = {
            "quantity": {
                "min_value": 0.001
            },
            "discount_percent": {
                "min_value": 0,
                "max_value": 100
            }
        }

    def validate(self, attrs):

        product = attrs.get(
            "product"
        )

        barcode = attrs.get(
            "barcode"
        )

        if not product and not barcode:
            raise serializers.ValidationError(
                {
                    "detail":
                        "product یا barcode را ارسال کنید."
                }
            )

        if product and barcode:
            raise serializers.ValidationError(
                {
                    "detail":
                        "product و barcode را همزمان ارسال نکنید."
                }
            )

        return attrs
        


class CartItemUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CartItem

        fields = [
            "quantity",
            "discount_percent",
        ]

        extra_kwargs = {
            "quantity": {
                "min_value": 0.001
            },
            "discount_percent": {
                "min_value": 0,
                "max_value": 100
            }
        }


        
class CheckoutSerializer(serializers.Serializer):
    cart_id = serializers.IntegerField()


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem

        fields = [
            "id",
            "product_id",
            "product_name",
            "quantity",
            "unit_price",
            "discount_percent",
            "total_price",
        ]


class OrderSerializer(serializers.ModelSerializer):

    created_at = JalaliDateTimeField(
        with_time=True
    )
    
    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order

        fields = [
            "id",
            "status",
            "total_before_discount",
            "total_discount",
            "total_price",
            "created_at",
            "items",
            "customer",
            "customer_name",
        ]
        
    customer_name = serializers.SerializerMethodField()

    def get_customer_name(
        self,
        obj
    ):

        if obj.customer:
            return str(obj.customer)

        return None

        
class OrderStatusSerializer(serializers.Serializer):

    status = serializers.ChoiceField(
        choices=[
            "confirmed",
            "cancelled",
            "delivered",
        ]
    )        
    
class ExpenseSerializer(
    serializers.ModelSerializer
):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )
    
    created_at = JalaliDateTimeField(
            with_time=True
    )
    
    class Meta:
        model = Expense

        fields = [
            "id",
            "store",
            "cashbox",
            "store_name",
            "user",
            "username",
            "expense_type",
            "title",
            "amount",
            "description",
            "expense_date",
            "created_at",
        ]

        read_only_fields = [
            "user",
            "username",
            "store_name",
            "created_at",
        ]

        
        
class CustomerSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = Customer

        fields = "__all__"


class CustomerTransactionSerializer(
    serializers.ModelSerializer
):

    created_at = JalaliDateTimeField(
        with_time=True
    )
    
    class Meta:

        model = CustomerTransaction

        fields = [
            "id",
            "customer",
            "transaction_type",
            "amount",
            "description",
            "reference_id",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


class CashBoxSerializer(
    serializers.ModelSerializer
):

    created_at = JalaliDateTimeField(
        with_time=True
    )
    
    class Meta:

        model = CashBox

        fields = [
            "id",
            "name",
            "store",
            "balance",
            "description",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "balance",
            "created_at",
        ]


class CashBoxTransactionSerializer(
    serializers.ModelSerializer
):

    created_at = JalaliDateTimeField(
        with_time=True
    )
    
    class Meta:

        model = CashBoxTransaction

        fields = [
            "id",
            "cashbox",
            "transaction_type",
            "amount",
            "description",
            "reference_id",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

class CashTransferSerializer(
    serializers.ModelSerializer
):

    created_at = JalaliDateTimeField(
        with_time=True
    )
    
    class Meta:

        model = CashTransfer

        fields = "__all__"

        read_only_fields = [
            "created_by",
            "created_at",
        ]
        
        