from unittest.mock import patch

from django.db import Error as DatabaseError
from django.test import TestCase


class HealthTests(TestCase):
    def test_health_does_not_require_a_token(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["database"], "ok")
        self.assertIsInstance(body["uptime_seconds"], int)
        self.assertGreaterEqual(body["uptime_seconds"], 0)

    def test_health_reports_a_database_failure(self):
        with patch("config.health.connection.cursor", side_effect=DatabaseError("down")):
            response = self.client.get("/health/")

        body = response.json()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(body["status"], "unavailable")
        self.assertEqual(body["database"], "unavailable")
        self.assertIsInstance(body["uptime_seconds"], int)
