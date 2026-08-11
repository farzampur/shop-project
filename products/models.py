from django.db import models

from core.models import Store


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