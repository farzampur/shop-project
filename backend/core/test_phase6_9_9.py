from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import AuditLog, Store


class AuditLogIntegrity699Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="audit699")
        self.store = Store.objects.create(name="Audit Store", code="AUD699")

    def _integrity_error(self, **kwargs):
        payload = {
            "user": self.user,
            "store": self.store,
            "action": "other",
            "model_name": "Test",
            "description": "valid",
        }
        payload.update(kwargs)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AuditLog.objects.create(**payload)

    def test_object_id_zero_is_rejected(self):
        self._integrity_error(object_id=0)

    def test_object_id_negative_is_rejected(self):
        self._integrity_error(object_id=-1)

    def test_empty_model_name_is_rejected(self):
        self._integrity_error(model_name="")

    def test_empty_description_is_rejected(self):
        self._integrity_error(description="")

    def test_valid_audit_log_is_still_allowed(self):
        log = AuditLog.objects.create(
            user=self.user,
            store=self.store,
            action="update",
            model_name="Product",
            object_id=1,
            description="ویرایش محصول",
            metadata={"source": "test"},
        )
        self.assertEqual(log.object_id, 1)
