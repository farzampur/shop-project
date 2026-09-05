from rest_framework import serializers
from decimal import Decimal

from .models import Cart, CartItem, Order, OrderItem, Product, Payment
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
            "purchase_price",
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
            "store",
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

    def validate_customer(self, value):
        if self.instance and value and value.store_id != self.instance.store_id:
            raise serializers.ValidationError("مشتری متعلق به فروشگاه این سبد نیست.")
        return value

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


        
class CheckoutPaymentSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=["cash", "card", "credit"])
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal("0.01"))
    cashbox_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        method = attrs["method"]
        cashbox_id = attrs.get("cashbox_id")
        if method in {"cash", "card"} and not cashbox_id:
            raise serializers.ValidationError({"cashbox_id": "برای پرداخت نقدی/کارتخوان صندوق الزامی است."})
        if method == "credit" and cashbox_id:
            raise serializers.ValidationError({"cashbox_id": "برای پرداخت حسابی صندوق ارسال نکنید."})
        return attrs


class CheckoutSerializer(serializers.Serializer):
    cart_id = serializers.IntegerField()
    payments = CheckoutPaymentSerializer(many=True, required=False, allow_empty=True)

    def validate(self, attrs):
        payments = attrs.get("payments", [])
        if any(p["amount"] <= 0 for p in payments):
            raise serializers.ValidationError({"payments": "مبلغ پرداخت باید بیشتر از صفر باشد."})
        return attrs


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


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "method", "amount", "cashbox", "created_at"]
        read_only_fields = ["id", "created_at"]


class OrderSerializer(serializers.ModelSerializer):

    created_at = JalaliDateTimeField(
        with_time=True
    )
    
    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    payments = PaymentSerializer(
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
            "payments",
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
        choices=["confirmed", "cancelled"]
    )


class OrderPaySerializer(serializers.Serializer):
    payments = CheckoutPaymentSerializer(many=True, allow_empty=False)        
    
class ExpenseSerializer(
    serializers.ModelSerializer
):

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("مبلغ هزینه باید بیشتر از صفر باشد.")
        return value

    def validate(self, attrs):
        store = attrs.get("store", getattr(self.instance, "store", None))
        cashbox = attrs.get("cashbox", getattr(self.instance, "cashbox", None))
        if store and cashbox and cashbox.store_id != store.id:
            raise serializers.ValidationError({"cashbox": "صندوق متعلق به فروشگاه انتخاب‌شده نیست."})
        return attrs

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

    def validate_store(self, value):
        if self.instance and value.id != self.instance.store_id:
            raise serializers.ValidationError("انتقال مشتری بین فروشگاه‌ها مجاز نیست.")
        return value

    class Meta:

        model = Customer

        fields = "__all__"


class CustomerTransactionSerializer(
    serializers.ModelSerializer
):

    def validate(self, attrs):
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        store = getattr(self.instance, "store", None)
        amount = attrs.get("amount", getattr(self.instance, "amount", None))
        if amount is not None and amount <= 0:
            raise serializers.ValidationError({"amount": "مبلغ تراکنش باید بیشتر از صفر باشد."})
        if store and customer and customer.store_id != store.id:
            raise serializers.ValidationError({"customer": "مشتری متعلق به فروشگاه این تراکنش نیست."})
        return attrs

    created_at = JalaliDateTimeField(
        with_time=True
    )
    
    class Meta:

        model = CustomerTransaction

        fields = [
            "id",
            "customer",
            "store",
            "transaction_type",
            "amount",
            "description",
            "reference_id",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "store",
            "created_at",
        ]


class CashBoxSerializer(
    serializers.ModelSerializer
):

    def validate_store(self, value):
        if self.instance and value.id != self.instance.store_id:
            raise serializers.ValidationError("انتقال صندوق بین فروشگاه‌ها مجاز نیست.")
        return value

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

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("مبلغ باید بیشتر از صفر باشد.")
        return value

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

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("مبلغ انتقال باید بیشتر از صفر باشد.")
        return value

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
        
        