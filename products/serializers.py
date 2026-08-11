from rest_framework import serializers

from .models import Category, Product, Inventory


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