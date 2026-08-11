from rest_framework import serializers

from .models import UserStore


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
            "created_at",
            "username",
            "store_name",
            "role_display",
        ]