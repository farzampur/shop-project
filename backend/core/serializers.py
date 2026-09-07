from rest_framework import serializers
from .models import Store, AuditLog
from .fields import JalaliDateTimeField


class StoreSerializer(serializers.ModelSerializer):
    manager_username = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = ["id", "name", "code", "phone", "address", "is_active", "created_at", "updated_at", "manager_username"]
        read_only_fields = ["id", "created_at", "updated_at", "manager_username"]

    def get_manager_username(self, obj):
        from accounts.models import UserStore
        row = UserStore.objects.filter(store=obj, role="manager", is_active=True).select_related("user").order_by("id").first()
        return row.user.username if row else None

    def validate_code(self, value):
        return value.strip().upper()


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    action_label = serializers.CharField(source="get_action_display", read_only=True)
    created_at = JalaliDateTimeField(with_time=True, read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "username", "store", "store_name", "action", "action_label", "model_name", "object_id", "description", "metadata", "created_at"]
        read_only_fields = fields
