from django.db import models
from core.models import Store
from django.contrib.auth.models import User


class Category(models.Model):

    name = models.CharField(
        max_length=100,
        verbose_name="نام دسته"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="فروشگاه"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    def __str__(self):
        return f"{self.name} - {self.store.name}"

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="unique_category_per_store"
            )
        ]


class Product(models.Model):

    name = models.CharField(
        max_length=200,
        verbose_name="نام کالا"
    )

    barcode = models.CharField(
        max_length=50,
        verbose_name="بارکد"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="دسته‌بندی"
    )

    unit = models.CharField(
        max_length=30,
        default="عدد",
        verbose_name="واحد"
    )

    purchase_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="قیمت خرید"
    )

    sale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="قیمت فروش"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین ویرایش"
    )



    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "کالا"
        verbose_name_plural = "کالاها"

        constraints = [
            models.UniqueConstraint(
                fields=["category", "barcode"],
                name="unique_barcode_per_store"
            )
        ]
        
        
class Inventory(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventories",
        verbose_name="کالا"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="inventories",
        verbose_name="فروشگاه"
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=0,
        verbose_name="موجودی"
    )

    min_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        default=0,
        verbose_name="حداقل موجودی"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "موجودی کالا"
        verbose_name_plural = "موجودی کالاها"

        constraints = [
            models.UniqueConstraint(
                fields=["product", "store"],
                name="unique_product_store_inventory"
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.store.name}"        
        
        
        
class InventoryTransaction(models.Model):

    TYPE_PURCHASE = "purchase"
    TYPE_SALE = "sale"
    TYPE_RETURN = "return"
    TYPE_ADJUSTMENT = "adjustment"

    TRANSACTION_TYPES = [
        (TYPE_PURCHASE, "Purchase"),
        (TYPE_SALE, "Sale"),
        (TYPE_RETURN, "Return"),
        (TYPE_ADJUSTMENT, "Adjustment"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3
    )

    reference_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


from django.db import models
from core.models import Store


class Supplier(models.Model):

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="suppliers",
        verbose_name="فروشگاه",        
    )

    name = models.CharField(
        max_length=255
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "name"],
                name="unique_supplier_name_per_store",
            )
        ]
    def __str__(self):
        return self.name

class Purchase(models.Model):

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )

    invoice_number = models.CharField(
        max_length=50,
        blank=True
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    received = models.BooleanField(
        default=False
    )    

    def __str__(self):
        return f"Purchase #{self.id}"


class PurchaseItem(models.Model):

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3
    )

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    def save(self, *args, **kwargs):

        self.total_price = (
            self.quantity *
            self.unit_price
        )

        super().save(
            *args,
            **kwargs
        )
        
        self.purchase.total_amount = sum(
            item.total_price
            for item in self.purchase.items.all()
        )

        self.purchase.save(
            update_fields=[
                "total_amount",
                "updated_at",
            ]
        )
        

    def delete(self, *args, **kwargs):

        purchase = self.purchase

        super().delete(*args, **kwargs)

        purchase.total_amount = sum(
            item.total_price
            for item in purchase.items.all()
        )

        purchase.save(
            update_fields=[
                "total_amount",
                "updated_at",
            ]
        )

    def __str__(self):
        return (
            f"{self.product.name}"
        )


class SupplierTransaction(models.Model):
    """
    ثبت گردش مالی تأمین‌کننده.

    purchase   : ایجاد بدهی بابت خرید
    payment    : پرداخت به تأمین‌کننده
    return     : برگشت خرید
    adjustment : اصلاح حساب
    """

    TRANSACTION_TYPES = [
        ("purchase", "خرید"),
        ("payment", "پرداخت"),
        ("return", "برگشت خرید"),
        ("adjustment", "اصلاح حساب"),
    ]

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="transactions"
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )

    reference_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-created_at",
            "-id"
        ]

        verbose_name = (
            "تراکنش تأمین‌کننده"
        )

        verbose_name_plural = (
            "تراکنش‌های تأمین‌کنندگان"
        )

    def __str__(self):
        return (
            f"{self.supplier.name} - "
            f"{self.transaction_type} - "
            f"{self.amount}"
        )
        
        
class PurchaseReturn(models.Model):
    """
    برگشت کالا به تأمین‌کننده.
    """

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        related_name="returns",
        verbose_name="خرید"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_returns",
        verbose_name="کالا"
    )

    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=3,
        verbose_name="مقدار برگشتی"
    )

    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="قیمت واحد"
    )

    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="مبلغ برگشت"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="ثبت‌کننده"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    def save(self, *args, **kwargs):

        self.total_amount = (
            self.quantity * self.unit_price
        )

        super().save(
            *args,
            **kwargs
        )

    def __str__(self):
        return (
            f"برگشت خرید #{self.purchase_id} - "
            f"{self.product.name}"
        )
        