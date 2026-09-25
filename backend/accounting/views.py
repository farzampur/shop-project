from datetime import datetime

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from accounts.store_access import user_store_ids
from .models import Account, AccountingPeriod, JournalEntry
from .permissions import AccountingManagerPermission
from .serializers import AccountSerializer, AccountingPeriodSerializer, JournalEntrySerializer
from .services import (
    assert_store_for_user,
    balance_sheet,
    create_entry,
    ensure_store_setup,
    general_ledger,
    profit_loss,
    reverse_entry,
    trial_balance,
    sync_store,
)


def _date(value, field):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError({field: "فرمت تاریخ باید YYYY-MM-DD باشد."})


class AccountingBaseMixin:
    permission_classes = [IsAuthenticated, AccountingManagerPermission]

    def store_from_request(self):
        return assert_store_for_user(self.request.user, self.request.query_params.get("store") or self.request.data.get("store"))

    def scoped_store_ids(self):
        return user_store_ids(self.request.user)


class AccountViewSet(AccountingBaseMixin, viewsets.ModelViewSet):
    serializer_class = AccountSerializer

    def get_queryset(self):
        store = self.request.query_params.get("store")
        qs = Account.objects.filter(store_id__in=self.scoped_store_ids()).select_related("parent")
        if store:
            assert_store_for_user(self.request.user, store)
            qs = qs.filter(store_id=int(store))
        return qs

    def perform_create(self, serializer):
        store = assert_store_for_user(self.request.user, serializer.validated_data.get("store"), {"manager"})
        serializer.save(store=store)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.is_system:
            allowed = {"name", "is_active"}
            if set(serializer.validated_data) - allowed:
                raise ValidationError("حساب سیستمی را نمی‌توان از نظر ساختار تغییر داد.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.is_system:
            raise ValidationError("حساب سیستمی قابل حذف نیست؛ در صورت نیاز آن را غیرفعال کنید.")
        if instance.children.exists() or instance.journal_lines.exists():
            raise ValidationError("حسابی که سابقه یا زیرحساب دارد قابل حذف نیست.")
        instance.delete()


class AccountingPeriodViewSet(AccountingBaseMixin, viewsets.ModelViewSet):
    serializer_class = AccountingPeriodSerializer

    def get_queryset(self):
        qs = AccountingPeriod.objects.filter(store_id__in=self.scoped_store_ids()).select_related("store", "closed_by")
        store = self.request.query_params.get("store")
        if store:
            assert_store_for_user(self.request.user, store)
            qs = qs.filter(store_id=int(store))
        return qs

    def perform_create(self, serializer):
        store = assert_store_for_user(self.request.user, serializer.validated_data.get("store"), {"manager"})
        serializer.save(store=store)

    def update(self, request, *args, **kwargs):
        if self.get_object().is_closed:
            raise ValidationError("دوره مالی بسته قابل ویرایش نیست.")
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if instance.entries.exists():
            raise ValidationError("دوره مالی دارای سند است و قابل حذف نیست.")
        if instance.is_closed:
            raise ValidationError("دوره مالی بسته قابل حذف نیست.")
        instance.delete()

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        period = self.get_object()
        if period.is_closed:
            raise ValidationError("این دوره مالی قبلاً بسته شده است.")
        with transaction.atomic():
            period.is_closed = True
            period.closed_by = request.user
            period.closed_at = __import__("django.utils.timezone", fromlist=["now"]).now()
            period.save(update_fields=["is_closed", "closed_by", "closed_at"])
        return Response(self.get_serializer(period).data)


class JournalEntryViewSet(AccountingBaseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = JournalEntrySerializer

    def get_queryset(self):
        qs = JournalEntry.objects.filter(store_id__in=self.scoped_store_ids()).select_related("store", "period", "created_by").prefetch_related("lines__account")
        store = self.request.query_params.get("store")
        if store:
            assert_store_for_user(self.request.user, store)
            qs = qs.filter(store_id=int(store))
        start = _date(self.request.query_params.get("start_date"), "start_date")
        end = _date(self.request.query_params.get("end_date"), "end_date")
        if start:
            qs = qs.filter(entry_date__gte=start)
        if end:
            qs = qs.filter(entry_date__lte=end)
        return qs

    @action(detail=False, methods=["post"], url_path="create")
    def create_entry(self, request):
        serializer = JournalEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = assert_store_for_user(request.user, serializer.validated_data["store"].id, {"manager"})
        lines = [dict(item) for item in serializer.validated_data["lines"]]
        entry, _ = create_entry(
            user=request.user,
            store=store,
            entry_date=serializer.validated_data["entry_date"],
            description=serializer.validated_data["description"],
            lines=lines,
        )
        return Response(self.get_serializer(entry).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        entry = self.get_object()
        reversal = reverse_entry(user=request.user, entry=entry)
        return Response(self.get_serializer(reversal).data, status=status.HTTP_201_CREATED)


class AccountingSetupView(APIView):
    permission_classes = [IsAuthenticated, AccountingManagerPermission]

    def post(self, request):
        store = assert_store_for_user(request.user, request.data.get("store"), {"manager"})
        ensure_store_setup(store)
        return Response({"store": store.id, "status": "ready"})


class AccountingSyncView(APIView):
    permission_classes = [IsAuthenticated, AccountingManagerPermission]

    def post(self, request):
        store = assert_store_for_user(request.user, request.data.get("store"), {"manager"})
        ensure_store_setup(store)
        sync_store(store)
        return Response({"store": store.id, "status": "synchronized"})


class TrialBalanceView(APIView):
    permission_classes = [IsAuthenticated, AccountingManagerPermission]

    def get(self, request):
        store = assert_store_for_user(request.user, request.query_params.get("store"), {"manager"})
        ensure_store_setup(store)
        return Response(trial_balance(store, _date(request.query_params.get("start_date"), "start_date"), _date(request.query_params.get("end_date"), "end_date")))


class GeneralLedgerView(APIView):
    permission_classes = [IsAuthenticated, AccountingManagerPermission]

    def get(self, request):
        store = assert_store_for_user(request.user, request.query_params.get("store"), {"manager"})
        account = None
        account_id = request.query_params.get("account")
        if account_id:
            account = Account.objects.filter(pk=account_id, store=store).first()
            if not account:
                raise ValidationError({"account": "حساب متعلق به این فروشگاه پیدا نشد."})
        return Response(general_ledger(store, account, _date(request.query_params.get("start_date"), "start_date"), _date(request.query_params.get("end_date"), "end_date")))


class ProfitLossView(APIView):
    permission_classes = [IsAuthenticated, AccountingManagerPermission]

    def get(self, request):
        store = assert_store_for_user(request.user, request.query_params.get("store"), {"manager"})
        return Response(profit_loss(store, _date(request.query_params.get("start_date"), "start_date"), _date(request.query_params.get("end_date"), "end_date")))


class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticated, AccountingManagerPermission]

    def get(self, request):
        store = assert_store_for_user(request.user, request.query_params.get("store"), {"manager"})
        return Response(balance_sheet(store, _date(request.query_params.get("as_of_date"), "as_of_date")))
