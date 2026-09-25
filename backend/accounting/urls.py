from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    AccountingPeriodViewSet,
    JournalEntryViewSet,
    AccountingSetupView,
    AccountingSyncView,
    TrialBalanceView,
    GeneralLedgerView,
    ProfitLossView,
    BalanceSheetView,
)

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="accounting-account")
router.register(r"periods", AccountingPeriodViewSet, basename="accounting-period")
router.register(r"entries", JournalEntryViewSet, basename="accounting-entry")

urlpatterns = [
    path("setup/", AccountingSetupView.as_view(), name="accounting-setup"),
    path("sync/", AccountingSyncView.as_view(), name="accounting-sync"),
    path("trial-balance/", TrialBalanceView.as_view(), name="accounting-trial-balance"),
    path("general-ledger/", GeneralLedgerView.as_view(), name="accounting-general-ledger"),
    path("profit-loss/", ProfitLossView.as_view(), name="accounting-profit-loss"),
    path("balance-sheet/", BalanceSheetView.as_view(), name="accounting-balance-sheet"),
    path("", include(router.urls)),
]
