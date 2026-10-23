from django.test import override_settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APITestCase

from accounts.models import Account
from config.exceptions import api_exception_handler


class LoginTests(APITestCase):
    def setUp(self):
        self.account = Account.objects.create_user(
            "Ada@Example.com",
            "correct-horse",
        )

    def test_login_returns_tokens(self):
        response = self.client.post(
            "/api/auth/token/",
            {"email": "Ada@Example.com", "password": "correct-horse"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejects_a_bad_password(self):
        response = self.client.post(
            "/api/auth/token/",
            {"email": "ada@example.com", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_refresh_returns_a_new_access_token(self):
        login = self.client.post(
            "/api/auth/token/",
            {"email": "ada@example.com", "password": "correct-horse"},
            format="json",
        )

        response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_me_returns_the_signed_in_account(self):
        login = self.client.post(
            "/api/auth/token/",
            {"email": "ada@example.com", "password": "correct-horse"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.account.email)
        self.assertEqual(response.data["role"], "STANDARD")

    def test_me_requires_a_token(self):
        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "not_authenticated")


class ErrorSchemaTests(APITestCase):
    def test_invalid_body_uses_the_error_schema(self):
        response = self.client.post("/api/auth/token/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            {
                "code": "validation_error",
                "message": "Invalid input.",
                "details": {
                    "email": ["This field is required."],
                    "password": ["This field is required."],
                },
            },
        )

    def test_permission_denial_uses_the_error_schema(self):
        response = api_exception_handler(PermissionDenied(), {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")
        self.assertEqual(
            response.data["error"]["message"],
            "You do not have permission to perform this action.",
        )
        self.assertEqual(response.data["error"]["details"], {})

    @override_settings(DEBUG=False)
    def test_unknown_url_uses_the_error_schema(self):
        response = self.client.get("/api/does-not-exist/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.json()["error"],
            {"code": "not_found", "message": "Not found.", "details": {}},
        )
