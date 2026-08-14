from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Cart, Order, OrderItem, CustomerTransaction

from products.models import Inventory
from products.models import InventoryTransaction

class CartValidationService:

    @staticmethod
    def validate(cart):

        if not cart:
            raise ValidationError(
                "سبد خرید پیدا نشد."
            )

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
    def checkout(cart):

        # 1. اعتبارسنجی Cart
        CartValidationService.validate(cart)

        # 2. ایجاد Order
 
        total_before_discount = 0
        total_discount = 0
        total_price = 0

        for cart_item in cart.items.all():

            line_before_discount = (
                cart_item.quantity *
                cart_item.unit_price
            )

            line_discount = (
                line_before_discount *
                cart_item.discount_percent / 100
            )

            line_total = (
                line_before_discount -
                line_discount
            )

            total_before_discount += line_before_discount
            total_discount += line_discount
            total_price += line_total

        order = Order.objects.create(
            user=cart.user,
            store=cart.store,
            customer=cart.customer,
            status="pending",
            total_before_discount=total_before_discount,
            total_discount=total_discount,
            total_price=total_price,
        )

        if order.customer:
                        
            CustomerTransaction.objects.create(
                customer=order.customer,
                transaction_type="sale",
                amount=order.total_price,
                reference_id=order.id,
                description=f"Order #{order.id}"
            )        


        # 3. ایجاد OrderItemها
        for cart_item in cart.items.select_related(
            "product",
            "product__category",
        ):

            product = cart_item.product

            quantity = cart_item.quantity
            unit_price = cart_item.unit_price
            discount_percent = cart_item.discount_percent

            # مبلغ قبل از تخفیف
            item_total_before_discount = (
                quantity * unit_price
            )

            # مبلغ تخفیف واحد
            discount_amount = (
                unit_price * discount_percent / 100
            )

            # مبلغ نهایی واحد
            final_unit_price = (
                unit_price - discount_amount
            )

            # کل تخفیف
            total_discount_amount = (
                quantity * discount_amount
            )

            # مبلغ نهایی
            item_total_price = (
                quantity * final_unit_price
            )

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                discount_percent=discount_percent,
                discount_amount=discount_amount,
                total_price_before_discount=(
                    item_total_before_discount
                ),
                total_discount_amount=(
                    total_discount_amount
                ),
                total_price=item_total_price,
            )

        # 5. کاهش موجودی
        for cart_item in cart.items.select_related(
            "product"
        ):

            inventory = cart_item.product.inventories.filter(
                store=cart.store
            ).first()

            if not inventory:
                raise ValidationError(
                    f"موجودی کالای "
                    f"«{cart_item.product.name}» پیدا نشد."
                )

            if inventory.quantity < cart_item.quantity:
                raise ValidationError(
                    f"موجودی کالای "
                    f"«{cart_item.product.name}» کافی نیست."
                )

            inventory.quantity -= cart_item.quantity
            inventory.save(
                update_fields=[
                    "quantity",
                    "updated_at",
                ]
            )
            InventoryTransaction.objects.create(
                product=cart_item.product,
                store=cart.store,
                transaction_type="sale",
                quantity=cart_item.quantity,
                reference_id=order.id,
                description=f"Order #{order.id}"
            )            


        # 6. خالی کردن Cart
        cart.items.all().delete()

        return order




class OrderService:

    @staticmethod
    @transaction.atomic
    def change_status(order, new_status):

        old_status = order.status

        if old_status == new_status:
            return order

        if (
            old_status != "cancelled"
            and new_status == "cancelled"
        ):

            for item in order.items.all():

                inventory = Inventory.objects.select_for_update().get(
                    product_id=item.product_id,
                    store=order.store,
                )

                inventory.quantity += item.quantity

                inventory.save()
                InventoryTransaction.objects.create(
                    product=item.product,
                    store=order.store,
                    transaction_type="return",
                    quantity=item.quantity,
                    reference_id=order.id,
                    description=f"Cancel Order #{order.id}"
)
        order.status = new_status
        order.save()

        return order



        