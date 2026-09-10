from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch


class Phase68ProductionReadinessTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint_is_public_and_reports_database(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"status": "ok", "database": "ok"})

    @patch("django.db.connection.cursor")
    def test_health_endpoint_returns_503_when_database_is_unavailable(self, cursor):
        cursor.side_effect = RuntimeError("database unavailable")
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, {"status": "error", "database": "unavailable"})
