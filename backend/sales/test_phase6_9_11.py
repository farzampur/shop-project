from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Store
from products.models import Category, Product
from .models import Order


class OrderDocumentIntegrity611Tests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="611 Sales Store", code="611-S")
        self.user = User.objects.create_user(username="611sales", password="x")

    def assert_db_rejects(self, **kwargs):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Order.objects.create(user=self.user, store=self.store, **kwargs)

    def test_order_total_before_discount_cannot_be_negative(self):
        self.assert_db_rejects(total_before_discount=-1)

    def test_order_total_discount_and_total_price_cannot_be_negative(self):
        self.assert_db_rejects(total_discount=-1)
        self.assert_db_rejects(total_price=-1)
