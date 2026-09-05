from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Cart, Order, OrderItem, CustomerTransaction, Payment, CashBox, CashBoxTransaction

from products.models import Inventory
from products.models import InventoryTransaction

from io import BytesIO
from decimal import Decimal

import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


class CartValidationService:

    @staticmethod
    def validate(cart):

        if not cart:
            raise ValidationError(
                "سبد خرید پیدا نشد."
            )

        if cart.customer_id and cart.customer.store_id != cart.store_id:
            raise ValidationError("مشتری متعلق به فروشگاه این سبد نیست.")

        items = cart.items.select_related(
            "product",
            "product__category",
        )

        if not items.exists():
            raise ValidationError(
                "سبد خرید خالی است."
            )

        for item in items:

            product = item.product

            if product.category.store_id != cart.store_id:
                raise ValidationError(
                    f"کالای «{product.name}» متعلق به فروشگاه این سبد نیست."
                )

            # فعال بودن کالا
            if not product.is_active:
                raise ValidationError(
                    f"کالای «{product.name}» غیرفعال است."
                )

            # فعال بودن دسته‌بندی
            if not product.category.is_active:
                raise ValidationError(
                    f"دسته‌بندی کالای «{product.name}» غیرفعال است."
                )

            # موجودی فروشگاه
            inventory = product.inventories.filter(
                store=cart.store
            ).first()

            if not inventory:
                raise ValidationError(
                    f"برای کالای «{product.name}» "
                    f"در این فروشگاه موجودی ثبت نشده است."
                )

            # کافی بودن موجودی
            if inventory.quantity < item.quantity:
                raise ValidationError(
                    f"موجودی کالای «{product.name}» کافی نیست. "
                    f"موجودی فعلی: {inventory.quantity}"
                )

        return True
        


class CheckoutService:

    @staticmethod
    @transaction.atomic
    def checkout(cart, payments=None):
        """Create a sale and atomically settle inventory/cash/customer ledger."""
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
        CartValidationService.validate(cart)

        items = list(cart.items.select_related("product", "product__category"))
        totals = [Decimal("0"), Decimal("0"), Decimal("0")]
        for item in items:
            before = item.quantity * item.unit_price
            discount = before * item.discount_percent / Decimal("100")
            totals[0] += before
            totals[1] += discount
            totals[2] += before - discount

        order = Order.objects.create(
            user=cart.user, store=cart.store, customer=cart.customer,
            status="pending",
            total_before_discount=totals[0],
            total_discount=totals[1],
            total_price=totals[2],
        )

        # Lock every inventory row before changing stock.
        inventories = {}
        for item in items:
            inventory = (Inventory.objects.select_for_update()
                         .select_related("product")
                         .filter(product_id=item.product_id, store=cart.store).first())
            if not inventory or inventory.quantity < item.quantity:
                raise ValidationError(
                    f"موجودی کالای «{item.product.name}» کافی نیست."
                )
            inventories[item.product_id] = inventory

        for item in items:
            before = item.quantity * item.unit_price
            discount_amount = item.unit_price * item.discount_percent / Decimal("100")
            final_unit_price = item.unit_price - discount_amount
            OrderItem.objects.create(
                order=order, product=item.product, product_name=item.product.name,
                quantity=item.quantity, unit_price=item.unit_price,
                purchase_price=item.product.purchase_price,
                discount_percent=item.discount_percent,
                discount_amount=discount_amount,
                total_price_before_discount=before,
                total_discount_amount=item.quantity * discount_amount,
                total_price=item.quantity * final_unit_price,
            )

        # Inventory is reserved/consumed at checkout and is reversed on cancellation.
        for item in items:
            inventory = inventories[item.product_id]
            inventory.quantity -= item.quantity
            inventory.save(update_fields=["quantity", "updated_at"])
            InventoryTransaction.objects.create(
                product=item.product, store=cart.store, transaction_type="sale",
                quantity=item.quantity, reference_id=order.id,
                description=f"Order #{order.id}",
            )

        CheckoutService._settle_order(order, payments or [])
        cart.items.all().delete()
        return order

    @staticmethod
    def _settle_order(order, payments):
        total = Decimal(order.total_price)
        if not payments:
            return

        allowed_methods = {"cash", "card", "credit"}
        for payment in payments:
            method = payment.get("method")
            amount = Decimal(payment.get("amount", 0))
            if method not in allowed_methods:
                raise ValidationError({"payments": "روش پرداخت نامعتبر است."})
            if amount <= 0:
                raise ValidationError({"payments": "مبلغ هر پرداخت باید بیشتر از صفر باشد."})
            if method in {"cash", "card"} and not payment.get("cashbox_id"):
                raise ValidationError({"payments": "برای پرداخت نقدی/کارتخوان صندوق الزامی است."})
            if method == "credit" and payment.get("cashbox_id"):
                raise ValidationError({"payments": "برای پرداخت حسابی صندوق ارسال نکنید."})

        paid = sum((Decimal(p["amount"]) for p in payments), Decimal("0"))
        if paid != total:
            raise ValidationError({"payments": "مجموع پرداخت‌ها باید دقیقاً برابر مبلغ سفارش باشد."})

        if any(p["method"] == "credit" for p in payments) and not order.customer:
            raise ValidationError({"payments": "فروش حسابی بدون مشتری مجاز نیست."})

        cashbox_ids = [p.get("cashbox_id") for p in payments if p["method"] in {"cash", "card"}]
        cashboxes = {
            cb.id: cb for cb in CashBox.objects.select_for_update().filter(
                id__in=cashbox_ids, store=order.store
            )
        }

        for p in payments:
            amount = Decimal(p["amount"])
            method = p["method"]
            cashbox = None
            if method in {"cash", "card"}:
                cashbox = cashboxes.get(p.get("cashbox_id"))
                if not cashbox:
                    raise ValidationError({"payments": "صندوق انتخاب‌شده متعلق به این فروشگاه نیست."})
                cashbox.balance += amount
                cashbox.save(update_fields=["balance", "updated_at"])
                CashBoxTransaction.objects.create(
                    cashbox=cashbox, transaction_type="receive", amount=amount,
                    reference_id=order.id, description=f"Order #{order.id} / {method}",
                )
            else:
                CustomerTransaction.objects.create(
                    customer=order.customer, store=order.store,
                    transaction_type="sale", amount=amount,
                    reference_id=order.id, description=f"Order #{order.id}",
                )

            Payment.objects.create(
                order=order, method=method, amount=amount, cashbox=cashbox
            )

        order.status = "paid"
        order.save(update_fields=["status", "updated_at"])


class OrderService:

    @staticmethod
    @transaction.atomic
    def settle(order, payments):
        order = Order.objects.select_for_update().get(pk=order.pk)
        if order.status not in {"pending", "confirmed"}:
            raise ValidationError("این سفارش قابل پرداخت نیست.")
        CheckoutService._settle_order(order, payments)
        return order

    ALLOWED_TRANSITIONS = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"cancelled"},
        "paid": {"cancelled"},
        "cancelled": set(),
    }

    @staticmethod
    @transaction.atomic
    def change_status(order, new_status):
        original_order = order
        order = Order.objects.select_for_update().get(pk=order.pk)
        old_status = order.status
        if new_status not in OrderService.ALLOWED_TRANSITIONS.get(old_status, set()):
            raise ValidationError(
                f"تغییر وضعیت از «{old_status}» به «{new_status}» مجاز نیست."
            )

        if new_status == "cancelled":
            # Reverse stock exactly once.
            for item in order.items.select_related("product"):
                inventory = Inventory.objects.select_for_update().get(
                    product_id=item.product_id, store=order.store
                )
                inventory.quantity += item.quantity
                inventory.save(update_fields=["quantity", "updated_at"])
                InventoryTransaction.objects.create(
                    product=item.product, store=order.store, transaction_type="return",
                    quantity=item.quantity, reference_id=order.id,
                    description=f"Cancel Order #{order.id}",
                )

            # Reverse cash settlements.
            for payment in order.payments.select_related("cashbox"):
                if payment.cashbox_id:
                    cashbox = CashBox.objects.select_for_update().get(pk=payment.cashbox_id)
                    if cashbox.balance < payment.amount:
                        raise ValidationError("موجودی صندوق برای برگشت وجه کافی نیست.")
                    cashbox.balance -= payment.amount
                    cashbox.save(update_fields=["balance", "updated_at"])
                    CashBoxTransaction.objects.create(
                        cashbox=cashbox, transaction_type="payment", amount=payment.amount,
                        reference_id=order.id, description=f"Refund Order #{order.id}",
                    )

            # Reverse customer account entries only when the sale was on account.
            # Cash/card sales may legitimately have no customer.
            if order.customer_id:
                for tx in order.customer.transactions.filter(
                    reference_id=order.id, transaction_type="sale"
                ):
                    CustomerTransaction.objects.create(
                        customer=tx.customer, store=order.store, transaction_type="payment",
                        amount=tx.amount, reference_id=order.id,
                        description=f"Cancel Order #{order.id}",
                    )

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        # Keep the caller's instance in sync with the locked database instance.
        original_order.status = order.status
        original_order.updated_at = order.updated_at
        return original_order


## چاپ فاکتور ##
from pathlib import Path

FONT_NAME = "InvoiceArial"
FONT_PATH = Path(__file__).resolve().parent.parent / "fonts" / "arial.ttf"

if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(
        TTFont(
            FONT_NAME,
            str(FONT_PATH),
        )
    )


def fa(text):
    if text is None:
        return ""

    text = str(text)

    reshaped = arabic_reshaper.reshape(
        text
    )

    return get_display(
        reshaped
    )


def money(value):
    if value is None:
        value = Decimal("0")

    return f"{Decimal(value):,.0f}"


def build_invoice_pdf(order):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title=f"فاکتور فروش شماره {order.id}",
        author=str(order.user),
    )

    styles = getSampleStyleSheet()

    # ==================================================
    # استایل‌ها
    # ==================================================

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=19,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=3 * mm,
    )

    subtitle_style = ParagraphStyle(
        "InvoiceSubtitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
    )

    normal_style = ParagraphStyle(
        "InvoiceNormal",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=14,
        alignment=TA_RIGHT,
    )

    small_style = ParagraphStyle(
        "InvoiceSmall",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT,
    )

    info_label_style = ParagraphStyle(
        "InvoiceInfoLabel",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#666666"),
    )

    info_value_style = ParagraphStyle(
        "InvoiceInfoValue",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
    )

    total_label_style = ParagraphStyle(
        "InvoiceTotalLabel",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=13,
        alignment=TA_RIGHT,
    )

    total_value_style = ParagraphStyle(
        "InvoiceTotalValue",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=10,
        leading=13,
        alignment=TA_RIGHT,
    )

    final_total_style = ParagraphStyle(
        "InvoiceFinalTotal",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=12,
        leading=16,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#0B5D1E"),
    )

    story = []

    # ==================================================
    # اطلاعات مشتری
    # ==================================================

    if order.customer:

        customer_name = (
            f"{order.customer.first_name} "
            f"{order.customer.last_name}"
        ).strip()

        if not customer_name:
            customer_name = "مشتری"

        customer_mobile = (
            order.customer.mobile
            or ""
        )

    else:

        customer_name = (
            "مشتری متفرقه"
        )

        customer_mobile = ""

    # ==================================================
    # وضعیت سفارش
    # ==================================================

    status_map = {
        "pending": "در انتظار",
        "completed": "تکمیل شده",
        "cancelled": "لغو شده",
    }

    status_text = status_map.get(
        str(order.status),
        str(order.status),
    )

    # ==================================================
    # سربرگ
    # ==================================================

    header_data = [
        [
            Paragraph(
                fa("فاکتور فروش"),
                title_style,
            )
        ],
        [
            Paragraph(
                fa("صورتحساب فروش کالا"),
                subtitle_style,
            )
        ],
    ]

    header_table = Table(
        header_data,
        colWidths=[
            186 * mm
        ],
    )

    header_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#1F2937"),
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 0),
                    1,
                    colors.HexColor("#1F2937"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        header_table
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    # ==================================================
    # اطلاعات فاکتور
    # ==================================================

    info_data = [

        [
            Paragraph(
                fa("شماره فاکتور"),
                info_label_style,
            ),

            Paragraph(
                fa("تاریخ"),
                info_label_style,
            ),

            Paragraph(
                fa("وضعیت"),
                info_label_style,
            ),

            Paragraph(
                fa("فروشنده"),
                info_label_style,
            ),
        ],

        [
            Paragraph(
                str(order.id),
                info_value_style,
            ),

            Paragraph(
                str(order.created_at),
                info_value_style,
            ),

            Paragraph(
                fa(status_text),
                info_value_style,
            ),

            Paragraph(
                fa(str(order.user)),
                info_value_style,
            ),
        ],

        [
            Paragraph(
                fa("فروشگاه"),
                info_label_style,
            ),

            Paragraph(
                fa("مشتری"),
                info_label_style,
            ),

            Paragraph(
                fa("موبایل مشتری"),
                info_label_style,
            ),

            Paragraph(
                fa("تعداد اقلام"),
                info_label_style,
            ),
        ],

        [
            Paragraph(
                fa(str(order.store)),
                info_value_style,
            ),

            Paragraph(
                fa(customer_name),
                info_value_style,
            ),

            Paragraph(
                fa(customer_mobile),
                info_value_style,
            ),

            Paragraph(
                str(order.items.count()),
                info_value_style,
            ),
        ],
    ]

    info_table = Table(
        info_data,
        colWidths=[
            46.5 * mm,
            46.5 * mm,
            46.5 * mm,
            46.5 * mm,
        ],
        rowHeights=[
            9 * mm,
            11 * mm,
            9 * mm,
            11 * mm,
        ],
    )

    info_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D1D5DB"),
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#F3F4F6"),
                ),

                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    colors.HexColor("#F3F4F6"),
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "RIGHT",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        info_table
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # ==================================================
    # جدول اقلام
    # ==================================================

    table_data = [
        [
            fa("ردیف"),
            fa("شرح کالا"),
            fa("تعداد"),
            fa("قیمت واحد"),
            fa("تخفیف"),
            fa("مبلغ"),
        ]
    ]

    for index, item in enumerate(
        order.items.all(),
        start=1,
    ):

        table_data.append(
            [
                str(index),

                Paragraph(
                    fa(item.product_name),
                    small_style,
                ),

                str(
                    item.quantity
                ),

                money(
                    item.unit_price
                ),

                f"{item.discount_percent}%",

                money(
                    item.total_price
                ),
            ]
        )

    item_table = Table(
        table_data,
        colWidths=[
            13 * mm,
            71 * mm,
            20 * mm,
            28 * mm,
            20 * mm,
            34 * mm,
        ],
        repeatRows=1,
    )

    item_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F2937"),
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D1D5DB"),
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    FONT_NAME,
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F9FAFB"),
                    ],
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(
        item_table
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    # ==================================================
    # خلاصه مالی
    # ==================================================

    summary_data = [
        [
            Paragraph(
                fa("مبلغ قبل از تخفیف"),
                total_label_style,
            ),

            Paragraph(
                money(
                    order.total_before_discount
                ),
                total_value_style,
            ),
        ],

        [
            Paragraph(
                fa("مجموع تخفیف"),
                total_label_style,
            ),

            Paragraph(
                money(
                    order.total_discount
                ),
                total_value_style,
            ),
        ],

        [
            Paragraph(
                fa("مبلغ قابل پرداخت"),
                final_total_style,
            ),

            Paragraph(
                money(
                    order.total_price
                ),
                final_total_style,
            ),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            120 * mm,
            60 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D1D5DB"),
                ),

                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    colors.HexColor("#ECFDF5"),
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            8 * mm,
        )
    )

    # ==================================================
    # پایین فاکتور
    # ==================================================

    footer_box = Table(
        [
            [
                Paragraph(
                    fa(
                        "این فاکتور به صورت سیستمی صادر شده است."
                    ),
                    small_style,
                )
            ],

            [
                Paragraph(
                    fa(
                        "از خرید شما سپاسگزاریم."
                    ),
                    ParagraphStyle(
                        "FooterThanks",
                        parent=small_style,
                        alignment=TA_CENTER,
                        fontSize=9,
                    ),
                )
            ],
        ],
        colWidths=[
            180 * mm,
        ],
    )

    footer_box.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D1D5DB"),
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F9FAFB"),
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(
        footer_box
    )

    # ==================================================
    # شماره صفحه
    # ==================================================

    def draw_page_number(
        canvas,
        doc,
    ):
        canvas.saveState()

        canvas.setFont(
            FONT_NAME,
            8,
        )

        canvas.drawCentredString(
            A4[0] / 2,
            7 * mm,
            fa(
                f"صفحه {doc.page}"
            ),
        )

        canvas.restoreState()

    # ==================================================
    # ساخت PDF
    # ==================================================

    document.build(
        story,
        onFirstPage=draw_page_number,
        onLaterPages=draw_page_number,
    )

    buffer.seek(0)

    return buffer
    
    
def build_thermal_receipt_pdf(order):
    """
    تولید رسید حرارتی 80mm
    با عرض چاپ مؤثر حدود 72mm
    """

    buffer = BytesIO()

    # عرض مفید چاپ حدود 72mm
    receipt_width = 72 * mm

    # ارتفاع را متناسب با تعداد اقلام تعیین می‌کنیم
    item_count = order.items.count()

    receipt_height = (
        105 * mm
        + (item_count * 12 * mm)
    )

    document = SimpleDocTemplate(
        buffer,
        pagesize=(
            receipt_width,
            receipt_height,
        ),
        rightMargin=3 * mm,
        leftMargin=3 * mm,
        topMargin=4 * mm,
        bottomMargin=5 * mm,
        title=f"رسید فروش {order.id}",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ThermalTitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
    )

    normal_style = ParagraphStyle(
        "ThermalNormal",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT,
    )

    small_style = ParagraphStyle(
        "ThermalSmall",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=7,
        leading=9,
        alignment=TA_RIGHT,
    )

    bold_style = ParagraphStyle(
        "ThermalBold",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
    )

    total_style = ParagraphStyle(
        "ThermalTotal",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT,
    )

    story = []

    # =========================================
    # اطلاعات مشتری
    # =========================================

    if order.customer:

        customer_name = (
            f"{order.customer.first_name} "
            f"{order.customer.last_name}"
        ).strip()

        customer_mobile = (
            order.customer.mobile
            or ""
        )

    else:

        customer_name = "مشتری متفرقه"
        customer_mobile = ""

    # =========================================
    # عنوان
    # =========================================

    story.append(
        Paragraph(
            fa("فاکتور فروش"),
            title_style,
        )
    )

    story.append(
        Paragraph(
            fa("رسید فروش"),
            ParagraphStyle(
                "ThermalSubtitle",
                parent=small_style,
                alignment=TA_CENTER,
                fontSize=8,
            ),
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    # =========================================
    # مشخصات اصلی
    # =========================================

    header_data = [
        [
            Paragraph(
                fa(
                    f"فروشگاه: {order.store}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"شماره: {order.id}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"تاریخ: {order.created_at}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"مشتری: {customer_name}"
                ),
                small_style,
            )
        ],
    ]

    if customer_mobile:

        header_data.append(
            [
                Paragraph(
                    fa(
                        f"موبایل: "
                        f"{customer_mobile}"
                    ),
                    small_style,
                )
            ]
        )

    header_table = Table(
        header_data,
        colWidths=[
            66 * mm,
        ],
    )

    header_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    story.append(
        header_table
    )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    # =========================================
    # اقلام
    # =========================================

    for index, item in enumerate(
        order.items.all(),
        start=1,
    ):

        item_data = [
            [
                Paragraph(
                    fa(
                        f"{index}. "
                        f"{item.product_name}"
                    ),
                    bold_style,
                )
            ],
            [
                Paragraph(
                    fa(
                        f"تعداد: "
                        f"{item.quantity}"
                    ),
                    small_style,
                )
            ],
            [
                Paragraph(
                    fa(
                        f"قیمت واحد: "
                        f"{money(item.unit_price)}"
                    ),
                    small_style,
                )
            ],
            [
                Paragraph(
                    fa(
                        f"تخفیف: "
                        f"{item.discount_percent}%"
                    ),
                    small_style,
                )
            ],
            [
                Paragraph(
                    fa(
                        f"مبلغ: "
                        f"{money(item.total_price)}"
                    ),
                    bold_style,
                )
            ],
        ]

        item_table = Table(
            item_data,
            colWidths=[
                66 * mm,
            ],
        )

        item_table.setStyle(
            TableStyle(
                [
                    (
                        "LINEBELOW",
                        (0, -1),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        2,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        1,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        1,
                    ),
                ]
            )
        )

        story.append(
            item_table
        )

    story.append(
        Spacer(
            1,
            3 * mm,
        )
    )

    # =========================================
    # خلاصه مبالغ
    # =========================================

    summary_data = [
        [
            Paragraph(
                fa("قبل از تخفیف"),
                small_style,
            ),
            Paragraph(
                money(
                    order.total_before_discount
                ),
                small_style,
            ),
        ],
        [
            Paragraph(
                fa("تخفیف"),
                small_style,
            ),
            Paragraph(
                money(
                    order.total_discount
                ),
                small_style,
            ),
        ],
        [
            Paragraph(
                fa("قابل پرداخت"),
                total_style,
            ),
            Paragraph(
                money(
                    order.total_price
                ),
                total_style,
            ),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            38 * mm,
            28 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "LINEABOVE",
                    (0, 2),
                    (-1, 2),
                    1,
                    colors.black,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    # =========================================
    # پایین رسید
    # =========================================

    story.append(
        Paragraph(
            fa(
                "از خرید شما سپاسگزاریم"
            ),
            ParagraphStyle(
                "ThermalThanks",
                parent=small_style,
                alignment=TA_CENTER,
                fontSize=9,
            ),
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm,
        )
    )

    story.append(
        Paragraph(
            fa(
                "این رسید به صورت سیستمی صادر شده است."
            ),
            ParagraphStyle(
                "ThermalSystem",
                parent=small_style,
                alignment=TA_CENTER,
                fontSize=7,
            ),
        )
    )

    # =========================================
    # ساخت PDF
    # =========================================

    document.build(
        story
    )

    buffer.seek(0)

    return buffer


    