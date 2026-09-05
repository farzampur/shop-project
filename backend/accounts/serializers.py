from rest_framework import serializers

from django.contrib.auth.models import User

from .models import UserStore
from core.models import Store
from core.serializers import StoreSerializer


class UserStoreSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    store_name = serializers.CharField(
        source="store.name",
        read_only=True
    )

    role_display = serializers.CharField(
        source="get_role_display",
        read_only=True
    )

    class Meta:
        model = UserStore

        fields = [
            "id",
            "user",
            "username",
            "store",
            "store_name",
            "role",
            "role_display",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "store",
            "created_at",
            "username",
            "store_name",
            "role_display",
        ]
        
        
        
        
class StoreUserCreateSerializer(serializers.Serializer):

    username = serializers.CharField(
        max_length=150
    )

    password = serializers.CharField(
        write_only=True,
        min_length=6
    )

    role = serializers.ChoiceField(
        choices=UserStore.ROLE_CHOICES
    )

    store = serializers.PrimaryKeyRelatedField(
        queryset=Store.objects.all()
    )

    def validate_store(self, store):

        request = self.context.get("request")

        if request is None:
            raise serializers.ValidationError(
                "Request در Serializer وجود ندارد."
            )

     #   if request.user.is_superuser:
     #       return store

        is_manager = UserStore.objects.filter(
            user=request.user,
            store=store,
            role="manager"
        ).exists()

        if not is_manager:
            raise serializers.ValidationError(
                "شما مدیر این فروشگاه نیستید."
            )

        return store

    def validate_username(self, value):

        if User.objects.filter(
            username=value
        ).exists():

            raise serializers.ValidationError(
                "این نام کاربری قبلاً استفاده شده است."
            )

        return value

    def create(self, validated_data):

        password = validated_data.pop("password")
        role = validated_data.pop("role")
        store = validated_data.pop("store")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        UserStore.objects.create(
            user=user,
            store=store,
            role=role
        )

        return user

class MeSerializer(serializers.ModelSerializer):
    stores = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_superuser",
            "stores",
        ]

    def get_stores(self, user):
        rows = (
            UserStore.objects
            .filter(user=user, store__is_active=True)
            .select_related("store")
            .order_by("store__name")
        )
        result = []
        for row in rows:
            data = StoreSerializer(row.store).data
            data["role"] = row.role
            data["role_display"] = row.get_role_display()
            result.append(data)
        return result
