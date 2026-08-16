from django.db import transaction
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_CENTER,
    TA_RIGHT,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .models import (
    Purchase,
    PurchaseItem,
    Inventory,
    InventoryTransaction,
)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
FONT_NAME = "InvoiceArial"

if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(
        TTFont(
            FONT_NAME,
            FONT_PATH,
        )
    )

import arabic_reshaper
from bidi.algorithm import get_display


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
    
from decimal import Decimal


def money(value):
    if value is None:
        value = Decimal("0")

    return f"{Decimal(value):,.0f}"
    
    
class PurchaseService:

    @staticmethod
    @transaction.atomic
    def receive_purchase(purchase):

        purchase = (
            Purchase.objects
            .select_for_update()
            .get(pk=purchase.pk)
        )

        if purchase.received:
            raise ValueError(
                "این خرید قبلاً دریافت شده است."
            )

        for item in purchase.items.all():

            # ---------------------------------
            # بررسی تراکنش قبلی این قلم خرید
            # ---------------------------------

            inventory_transaction = (
                InventoryTransaction.objects
                .filter(
                    product=item.product,
                    store=purchase.store,
                    transaction_type=(
                        InventoryTransaction.TYPE_PURCHASE
                    ),
                    reference_id=purchase.id,
                )
                .first()
            )

            # اگر قبلاً ثبت شده، نباید موجودی
            # دوباره افزایش پیدا کند.
            if inventory_transaction:
                continue

            # ---------------------------------
            # پیدا کردن موجودی
            # ---------------------------------

            inventory = (
                Inventory.objects
                .select_for_update()
                .filter(
                    product=item.product,
                    store=purchase.store,
                )
                .first()
            )

            # ---------------------------------
            # ایجاد / افزایش موجودی
            # ---------------------------------

            if inventory is None:

                inventory = Inventory.objects.create(
                    product=item.product,
                    store=purchase.store,
                    quantity=item.quantity,
                    min_quantity=0,
                )

            else:

                inventory.quantity += (
                    item.quantity
                )

                inventory.save(
                    update_fields=[
                        "quantity",
                        "updated_at",
                    ]
                )

            # ---------------------------------
            # ثبت گردش انبار
            # ---------------------------------

            InventoryTransaction.objects.create(
                product=item.product,
                store=purchase.store,
                transaction_type=(
                    InventoryTransaction.TYPE_PURCHASE
                ),
                quantity=item.quantity,
                reference_id=purchase.id,
                description=(
                    f"Purchase #{purchase.id}"
                ),
            )

        # -------------------------------------
        # دریافت خرید
        # -------------------------------------

        purchase.received = True

        purchase.save(
            update_fields=[
                "received",
                "updated_at",
            ]
        )

        return purchase
        
def build_purchase_receipt_pdf(purchase):
    """
    تولید رسید خرید برای پرینتر حرارتی 80mm
    """

    buffer = BytesIO()

    receipt_width = 72 * mm

    item_count = purchase.items.count()

    receipt_height = (
        110 * mm
        + (item_count * 14 * mm)
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
        title=(
            f"رسید خرید شماره {purchase.id}"
        ),
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PurchaseReceiptTitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
    )

    normal_style = ParagraphStyle(
        "PurchaseReceiptNormal",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT,
    )

    small_style = ParagraphStyle(
        "PurchaseReceiptSmall",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=7,
        leading=9,
        alignment=TA_RIGHT,
    )

    bold_style = ParagraphStyle(
        "PurchaseReceiptBold",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
    )

    total_style = ParagraphStyle(
        "PurchaseReceiptTotal",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT,
    )

    story = []

    # =========================================
    # اطلاعات تأمین‌کننده
    # =========================================

    supplier_name = str(
        purchase.supplier
    )

    store_name = str(
        purchase.store
    )

    username = str(
        purchase.user
    )

    # =========================================
    # عنوان
    # =========================================

    story.append(
        Paragraph(
            fa("رسید خرید"),
            title_style,
        )
    )

    story.append(
        Paragraph(
            fa("ورود کالا از تأمین‌کننده"),
            ParagraphStyle(
                "PurchaseReceiptSubtitle",
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
    # اطلاعات اصلی خرید
    # =========================================

    header_data = [
        [
            Paragraph(
                fa(
                    f"شماره خرید: "
                    f"{purchase.id}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"شماره فاکتور: "
                    f"{purchase.invoice_number or '-'}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"تأمین‌کننده: "
                    f"{supplier_name}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"فروشگاه: "
                    f"{store_name}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"ثبت‌کننده: "
                    f"{username}"
                ),
                small_style,
            )
        ],
        [
            Paragraph(
                fa(
                    f"تاریخ: "
                    f"{purchase.created_at}"
                ),
                small_style,
            )
        ],
    ]

    header_table = Table(
        header_data,
        colWidths=[
            66 * mm
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
    # اقلام خرید
    # =========================================

    for index, item in enumerate(
        purchase.items.all(),
        start=1,
    ):

        item_data = [
            [
                Paragraph(
                    fa(
                        f"{index}. "
                        f"{item.product}"
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
                66 * mm
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
    # جمع خرید
    # =========================================

    summary_data = [
        [
            Paragraph(
                fa("مبلغ کل خرید"),
                total_style,
            ),
            Paragraph(
                money(
                    purchase.total_amount
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
                    (0, 0),
                    (-1, 0),
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
                    3,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
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
    # وضعیت دریافت
    # =========================================

    received_text = (
        "دریافت شده"
        if purchase.received
        else "دریافت نشده"
    )

    story.append(
        Paragraph(
            fa(
                f"وضعیت کالا: {received_text}"
            ),
            ParagraphStyle(
                "PurchaseReceived",
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

    story.append(
        Paragraph(
            fa(
                "رسید خرید به صورت سیستمی صادر شده است."
            ),
            ParagraphStyle(
                "PurchaseFooter",
                parent=small_style,
                alignment=TA_CENTER,
                fontSize=7,
            ),
        )
    )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer

    