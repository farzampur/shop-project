from rest_framework import serializers
from django.db import transaction

from core.fields import (
    JalaliDateTimeField,
)
from .models import Category, Product, Inventory, InventoryTransaction, Supplier, Purchase, PurchaseReturn, PurchaseItem, SupplierTransaction

from .services import (
    generate_ean13,
    is_valid_ean13,
)

class CategorySerializer(serializers.ModelSerializer):

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )
    created_at = JalaliDateTimeField(
    with_time=True
)
    class Meta:
        model = Category

        fields = [
            "id",
            "name",
            "store",
            "store_name",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "store_name",
        ]


class ProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    store_name = serializers.CharField(
        source="category.store.name",
        read_only=True
    )
    barcode = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    created_at = JalaliDateTimeField(
        with_time=True
    )

    updated_at = JalaliDateTimeField(
        with_time=True
    )
    
    class Meta:
        model = Product

        fields = [
            "id",
            "name",
            "barcode",
            "category",
            "category_name",
            "store_name",
            "unit",
            "purchase_price",
            "sale_price",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "category_name",
            "store_name",
        ]


    def to_internal_value(self, data):

        data = data.copy()

        barcode = data.get("barcode")

        if not barcode:
            data["barcode"] = generate_ean13()

        return super().to_internal_value(data)
        
    def validate_barcode(self, value):
        """
        اعتبارسنجی بارکد در صورت ارسال توسط کاربر.
        """

        if value in (
            None,
            ""
        ):
            return value

        value = str(value).strip()

        if not is_valid_ean13(value):
            raise serializers.ValidationError(
                "بارکد باید یک EAN-13 معتبر باشد."
            )

        store_id = None
        if self.instance:
            store_id = self.instance.category.store_id
        else:
            category = self.initial_data.get("category")
            if category:
                try:
                    store_id = Category.objects.only("store_id").get(pk=category).store_id
                except Category.DoesNotExist:
                    store_id = None

        queryset = Product.objects.filter(barcode=value)
        if store_id:
            queryset = queryset.filter(category__store_id=store_id)

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "این بارکد قبلاً برای کالای دیگری ثبت شده است."
            )

        return value
        


class InventorySerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        store = attrs.get("store", getattr(self.instance, "store", None))
        if product and store and product.category.store_id != store.id:
            raise serializers.ValidationError({"product": "کالا متعلق به این فروشگاه نیست."})
        return attrs

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    barcode = serializers.CharField(
        source="product.barcode",
        read_only=True
    )

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )
    
    updated_at = JalaliDateTimeField(
    with_time=True
)
    class Meta:
        model = Inventory

        fields = [
            "id",
            "product",
            "product_name",
            "barcode",
            "store",
            "store_name",
            "quantity",
            "min_quantity",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "barcode",
            "store_name",
            "updated_at",
        ]
        
        
class InventoryTransactionSerializer(
    serializers.ModelSerializer
):

    created_at = JalaliDateTimeField(
        with_time=True
    )

    class Meta:
        model = InventoryTransaction

        fields = [
            "id",
            "transaction_type",
            "quantity",
            "reference_id",
            "description",
            "created_at",
        ]



class InventoryReportSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )

    class Meta:
        model = Inventory

        fields = [
            "id",
            "product",
            "product_name",
            "store",
            "store_name",
            "quantity",
        ]


class SupplierSerializer(
    serializers.ModelSerializer
):

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )

    class Meta:
        model = Supplier

        fields = [
            "id",
            "store",
            "store_name",
            "name",
            "phone",
            "address",
            "description",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]     
        

class PurchaseItemSerializer(
    serializers.ModelSerializer
):

    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    class Meta:

        model = PurchaseItem

        fields = [
            "id",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "total_price",
        ]

        read_only_fields = [
            "id",
            "total_price",
        ]


class PurchaseSerializer(
    serializers.ModelSerializer
):

    supplier_name = serializers.CharField(
        source="supplier.name",
        read_only=True
    )

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )

    items = PurchaseItemSerializer(
        many=True
    )

    received = serializers.BooleanField(
        required=False
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    item_count = serializers.SerializerMethodField()

    created_at = JalaliDateTimeField(
        with_time=True
    )

    class Meta:

        model = Purchase

        fields = [
            "id",
            "supplier",
            "supplier_name",
            "store",
            "store_name",
            "user",
            "invoice_number",
            "total_amount",
            "created_at",
            "items",
            "received",
            "username",
            "item_count",
        ]

        read_only_fields = [
            "id",
            "user",
            "total_amount",
            "created_at",
        ]

    def get_item_count(
        self,
        obj
    ):
        return obj.items.count()

    def validate(
        self,
        attrs
    ):

        store = attrs.get(
            "store",
            getattr(
                self.instance,
                "store",
                None
            )
        )

        supplier = attrs.get(
            "supplier",
            getattr(
                self.instance,
                "supplier",
                None
            )
        )

        items = attrs.get("items")

        # تأمین‌کننده متعلق به فروشگاه باشد
        if (
            store
            and supplier
            and supplier.store_id != store.id
        ):
            raise serializers.ValidationError(
                {
                    "supplier": (
                        "تأمین‌کننده انتخاب‌شده "
                        "متعلق به فروشگاه انتخاب‌شده نیست."
                    )
                }
            )

        # در ایجاد خرید، حداقل یک قلم لازم است
        if items is not None and not items:
            raise serializers.ValidationError(
                {
                    "items": (
                        "حداقل یک قلم خرید "
                        "باید ثبت شود."
                    )
                }
            )

        # تمام محصولات متعلق به فروشگاه باشند
        if store and items:

            for item in items:

                product = item["product"]

                product_store_id = (
                    product.category.store_id
                )

                if (
                    product_store_id
                    != store.id
                ):
                    raise serializers.ValidationError(
                        {
                            "items": (
                                f"محصول «{product.name}» "
                                "متعلق به فروشگاه "
                                "انتخاب‌شده نیست."
                            )
                        }
                    )

        return attrs        

    @transaction.atomic
    def create(
        self,
        validated_data
    ):

        items_data = (
            validated_data.pop(
                "items",
                []
            )
        )

        purchase = Purchase.objects.create(
            **validated_data
        )

        total_amount = 0

        for item_data in items_data:

            quantity = item_data["quantity"]
            unit_price = item_data["unit_price"]

            total_price = (
                quantity
                * unit_price
            )

            PurchaseItem.objects.create(
                purchase=purchase,
                product=item_data["product"],
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )

            total_amount += total_price

        purchase.total_amount = total_amount

        purchase.save(
            update_fields=[
                "total_amount"
            ]
        )

        return purchase
        
        
        
    @transaction.atomic
    def update(
        self,
        instance,
        validated_data
    ):
        """
        ویرایش اتمیک خرید چندقلمی.
        """

        items_data = validated_data.pop(
            "items",
            None
        )

        # ویرایش اطلاعات اصلی خرید
        for attr, value in validated_data.items():
            setattr(
                instance,
                attr,
                value
            )

        instance.save()

        # اگر اقلام ارسال نشده‌اند،
        # فقط اطلاعات اصلی خرید تغییر کرده‌اند
        if items_data is None:
            return instance

        # حذف اقلام قبلی
        instance.items.all().delete()

        total_amount = 0

        # ایجاد اقلام جدید
        for item_data in items_data:

            quantity = item_data["quantity"]

            unit_price = item_data[
                "unit_price"
            ]

            total_price = (
                quantity *
                unit_price
            )

            PurchaseItem.objects.create(
                purchase=instance,
                product=item_data["product"],
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
            )

            total_amount += total_price

        # به‌روزرسانی مبلغ کل
        instance.total_amount = total_amount

        instance.save(
            update_fields=[
                "total_amount",
                "updated_at",
            ]
        )

        return instance        
        
class SupplierTransactionSerializer(
    serializers.ModelSerializer
):
    """
    Serializer تراکنش مالی تأمین‌کننده.
    """
    created_at = JalaliDateTimeField(
    with_time=True
)
    class Meta:

        model = SupplierTransaction

        fields = [
            "id",
            "supplier",
            "transaction_type",
            "amount",
            "reference_id",
            "description",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


class SupplierPaymentSerializer(
    serializers.ModelSerializer
):
    """
    Serializer ثبت پرداخت به تأمین‌کننده.
    """
    created_at = JalaliDateTimeField(
    with_time=True
)
    class Meta:
        model = SupplierTransaction

        fields = [
            "id",
            "supplier",
            "amount",
            "reference_id",
            "description",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "reference_id",
            "created_at",
        ]

    def validate_amount(
        self,
        value
    ):
        """
        جلوگیری از مبلغ صفر یا منفی.
        """

        if value <= 0:
            raise serializers.ValidationError(
                "مبلغ پرداخت باید بیشتر از صفر باشد."
            )

        return value


class PurchaseReturnSerializer(
    serializers.ModelSerializer
):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    supplier_name = serializers.CharField(
        source="purchase.supplier.name",
        read_only=True
    )

    store_name = serializers.CharField(
        source="purchase.store.name",
        read_only=True
    )
    
    created_at = JalaliDateTimeField(
    with_time=True
)
    class Meta:
        model = PurchaseReturn

        fields = [
            "id",
            "purchase",
            "product",
            "product_name",
            "supplier_name",
            "store_name",
            "quantity",
            "unit_price",
            "total_amount",
            "description",
            "created_by",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "product_name",
            "supplier_name",
            "store_name",
            "total_amount",
            "created_by",
            "created_at",
        ]

        