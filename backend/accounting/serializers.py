from rest_framework import serializers

from core.serializers import JalaliDateTimeField
from .models import Account, AccountingPeriod, JournalEntry, JournalLine


class AccountSerializer(serializers.ModelSerializer):
    account_type_label = serializers.CharField(source="get_account_type_display", read_only=True)

    class Meta:
        model = Account
        fields = ["id", "store", "parent", "code", "name", "account_type", "account_type_label", "is_group", "is_system", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_system", "created_at", "updated_at", "account_type_label"]

    def validate(self, attrs):
        store = attrs.get("store") or getattr(self.instance, "store", None)
        if self.instance and "store" in attrs and attrs["store"].id != self.instance.store_id:
            raise serializers.ValidationError("فروشگاه حساب پس از ایجاد قابل تغییر نیست.")
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        if parent and store and parent.store_id != store.id:
            raise serializers.ValidationError("حساب مادر باید متعلق به همین فروشگاه باشد.")
        if parent and not parent.is_group:
            raise serializers.ValidationError("حساب مادر باید یک حساب گروهی باشد.")
        return attrs


class AccountingPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingPeriod
        fields = ["id", "store", "name", "start_date", "end_date", "is_closed", "created_at", "closed_at", "closed_by"]
        read_only_fields = ["id", "is_closed", "created_at", "closed_at", "closed_by"]

    def validate(self, attrs):
        if self.instance and "store" in attrs and attrs["store"].id != self.instance.store_id:
            raise serializers.ValidationError("فروشگاه دوره مالی پس از ایجاد قابل تغییر نیست.")
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError("تاریخ شروع دوره نمی‌تواند بعد از تاریخ پایان باشد.")
        store = attrs.get("store") or getattr(self.instance, "store", None)
        if store:
            overlapping = AccountingPeriod.objects.filter(
                store=store,
                start_date__lte=attrs["end_date"],
                end_date__gte=attrs["start_date"],
            )
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError("بازه این دوره مالی با یک دوره دیگر همپوشانی دارد.")
        return attrs


class JournalLineInputSerializer(serializers.Serializer):
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    debit = serializers.DecimalField(max_digits=18, decimal_places=2, default="0")
    credit = serializers.DecimalField(max_digits=18, decimal_places=2, default="0")
    description = serializers.CharField(required=False, allow_blank=True)
    party_type = serializers.ChoiceField(choices=JournalLine.PARTY_CHOICES, required=False, allow_blank=True)
    party_id = serializers.IntegerField(required=False, allow_null=True)


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineInputSerializer(many=True, write_only=True)
    line_items = serializers.SerializerMethodField(read_only=True)
    created_at = JalaliDateTimeField(read_only=True)

    class Meta:
        model = JournalEntry
        fields = ["id", "store", "period", "entry_number", "entry_date", "description", "status", "source_type", "source_id", "source_key", "reversal_of", "created_by", "created_at", "lines", "line_items"]
        read_only_fields = ["id", "period", "entry_number", "status", "source_type", "source_id", "source_key", "reversal_of", "created_by", "created_at", "line_items"]

    def get_line_items(self, obj):
        return [
            {
                "id": line.id,
                "account": line.account_id,
                "account_code": line.account.code,
                "account_name": line.account.name,
                "debit": line.debit,
                "credit": line.credit,
                "description": line.description,
                "party_type": line.party_type,
                "party_id": line.party_id,
            }
            for line in obj.lines.select_related("account").all()
        ]
