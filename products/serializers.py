from rest_framework import serializers

from .models import Category, Product, Inventory, InventoryTransaction, Supplier, Purchase, PurchaseItem


class CategorySerializer(serializers.ModelSerializer):

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
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


class InventorySerializer(serializers.ModelSerializer):

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

    class Meta:
        model = Supplier

        fields = "__all__"        
        

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
            "total_price"
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
        many=True,
        read_only=True
    )

    received = serializers.BooleanField(
        read_only=True
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
        ]

        read_only_fields = [
            "user",
            "total_amount",
            "created_at",
        ]
        
        
        