from django.contrib.auth.models import User
from django.test import TestCase
from core.models import Store
from .models import StockTransfer


class Phase694TransferTests(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="694 Store", code="694-SRC")
        self.other_store = Store.objects.create(name="694 Other Store", code="694-DST")
        self.user = User.objects.create_user(username="694", password="x")

    def test_transfer_fixture_uses_distinct_destination_store(self):
        transfer = StockTransfer.objects.create(
            source_store=self.store,
            destination_store=self.other_store,
            created_by=self.user,
        )
        self.assertNotEqual(transfer.source_store_id, transfer.destination_store_id)
