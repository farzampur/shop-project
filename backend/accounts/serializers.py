from django.contrib.auth.models import User
from rest_framework import serializers

from .models import UserStore
from core.models import Store
from core.serializers import StoreSerializer


class UserStoreSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = UserStore
        fields = ["id", "user", "username", "first_name", "last_name", "email", "store", "store_name", "role", "role_display", "is_active", "created_at"]
        read_only_fields = ["id", "user", "username", "first_name", "last_name", "email", "store", "store_name", "role_display", "created_at"]

    def update(self, instance, validated_data):
        if "is_active" in validated_data:
            instance.is_active = validated_data["is_active"]
        if "role" in validated_data:
            instance.role = validated_data["role"]
        instance.save(update_fields=["is_active", "role"])
        return instance


class StoreUserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserStore.ROLE_CHOICES)
    store = serializers.PrimaryKeyRelatedField(queryset=Store.objects.all())

    def validate_store(self, store):
        request = self.context.get("request")
        if request is None:
            raise serializers.ValidationError("Request در Serializer وجود ندارد.")
        if request.user.is_superuser:
            if not store.is_active:
                raise serializers.ValidationError("فروشگاه انتخاب‌شده غیرفعال است.")
            return store
        if not UserStore.objects.filter(user=request.user, store=store, role="manager", is_active=True).exists():
            raise serializers.ValidationError("شما مدیر این فروشگاه نیستید.")
        if not store.is_active:
            raise serializers.ValidationError("این فروشگاه غیرفعال است.")
        return store

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً استفاده شده است.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role")
        store = validated_data.pop("store")
        user = User.objects.create_user(password=password, **validated_data)
        UserStore.objects.create(user=user, store=store, role=role)
        return user


class MeSerializer(serializers.ModelSerializer):
    stores = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_staff", "is_superuser", "stores"]

    def get_stores(self, user):
        if user.is_superuser:
            return [
                {**StoreSerializer(store).data, "role": "manager", "role_display": "مدیر"}
                for store in Store.objects.filter(is_active=True).order_by("name")
            ]
        rows = UserStore.objects.filter(user=user, store__is_active=True, is_active=True).select_related("store").order_by("store__name")
        result = []
        for row in rows:
            data = StoreSerializer(row.store).data
            data["role"] = row.role
            data["role_display"] = row.get_role_display()
            result.append(data)
        return result
