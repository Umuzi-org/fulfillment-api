from django.test import override_settings
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APITestCase

from accounts.models import Account, Role
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


class AccountApiTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse"
        self.standard = Account.objects.create_user(
            "standard@example.com",
            self.password,
        )
        self.admin = Account.objects.create_user(
            "admin@example.com",
            self.password,
            role=Role.ADMIN,
        )

    def authenticate(self, account):
        login = self.client.post(
            "/api/auth/token/",
            {"email": account.email, "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def test_admin_can_list_and_create_accounts(self):
        self.authenticate(self.admin)

        listing = self.client.get("/api/accounts/")
        created = self.client.post(
            "/api/accounts/",
            {
                "email": "New.User@Example.com",
                "password": "a-private-passphrase",
                "role": Role.STANDARD,
            },
            format="json",
        )

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 2)
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["email"], "new.user@example.com")
        self.assertNotIn("password", created.data)
        account = Account.objects.get(email="new.user@example.com")
        self.assertTrue(account.check_password("a-private-passphrase"))

    def test_standard_user_cannot_list_accounts(self):
        self.authenticate(self.standard)

        response = self.client.get("/api/accounts/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    def test_user_can_update_their_own_account(self):
        self.authenticate(self.standard)

        response = self.client.patch(
            f"/api/accounts/{self.standard.id}/",
            {"password": "a-new-passphrase"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", response.data)
        self.standard.refresh_from_db()
        self.assertTrue(self.standard.check_password("a-new-passphrase"))

    def test_user_cannot_read_another_account_or_change_role(self):
        self.authenticate(self.standard)

        other = self.client.get(f"/api/accounts/{self.admin.id}/")
        role_change = self.client.patch(
            f"/api/accounts/{self.standard.id}/",
            {"role": Role.ADMIN},
            format="json",
        )

        self.assertEqual(other.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(role_change.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(role_change.data["error"]["code"], "validation_error")
        self.standard.refresh_from_db()
        self.assertEqual(self.standard.role, Role.STANDARD)
