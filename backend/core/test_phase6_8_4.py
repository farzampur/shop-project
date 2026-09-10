from django.conf import settings
from pathlib import Path
import importlib
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class Phase684ProductionConfigurationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint_remains_public(self):
        response = self.client.get(reverse("health"))
        self.assertIn(response.status_code, (200, 503))

    def test_production_configuration_is_environment_driven(self):
        self.assertTrue(settings.SECRET_KEY)
        self.assertNotEqual(settings.SECRET_KEY, "django-insecure-(k73h0bemwb*9v#5#6^&uu9ep15k&-@h!73$c7_ca+!gv0k8&u")
        self.assertTrue(hasattr(settings, "CSRF_TRUSTED_ORIGINS"))
        self.assertTrue(settings.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertEqual(settings.X_FRAME_OPTIONS, "DENY")

    def test_database_password_is_environment_driven(self):
        settings_path = Path(importlib.import_module("config.settings").__file__).resolve()
        source = settings_path.read_text(encoding="utf-8")
        self.assertIn('"PASSWORD": os.getenv("DB_PASSWORD", "")', source)
        self.assertNotIn('"PASSWORD": os.getenv("DB_PASSWORD", "123456")', source)
        self.assertNotIn("'PASSWORD': os.getenv('DB_PASSWORD', '123456')", source)


    def test_production_https_defaults_are_secure_when_debug_is_disabled(self):
        settings_path = Path(importlib.import_module("config.settings").__file__).resolve()
        source = settings_path.read_text(encoding="utf-8")
        self.assertIn("SECURE_SSL_REDIRECT = _env_bool(\"SECURE_SSL_REDIRECT\", not DEBUG)", source)
        self.assertIn("SESSION_COOKIE_SECURE = _env_bool(\"SESSION_COOKIE_SECURE\", not DEBUG)", source)
        self.assertIn("CSRF_COOKIE_SECURE = _env_bool(\"CSRF_COOKIE_SECURE\", not DEBUG)", source)
        self.assertIn('"31536000" if not DEBUG else "0"', source)
