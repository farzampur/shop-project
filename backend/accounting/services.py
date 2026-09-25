from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied

from accounts.store_access import has_store_access
from core.models import Store
from .models import Account, AccountingPeriod, JournalEntry, JournalLine


D = Decimal

DEFAULT_ACCOUNTS = [
    ("1000", "دارایی‌ها", Account.TYPE_ASSET, None, True),
    ("1100", "صندوق‌ها", Account.TYPE_ASSET, "1000", True),
    ("1200", "بانک و کارتخوان", Account.TYPE_ASSET, "1000", True),
    ("1300", "حساب‌های دریافتنی", Account.TYPE_ASSET, "1000", False),
    ("1400", "موجودی کالا", Account.TYPE_ASSET, "1000", False),
    ("2000", "بدهی‌ها", Account.TYPE_LIABILITY, None, True),
    ("2100", "حساب‌های پرداختنی", Account.TYPE_LIABILITY, "2000", False),
    ("3000", "حقوق مالکانه", Account.TYPE_EQUITY, None, True),
    ("3100", "سرمایه مالک", Account.TYPE_EQUITY, "3000", False),
    ("3200", "تعدیلات سرمایه", Account.TYPE_EQUITY, "3000", False),
    ("4000", "درآمدها", Account.TYPE_REVENUE, None, True),
    ("4100", "فروش کالا", Account.TYPE_REVENUE, "4000", False),
    ("4200", "برگشت از فروش", Account.TYPE_REVENUE, "4000", False),
    ("4300", "تخفیفات فروش", Account.TYPE_REVENUE, "4000", False),
    ("5000", "بهای تمام‌شده", Account.TYPE_EXPENSE, None, True),
    ("5100", "بهای تمام‌شده کالای فروش‌رفته", Account.TYPE_EXPENSE, "5000", False),
    ("6000", "هزینه‌ها", Account.TYPE_EXPENSE, None, True),
    ("6100", "هزینه‌های جاری", Account.TYPE_EXPENSE, "6000", False),
    ("6200", "هزینه‌های متفرقه", Account.TYPE_EXPENSE, "6000", False),
]


def ensure_store_setup(store):
    """Create the frozen baseline chart for one store, idempotently."""
    existing = {a.code: a for a in Account.objects.filter(store=store)}
    created = False
    for code, name, account_type, parent_code, is_group in DEFAULT_ACCOUNTS:
        account = existing.get(code)
        parent = existing.get(parent_code) if parent_code else None
        if account is None:
            account = Account.objects.create(
                store=store,
                code=code,
                name=name,
                account_type=account_type,
                parent=parent,
                is_group=is_group,
                is_system=True,
                is_active=True,
            )
            existing[code] = account
            created = True
    return existing, created


def ensure_cashbox_account(cashbox):
    accounts, _ = ensure_store_setup(cashbox.store)
    parent = accounts["1100"]
    code = f"11{cashbox.id:06d}"
    account, _ = Account.objects.get_or_create(
        store=cashbox.store,
        code=code,
        defaults={
            "parent": parent,
            "name": f"صندوق {cashbox.name}",
            "account_type": Account.TYPE_ASSET,
            "is_group": False,
            "is_system": True,
            "is_active": True,
        },
    )
    return account


def _account(store, code):
    accounts, _ = ensure_store_setup(store)
    return accounts[code]


def ensure_open_period(store, entry_date=None):
    entry_date = entry_date or timezone.localdate()
    period = (
        AccountingPeriod.objects
        .filter(store=store, start_date__lte=entry_date, end_date__gte=entry_date, is_closed=False)
        .order_by("-start_date", "-id")
        .first()
    )
    if period:
        return period
    period = AccountingPeriod.objects.filter(store=store).order_by("-start_date", "-id").first()
    if period and not period.is_closed and period.start_date <= entry_date <= period.end_date:
        return period
    # One annual period around the target date. Existing overlapping periods are respected.
    year = entry_date.year
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    if AccountingPeriod.objects.filter(store=store, start_date__lte=end, end_date__gte=start).exists():
        raise ValidationError("برای تاریخ سند دوره مالی باز مناسبی وجود ندارد.")
    return AccountingPeriod.objects.create(
        store=store,
        name=f"دوره {year}",
        start_date=start,
        end_date=end,
    )


def _next_entry_number(store):
    row = JournalEntry.objects.filter(store=store).order_by("-entry_number").values_list("entry_number", flat=True).first()
    return (row or 0) + 1


def _validate_lines(store, lines):
    if len(lines) < 2:
        raise ValidationError({"lines": "سند حسابداری حداقل باید دو ردیف داشته باشد."})
    total_debit = D("0")
    total_credit = D("0")
    clean = []
    for index, item in enumerate(lines, start=1):
        account_ref = item.get("account")
        account_id = getattr(account_ref, "pk", account_ref)
        if not account_id:
            raise ValidationError({"lines": f"حساب ردیف {index} مشخص نشده است."})
        account = Account.objects.filter(pk=account_id, store=store).first()
        if not account:
            raise ValidationError({"lines": f"حساب ردیف {index} متعلق به این فروشگاه نیست."})
        if account.is_group:
            raise ValidationError({"lines": f"حساب گروهی «{account.name}» قابل ثبت سند نیست."})
        debit = D(str(item.get("debit", "0") or "0"))
        credit = D(str(item.get("credit", "0") or "0"))
        if debit < 0 or credit < 0 or ((debit > 0) == (credit > 0)):
            raise ValidationError({"lines": f"ردیف {index} باید دقیقاً یک مبلغ بدهکار یا بستانکار مثبت داشته باشد."})
        total_debit += debit
        total_credit += credit
        clean.append((account, debit, credit, item.get("description", ""), item.get("party_type", ""), item.get("party_id")))
    if total_debit != total_credit:
        raise ValidationError({"lines": f"سند نامتوازن است. جمع بدهکار {total_debit} و جمع بستانکار {total_credit} است."})
    if total_debit <= 0:
        raise ValidationError({"lines": "مجموع سند باید بیشتر از صفر باشد."})
    return clean


@transaction.atomic
def create_entry(*, user, store, entry_date, description, lines, source_type="", source_id=None, source_key="", period=None):
    if not has_store_access(user, store.id, {"manager"}):
        raise PermissionDenied("ثبت سند حسابداری فقط برای مدیر فروشگاه مجاز است.")
    ensure_store_setup(store)
    store = Store.objects.select_for_update().get(pk=store.pk)
    period = period or ensure_open_period(store, entry_date)
    period = AccountingPeriod.objects.select_for_update().get(pk=period.pk)
    if period.store_id != store.id:
        raise ValidationError("دوره مالی متعلق به این فروشگاه نیست.")
    if period.is_closed:
        raise ValidationError("دوره مالی بسته است و ثبت سند جدید در آن مجاز نیست.")
    if not (period.start_date <= entry_date <= period.end_date):
        raise ValidationError("تاریخ سند خارج از دوره مالی انتخاب‌شده است.")
    if source_key:
        existing = JournalEntry.objects.filter(store=store, source_key=source_key).first()
        if existing:
            return existing, False
    clean_lines = _validate_lines(store, lines)
    entry = JournalEntry.objects.create(
        store=store,
        period=period,
        entry_number=_next_entry_number(store),
        entry_date=entry_date,
        description=description.strip(),
        source_type=source_type,
        source_id=source_id,
        source_key=source_key,
        created_by=user,
    )
    JournalLine.objects.bulk_create([
        JournalLine(
            entry=entry,
            account=account,
            debit=debit,
            credit=credit,
            description=line_description,
            party_type=party_type or "",
            party_id=party_id,
        )
        for account, debit, credit, line_description, party_type, party_id in clean_lines
    ])
    return entry, True


@transaction.atomic
def reverse_entry(*, user, entry):
    original_entry = entry
    if not has_store_access(user, entry.store_id, {"manager"}):
        raise PermissionDenied("فقط مدیر فروشگاه می‌تواند سند را برگشت بزند.")
    entry = JournalEntry.objects.select_for_update().get(pk=entry.pk)
    if entry.status != JournalEntry.STATUS_POSTED:
        raise ValidationError("فقط سندهای ثبت قطعی و برگشت‌نخورده قابل برگشت هستند.")
    if entry.reversal_of_id:
        raise ValidationError("سند برگشت قبلی قابل برگشت مجدد نیست.")
    period = AccountingPeriod.objects.select_for_update().get(pk=entry.period_id)
    if period.is_closed:
        raise ValidationError("دوره مالی بسته است و برگشت سند در آن مجاز نیست.")
    reversal_key = f"reversal:{entry.id}"
    existing = JournalEntry.objects.filter(store=entry.store, source_key=reversal_key).first()
    if existing:
        if existing.reversal_of_id != entry.id:
            existing.reversal_of_id = entry.id
            existing.save(update_fields=["reversal_of"])
        if original_entry.pk == entry.pk:
            original_entry.status = JournalEntry.STATUS_REVERSED
        return existing
    lines = [
        {
            "account": line.account_id,
            "debit": line.credit,
            "credit": line.debit,
            "description": f"برگشت سند {entry.entry_number}",
            "party_type": line.party_type,
            "party_id": line.party_id,
        }
        for line in entry.lines.select_related("account").all()
    ]
    today = timezone.localdate()
    reversal_date = min(max(today, entry.period.start_date), entry.period.end_date)
    reversal, _ = create_entry(
        user=user,
        store=entry.store,
        entry_date=reversal_date,
        description=f"برگشت سند شماره {entry.entry_number}",
        lines=lines,
        source_type="journal-reversal",
        source_id=entry.id,
        source_key=reversal_key,
    )
    if reversal.reversal_of_id != entry.id:
        reversal.reversal_of_id = entry.id
        reversal.save(update_fields=["reversal_of"])
    entry.status = JournalEntry.STATUS_REVERSED
    entry.save(update_fields=["status"])
    if original_entry.pk == entry.pk:
        original_entry.status = JournalEntry.STATUS_REVERSED
    return reversal


def assert_store_for_user(user, store_id, roles={"manager"}):
    if store_id is None:
        raise ValidationError({"store": "فروشگاه الزامی است."})
    try:
        store_id = int(store_id)
    except (TypeError, ValueError):
        raise ValidationError({"store": "شناسه فروشگاه نامعتبر است."})
    if not has_store_access(user, store_id, roles):
        raise PermissionDenied("شما به این فروشگاه دسترسی ندارید.")
    return Store.objects.get(pk=store_id)


def _post_sale(order):
    items = list(order.items.all())
    total_before = D(order.total_before_discount)
    discount = D(order.total_discount)
    net = D(order.total_price)
    sale_lines = []
    for payment in order.payments.select_related("cashbox").all():
        if payment.method in {"cash", "card"} and payment.cashbox_id:
            account = ensure_cashbox_account(payment.cashbox)
            sale_lines.append({"account": account.id, "debit": D(payment.amount), "credit": 0, "party_type": "cashbox", "party_id": payment.cashbox_id, "description": "دریافت فروش"})
        elif payment.method == "credit":
            sale_lines.append({"account": _account(order.store, "1300").id, "debit": D(payment.amount), "credit": 0, "party_type": "customer", "party_id": order.customer_id, "description": "فروش حسابی"})
    # If no payment rows exist, this is not an accounting sale settlement.
    if sale_lines:
        if total_before:
            sale_lines.append({"account": _account(order.store, "4100").id, "debit": 0, "credit": total_before, "description": "فروش کالا"})
        if discount:
            sale_lines.append({"account": _account(order.store, "4300").id, "debit": discount, "credit": 0, "description": "تخفیف فروش"})
        create_entry(
            user=order.user,
            store=order.store,
            entry_date=order.created_at.date(),
            description=f"فروش شماره {order.id}",
            lines=sale_lines,
            source_type="sale-revenue",
            source_id=order.id,
            source_key=f"sale-revenue:{order.id}",
        )
    cost = sum((D(item.quantity) * D(item.purchase_price) for item in items), D("0"))
    if cost > 0:
        create_entry(
            user=order.user,
            store=order.store,
            entry_date=order.created_at.date(),
            description=f"بهای تمام‌شده فروش شماره {order.id}",
            lines=[
                {"account": _account(order.store, "5100").id, "debit": cost, "credit": 0, "description": "بهای تمام‌شده کالای فروش‌رفته"},
                {"account": _account(order.store, "1400").id, "debit": 0, "credit": cost, "description": "کاهش موجودی کالا"},
            ],
            source_type="sale-cogs",
            source_id=order.id,
            source_key=f"sale-cogs:{order.id}",
        )


def _post_purchase(purchase):
    if not purchase.received or D(purchase.total_amount) <= 0:
        return
    # The existing purchase total represents the stock valuation entered on receipt.
    user = purchase.user
    create_entry(
        user=user,
        store=purchase.store,
        entry_date=purchase.updated_at.date(),
        description=f"دریافت خرید شماره {purchase.id}",
        lines=[
            {"account": _account(purchase.store, "1400").id, "debit": D(purchase.total_amount), "credit": 0, "description": "افزایش موجودی کالا"},
            {"account": _account(purchase.store, "2100").id, "debit": 0, "credit": D(purchase.total_amount), "description": "بدهی به تأمین‌کننده", "party_type": "supplier", "party_id": purchase.supplier_id},
        ],
        source_type="purchase",
        source_id=purchase.id,
        source_key=f"purchase:{purchase.id}",
    )


def _post_supplier_transaction(tx):
    from products.models import Purchase
    if tx.transaction_type == "payment":
        # Cashbox transaction is the authoritative cash selection.
        from sales.models import CashBoxTransaction
        cash_tx = CashBoxTransaction.objects.filter(reference_type="supplier_transaction", reference_id=tx.id).select_related("cashbox").first()
        if not cash_tx:
            return
        lines = [
            {"account": _account(tx.supplier.store, "2100").id, "debit": D(tx.amount), "credit": 0, "description": "کاهش بدهی تأمین‌کننده", "party_type": "supplier", "party_id": tx.supplier_id},
            {"account": ensure_cashbox_account(cash_tx.cashbox).id, "debit": 0, "credit": D(tx.amount), "description": "پرداخت به تأمین‌کننده", "party_type": "cashbox", "party_id": cash_tx.cashbox_id},
        ]
        create_entry(user=_actor_for_store(tx.supplier.store), store=tx.supplier.store, entry_date=tx.created_at.date(), description=f"پرداخت به تأمین‌کننده {tx.supplier.name}", lines=lines, source_type="supplier-payment", source_id=tx.id, source_key=f"supplier-payment:{tx.id}")
    elif tx.transaction_type == "return":
        create_entry(user=_actor_for_store(tx.supplier.store), store=tx.supplier.store, entry_date=tx.created_at.date(), description=f"برگشت خرید از {tx.supplier.name}", lines=[
            {"account": _account(tx.supplier.store, "2100").id, "debit": D(tx.amount), "credit": 0, "description": "کاهش بدهی تأمین‌کننده", "party_type": "supplier", "party_id": tx.supplier_id},
            {"account": _account(tx.supplier.store, "1400").id, "debit": 0, "credit": D(tx.amount), "description": "کاهش موجودی کالا"},
        ], source_type="purchase-return", source_id=tx.id, source_key=f"purchase-return:{tx.id}")


def _post_customer_transaction(tx):
    store = tx.store
    actor = _actor_for_store(store)
    if tx.transaction_type == "sale":
        create_entry(user=actor, store=store, entry_date=tx.created_at.date(), description=f"فروش ثبت‌شده برای مشتری {tx.customer}", lines=[
            {"account": _account(store, "1300").id, "debit": D(tx.amount), "credit": 0, "description": "بدهکار شدن مشتری", "party_type": "customer", "party_id": tx.customer_id},
            {"account": _account(store, "4100").id, "debit": 0, "credit": D(tx.amount), "description": "فروش"},
        ], source_type="customer-sale", source_id=tx.id, source_key=f"customer-sale:{tx.id}")
    elif tx.transaction_type == "payment":
        from sales.models import CashBoxTransaction
        cash_tx = CashBoxTransaction.objects.filter(reference_type="customer_transaction", reference_id=tx.id).select_related("cashbox").first()
        if not cash_tx:
            return
        create_entry(user=actor, store=store, entry_date=tx.created_at.date(), description=f"دریافت از مشتری {tx.customer}", lines=[
            {"account": ensure_cashbox_account(cash_tx.cashbox).id, "debit": D(tx.amount), "credit": 0, "description": "دریافت وجه", "party_type": "cashbox", "party_id": cash_tx.cashbox_id},
            {"account": _account(store, "1300").id, "debit": 0, "credit": D(tx.amount), "description": "کاهش بدهی مشتری", "party_type": "customer", "party_id": tx.customer_id},
        ], source_type="customer-payment", source_id=tx.id, source_key=f"customer-payment:{tx.id}")


def _post_expense(expense):
    if D(expense.amount) <= 0:
        return
    create_entry(user=expense.user, store=expense.store, entry_date=expense.expense_date, description=f"هزینه: {expense.title}", lines=[
        {"account": _account(expense.store, "6100").id, "debit": D(expense.amount), "credit": 0, "description": expense.title},
        {"account": ensure_cashbox_account(expense.cashbox).id, "debit": 0, "credit": D(expense.amount), "description": "پرداخت هزینه", "party_type": "cashbox", "party_id": expense.cashbox_id},
    ], source_type="expense", source_id=expense.id, source_key=f"expense:{expense.id}")


def _post_cash_transfer(transfer):
    store = transfer.from_cashbox.store
    create_entry(user=transfer.created_by, store=store, entry_date=transfer.created_at.date(), description="انتقال بین صندوق‌ها", lines=[
        {"account": ensure_cashbox_account(transfer.to_cashbox).id, "debit": D(transfer.amount), "credit": 0, "description": f"ورود از صندوق {transfer.from_cashbox.name}", "party_type": "cashbox", "party_id": transfer.to_cashbox_id},
        {"account": ensure_cashbox_account(transfer.from_cashbox).id, "debit": 0, "credit": D(transfer.amount), "description": f"خروج به صندوق {transfer.to_cashbox.name}", "party_type": "cashbox", "party_id": transfer.from_cashbox_id},
    ], source_type="cash-transfer", source_id=transfer.id, source_key=f"cash-transfer:{transfer.id}")


def _post_manual_cashbox_transaction(tx):
    if tx.reference_type in {"order", "expense", "customer_transaction", "supplier_transaction"}:
        return
    account = _account(tx.cashbox.store, "3200" if tx.transaction_type == "deposit" else "6200")
    if tx.transaction_type == "deposit":
        lines = [
            {"account": ensure_cashbox_account(tx.cashbox).id, "debit": D(tx.amount), "credit": 0, "description": "واریز دستی صندوق", "party_type": "cashbox", "party_id": tx.cashbox_id},
            {"account": account.id, "debit": 0, "credit": D(tx.amount), "description": "تعدیل سرمایه"},
        ]
    else:
        lines = [
            {"account": account.id, "debit": D(tx.amount), "credit": 0, "description": "برداشت/تعدیل صندوق"},
            {"account": ensure_cashbox_account(tx.cashbox).id, "debit": 0, "credit": D(tx.amount), "description": "برداشت دستی صندوق", "party_type": "cashbox", "party_id": tx.cashbox_id},
        ]
    create_entry(user=_actor_for_store(tx.cashbox.store), store=tx.cashbox.store, entry_date=tx.created_at.date(), description=f"تراکنش دستی صندوق {tx.cashbox.name}", lines=lines, source_type="cashbox-transaction", source_id=tx.id, source_key=f"cashbox-tx:{tx.id}")


def _actor_for_store(store):
    from accounts.models import UserStore
    user = UserStore.objects.filter(store=store, role="manager", is_active=True).select_related("user").order_by("id").first()
    if user:
        return user.user
    from django.contrib.auth.models import User
    return User.objects.filter(is_superuser=True).order_by("id").first()


# Public integration functions. They are intentionally callable and idempotent.
def post_sale(order):
    if not order or order.status != "paid":
        return
    return _post_sale(order)


def post_purchase(purchase):
    return _post_purchase(purchase)


def post_supplier_transaction(tx):
    return _post_supplier_transaction(tx)


def post_customer_transaction(tx):
    return _post_customer_transaction(tx)


def post_expense(expense):
    return _post_expense(expense)


def post_cash_transfer(transfer):
    return _post_cash_transfer(transfer)


def post_manual_cashbox_transaction(tx):
    return _post_manual_cashbox_transaction(tx)


def reverse_order_accounting(order):
    for entry in JournalEntry.objects.filter(store=order.store, source_key__in=[f"sale-revenue:{order.id}", f"sale-cogs:{order.id}"], status=JournalEntry.STATUS_POSTED):
        manager = _actor_for_store(order.store)
        if manager:
            reverse_entry(user=manager, entry=entry)


def sync_store(store):
    """Idempotent historical sync for one store."""
    from sales.models import Order, CustomerTransaction, Expense, CashTransfer, CashBoxTransaction
    from products.models import Purchase, SupplierTransaction

    for purchase in Purchase.objects.filter(store=store, received=True).select_related("store", "supplier", "user").order_by("id"):
        _post_purchase(purchase)
    for order in Order.objects.filter(store=store, status="paid").prefetch_related("items", "payments").order_by("id"):
        _post_sale(order)
    for tx in CustomerTransaction.objects.filter(store=store).select_related("customer", "store").order_by("id"):
        if tx.transaction_type in {"sale", "payment"}:
            _post_customer_transaction(tx)
    for tx in SupplierTransaction.objects.filter(supplier__store=store).select_related("supplier", "supplier__store").order_by("id"):
        _post_supplier_transaction(tx)
    for expense in Expense.objects.filter(store=store).select_related("store", "cashbox", "user").order_by("id"):
        _post_expense(expense)
    for transfer in CashTransfer.objects.filter(from_cashbox__store=store).select_related("from_cashbox", "to_cashbox", "created_by").order_by("id"):
        _post_cash_transfer(transfer)
    for tx in CashBoxTransaction.objects.filter(cashbox__store=store).select_related("cashbox").order_by("id"):
        _post_manual_cashbox_transaction(tx)
    for order in Order.objects.filter(store=store, status="cancelled").order_by("id"):
        reverse_order_accounting(order)


def trial_balance(store, start_date=None, end_date=None):
    qs = JournalLine.objects.filter(entry__store=store, entry__status__in=[JournalEntry.STATUS_POSTED, JournalEntry.STATUS_REVERSED])
    if start_date:
        qs = qs.filter(entry__entry_date__gte=start_date)
    if end_date:
        qs = qs.filter(entry__entry_date__lte=end_date)
    qs = qs.values("account_id", "account__code", "account__name", "account__account_type").annotate(debit=Sum("debit"), credit=Sum("credit")).order_by("account__code")
    rows = []
    for row in qs:
        debit = row["debit"] or D("0")
        credit = row["credit"] or D("0")
        rows.append({**row, "debit": debit, "credit": credit, "balance": debit - credit})
    return rows


def general_ledger(store, account=None, start_date=None, end_date=None):
    qs = JournalLine.objects.filter(entry__store=store).select_related("entry", "account")
    if account:
        qs = qs.filter(account=account)
    if start_date:
        qs = qs.filter(entry__entry_date__gte=start_date)
    if end_date:
        qs = qs.filter(entry__entry_date__lte=end_date)
    qs = qs.order_by("entry__entry_date", "entry__entry_number", "id")
    balance = D("0")
    rows = []
    for line in qs:
        if line.account.account_type in {Account.TYPE_ASSET, Account.TYPE_EXPENSE}:
            balance += D(line.debit) - D(line.credit)
        else:
            balance += D(line.credit) - D(line.debit)
        rows.append({
            "entry_id": line.entry_id,
            "entry_number": line.entry.entry_number,
            "date": line.entry.entry_date,
            "description": line.description or line.entry.description,
            "account_id": line.account_id,
            "account_code": line.account.code,
            "account_name": line.account.name,
            "debit": line.debit,
            "credit": line.credit,
            "balance": balance,
        })
    return rows


def profit_loss(store, start_date=None, end_date=None):
    rows = trial_balance(store, start_date, end_date)
    revenue = D("0")
    expense = D("0")
    for row in rows:
        if row["account__account_type"] == Account.TYPE_REVENUE:
            revenue += row["credit"] - row["debit"]
        elif row["account__account_type"] == Account.TYPE_EXPENSE:
            expense += row["debit"] - row["credit"]
    return {"revenue": revenue, "expense": expense, "net_profit": revenue - expense}


def balance_sheet(store, as_of_date=None):
    rows = trial_balance(store, None, as_of_date)
    assets = D("0")
    liabilities = D("0")
    equity = D("0")
    revenue = D("0")
    expense = D("0")
    details = []
    for row in rows:
        typ = row["account__account_type"]
        if typ == Account.TYPE_ASSET:
            value = row["debit"] - row["credit"]
            assets += value
        elif typ == Account.TYPE_LIABILITY:
            value = row["credit"] - row["debit"]
            liabilities += value
        elif typ == Account.TYPE_EQUITY:
            value = row["credit"] - row["debit"]
            equity += value
        elif typ == Account.TYPE_REVENUE:
            revenue += row["credit"] - row["debit"]
        elif typ == Account.TYPE_EXPENSE:
            expense += row["debit"] - row["credit"]
        else:
            value = D("0")
        if typ in {Account.TYPE_ASSET, Account.TYPE_LIABILITY, Account.TYPE_EQUITY}:
            details.append({**row, "balance": value})
    current_profit = revenue - expense
    total_equity = equity + current_profit
    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": total_equity,
        "current_profit": current_profit,
        "liabilities_plus_equity": liabilities + total_equity,
        "balanced": assets == liabilities + total_equity,
        "accounts": details,
    }
