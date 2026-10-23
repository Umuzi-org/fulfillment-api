import json
import os
from unittest.mock import patch

from django.db import Error as DatabaseError
from django.test import RequestFactory, SimpleTestCase, TestCase
from rest_framework.exceptions import APIException

from config.exceptions import api_exception_handler, server_error
from config.settings import BASE_DIR, database_from_environment


class DatabaseSettingsTests(SimpleTestCase):
    def test_sqlite_is_used_when_postgres_is_unset(self):
        with patch.dict(os.environ, {'POSTGRES_DB': ''}, clear=False):
            config = database_from_environment()

        self.assertEqual(
            config['default']['ENGINE'],
            'django.db.backends.sqlite3',
        )
        self.assertEqual(config['default']['NAME'], BASE_DIR / 'db.sqlite3')

    def test_postgres_is_used_when_the_environment_names_a_database(self):
        with patch.dict(
            os.environ,
            {
                'POSTGRES_DB': 'fulfilment',
                'POSTGRES_USER': 'app',
                'POSTGRES_PASSWORD': 'secret',
                'POSTGRES_HOST': 'db',
                'POSTGRES_PORT': '5433',
            },
            clear=False,
        ):
            config = database_from_environment()

        self.assertEqual(
            config['default'],
            {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'fulfilment',
                'USER': 'app',
                'PASSWORD': 'secret',
                'HOST': 'db',
                'PORT': '5433',
            },
        )

    def test_postgres_defaults_the_host_and_port(self):
        with patch.dict(
            os.environ,
            {'POSTGRES_DB': 'fulfilment'},
            clear=False,
        ):
            os.environ.pop('POSTGRES_USER', None)
            os.environ.pop('POSTGRES_PASSWORD', None)
            os.environ.pop('POSTGRES_HOST', None)
            os.environ.pop('POSTGRES_PORT', None)
            config = database_from_environment()

        self.assertEqual(config['default']['USER'], '')
        self.assertEqual(config['default']['PASSWORD'], '')
        self.assertEqual(config['default']['HOST'], 'localhost')
        self.assertEqual(config['default']['PORT'], '5432')


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
        with patch(
            "config.health.connection.cursor",
            side_effect=DatabaseError("down"),
        ):
            response = self.client.get("/health/")

        body = response.json()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(body["status"], "unavailable")
        self.assertEqual(body["database"], "unavailable")
        self.assertIsInstance(body["uptime_seconds"], int)


class ErrorHandlerTests(TestCase):
    def test_unhandled_exception_is_left_to_django(self):
        self.assertIsNone(api_exception_handler(RuntimeError("boom"), {}))

    def test_list_error_uses_the_fallback_message(self):
        class ListError(APIException):
            status_code = 400
            default_detail = ["bad"]
            default_code = "bad_request"

        response = api_exception_handler(ListError(), {})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "bad_request")
        self.assertEqual(response.data["error"]["message"], "Request failed.")
        self.assertEqual(response.data["error"]["details"], {})

    def test_server_error_uses_the_error_schema(self):
        response = server_error(RequestFactory().get("/"))

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            json.loads(response.content),
            {
                "error": {
                    "code": "server_error",
                    "message": "Something went wrong.",
                    "details": {},
                }
            },
        )
