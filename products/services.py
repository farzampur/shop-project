from django.db import transaction
from io import BytesIO
import random
from io import BytesIO

import barcode
import qrcode
from barcode.writer import ImageWriter
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image
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
    Product,
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

    
def is_valid_ean13(barcode):
    """
    بررسی معتبر بودن بارکد EAN-13
    """

    if not barcode:
        return False

    barcode = str(barcode).strip()

    if len(barcode) != 13:
        return False

    if not barcode.isdigit():
        return False

    digits = [
        int(char)
        for char in barcode
    ]

    total = (
        sum(digits[0:12:2])
        +
        3 * sum(digits[1:12:2])
    )

    check_digit = (
        10 - (total % 10)
    ) % 10

    return (
        check_digit
        == digits[12]
    )




def generate_ean13():
    """
    تولید یک بارکد معتبر EAN-13
    و جلوگیری از تکراری بودن آن در Product.
    """

    while True:

        base = (
            "626"
            + "".join(
                str(
                    random.randint(0, 9)
                )
                for _ in range(9)
            )
        )

        digits = [
            int(char)
            for char in base
        ]

        total = (
            sum(
                digits[0:12:2]
            )
            +
            3 * sum(
                digits[1:12:2]
            )
        )

        check_digit = (
            10 - (total % 10)
        ) % 10

        barcode = (
            base
            + str(check_digit)
        )

        if not Product.objects.filter(
            barcode=barcode
        ).exists():

            return barcode


def build_product_barcode_png(product):
    """
    تولید تصویر PNG از بارکد EAN-13 محصول
    """

    if not product.barcode:
        raise ValueError(
            "این کالا بارکد ندارد."
        )

    if not is_valid_ean13(
        product.barcode
    ):
        raise ValueError(
            "بارکد کالا EAN-13 معتبر نیست."
        )

    ean13 = barcode.get(
        "ean13",
        product.barcode[:-1],
        writer=ImageWriter(),
    )

    buffer = BytesIO()

    ean13.write(
        buffer,
        options={
            "module_width": 0.35,
            "module_height": 18,
            "font_size": 9,
            "text_distance": 3,
            "quiet_zone": 6.5,
            "write_text": True,
        },
    )

    buffer.seek(0)

    return buffer


import qrcode
from io import BytesIO


def build_product_qrcode_png(product):

    if not product.barcode:
        raise ValueError(
            "این کالا بارکد ندارد."
        )

    data = (
        f"PRODUCT:{product.id}|"
        f"BARCODE:{product.barcode}|"
        f"NAME:{product.name}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(data)
    qr.make(
        fit=True
    )

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer
    
def build_product_label_pdf(product):
    """
    تولید PDF برچسب یک کالا
    شامل نام، قیمت، Barcode و QR Code
    """

    if not product.barcode:
        raise ValueError(
            "این کالا بارکد ندارد."
        )

    if not is_valid_ean13(
        product.barcode
    ):
        raise ValueError(
            "بارکد کالا EAN-13 معتبر نیست."
        )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()

    label_title_style = ParagraphStyle(
        "LabelTitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
    )

    label_price_style = ParagraphStyle(
        "LabelPrice",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
    )

    story = []

    # -----------------------------------------
    # Barcode
    # -----------------------------------------

    barcode_buffer = build_product_barcode_png(
        product
    )



    # -----------------------------------------
    # QR Code
    # -----------------------------------------

    qrcode_buffer = build_product_qrcode_png(
        product
    )



    # -----------------------------------------
    # اطلاعات برچسب
    # -----------------------------------------

    product_name = Paragraph(
        fa(product.name),
        label_title_style,
    )

    product_price = Paragraph(
        fa(
            f"قیمت: {money(product.sale_price)}"
        ),
        label_price_style,
    )

    # -----------------------------------------
    # ساخت Table
    # -----------------------------------------

    label_data = [
        [
            product_name
        ],
        [
            product_price
        ],
        [
            Table(
                [
                    [
                        Image(
                            barcode_buffer,
                            width=55 * mm,
                            height=20 * mm,
                        ),
                        Image(
                            qrcode_buffer,
                            width=25 * mm,
                            height=25 * mm,
                        ),
                    ]
                ],
                colWidths=[
                    60 * mm,
                    30 * mm,
                ],
            )
        ],
        [
            Paragraph(
                fa(product.barcode),
                label_price_style,
            )
        ],
    ]

    label_table = Table(
        label_data,
        colWidths=[
            90 * mm
        ],
    )

    label_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    colors.black,
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
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(
        label_table
    )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer


def build_product_labels_pdf(
    product,
    count=9,
):
    """
    تولید PDF چند برچسب برای یک کالا
    در صفحات A4

    تعداد پیش‌فرض: 9 برچسب
    """

    if not product.barcode:
        raise ValueError(
            "این کالا بارکد ندارد."
        )

    if not is_valid_ean13(
        product.barcode
    ):
        raise ValueError(
            "بارکد کالا EAN-13 معتبر نیست."
        )

    try:
        count = int(count)
    except (TypeError, ValueError):
        raise ValueError(
            "تعداد برچسب نامعتبر است."
        )

    if count < 1:
        raise ValueError(
            "تعداد برچسب باید حداقل 1 باشد."
        )

    if count > 100:
        raise ValueError(
            "حداکثر تعداد برچسب 100 عدد است."
        )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
    )

    styles = getSampleStyleSheet()

    label_name_style = ParagraphStyle(
        "MultiLabelName",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
    )

    label_price_style = ParagraphStyle(
        "MultiLabelPrice",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=7,
        leading=9,
        alignment=TA_CENTER,
    )

    label_barcode_style = ParagraphStyle(
        "MultiLabelBarcode",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=6,
        leading=8,
        alignment=TA_CENTER,
    )

    # ----------------------------------------
    # تعداد ستون و ردیف
    # ----------------------------------------

    columns = 3

    rows = (
        count + columns - 1
    ) // columns

    # ----------------------------------------
    # اندازه هر برچسب
    # ----------------------------------------

    page_width = A4[0]
    page_height = A4[1]

    usable_width = (
        page_width
        - 16 * mm
    )

    usable_height = (
        page_height
        - 16 * mm
    )

    horizontal_gap = 3 * mm
    vertical_gap = 3 * mm

    label_width = (
        usable_width
        - (
            (columns - 1)
            * horizontal_gap
        )
    ) / columns

    label_height = (
        82 * mm
    )

    # ----------------------------------------
    # تصاویر
    # ----------------------------------------

    barcode_buffer = (
        build_product_barcode_png(
            product
        )
    )

    barcode_data = (
        barcode_buffer.getvalue()
    )

    qrcode_buffer = (
        build_product_qrcode_png(
            product
        )
    )

    qrcode_data = (
        qrcode_buffer.getvalue()
    )

    # ----------------------------------------
    # ساخت برچسب
    # ----------------------------------------

    def create_label():

        barcode_stream = BytesIO(
            barcode_data
        )

        qrcode_stream = BytesIO(
            qrcode_data
        )

        barcode_image = Image(
            barcode_stream,
            width=(
                label_width - 8 * mm
            ),
            height=18 * mm,
        )

        qrcode_image = Image(
            qrcode_stream,
            width=24 * mm,
            height=24 * mm,
        )

        product_name = Paragraph(
            fa(product.name),
            label_name_style,
        )

        product_price = Paragraph(
            fa(
                f"قیمت: "
                f"{money(product.sale_price)}"
            ),
            label_price_style,
        )

        product_barcode = Paragraph(
            fa(product.barcode),
            label_barcode_style,
        )

        label_content = [
            [
                product_name
            ],
            [
                product_price
            ],
            [
                barcode_image
            ],
            [
                product_barcode
            ],
            [
                qrcode_image
            ],
        ]

        label_table = Table(
            label_content,
            colWidths=[
                label_width - 4 * mm
            ],
        )

        label_table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        colors.black,
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

        return label_table

    # ----------------------------------------
    # ساخت برچسب‌ها
    # ----------------------------------------

    labels = []

    for _ in range(count):
        labels.append(
            create_label()
        )

    # پر کردن ردیف آخر
    while len(labels) % columns != 0:
        labels.append("")

    # ----------------------------------------
    # ساخت صفحات
    # ----------------------------------------

    story = []

    for row_index in range(
        0,
        len(labels),
        columns,
    ):

        row = labels[
            row_index:
            row_index + columns
        ]

        story.append(
            Table(
                [row],
                colWidths=[
                    label_width
                ] * columns,
                rowHeights=[
                    label_height
                ],
                hAlign="CENTER",
            )
        )

        if (
            row_index + columns
            < len(labels)
        ):
            story.append(
                Spacer(
                    1,
                    vertical_gap,
                )
            )

    document.build(
        story
    )

    buffer.seek(0)

    return buffer

    