from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Account


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
