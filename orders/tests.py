from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Account, Role
from inventory.models import Product
from orders.models import FulfillmentOrder


class FulfillmentOrderApiTests(APITestCase):
    def setUp(self):
        self.password = "correct-horse"
        self.standard = Account.objects.create_user(
            "standard@example.com",
            self.password,
        )
        self.other = Account.objects.create_user(
            "other@example.com",
            self.password,
        )
        self.admin = Account.objects.create_user(
            "admin@example.com",
            self.password,
            role=Role.ADMIN,
        )
        self.crate = Product.objects.create(
            sku="CRATE-1",
            name="Crate",
            unit_price="12.50",
        )
        self.box = Product.objects.create(
            sku="BOX-1",
            name="Box",
            unit_price="3.00",
        )

    def authenticate(self, account):
        login = self.client.post(
            "/api/auth/token/",
            {"email": account.email, "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def create_order(self, lines=None):
        if lines is None:
            lines = [{"product": self.crate.id, "quantity": 2}]
        return self.client.post("/api/orders/", {"lines": lines}, format="json")

    def test_create_copies_the_price_and_assigns_the_signed_in_account(self):
        self.authenticate(self.standard)

        response = self.create_order(
            [
                {"product": self.crate.id, "quantity": 2, "unit_price": "0.01"},
                {"product": self.box.id, "quantity": 1},
            ]
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["account"], self.standard.id)
        self.assertEqual(response.data["status"], FulfillmentOrder.Status.PENDING)
        prices = {line["product"]: line["unit_price"] for line in response.data["lines"]}
        self.assertEqual(prices[self.crate.id], "12.50")
        self.assertEqual(prices[self.box.id], "3.00")

    def test_duplicate_product_is_rejected(self):
        self.authenticate(self.standard)

        response = self.create_order(
            [
                {"product": self.crate.id, "quantity": 1},
                {"product": self.crate.id, "quantity": 2},
            ]
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "validation_error")
        self.assertEqual(FulfillmentOrder.objects.count(), 0)

    def test_standard_user_sees_only_their_orders(self):
        self.authenticate(self.standard)
        own = self.create_order()
        self.authenticate(self.other)
        self.create_order()
        self.authenticate(self.standard)

        listing = self.client.get("/api/orders/")
        other = self.client.get(f"/api/orders/{own.data['id']}/")

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["id"], own.data["id"])
        self.assertEqual(other.status_code, status.HTTP_200_OK)

        self.authenticate(self.other)
        hidden = self.client.get(f"/api/orders/{own.data['id']}/")
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)

    def test_standard_user_can_only_cancel_a_pending_order(self):
        self.authenticate(self.standard)
        created = self.create_order()
        url = f"/api/orders/{created.data['id']}/"

        shipped = self.client.patch(
            url,
            {"status": FulfillmentOrder.Status.SHIPPED},
            format="json",
        )
        cancelled = self.client.patch(
            url,
            {"status": FulfillmentOrder.Status.CANCELLED},
            format="json",
        )

        self.assertEqual(shipped.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(shipped.data["error"]["code"], "validation_error")
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK)
        self.assertEqual(cancelled.data["status"], FulfillmentOrder.Status.CANCELLED)

    def test_admin_can_see_every_order_and_move_status(self):
        self.authenticate(self.standard)
        created = self.create_order()
        self.authenticate(self.admin)

        listing = self.client.get("/api/orders/")
        updated = self.client.patch(
            f"/api/orders/{created.data['id']}/",
            {"status": FulfillmentOrder.Status.SHIPPED},
            format="json",
        )

        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["status"], FulfillmentOrder.Status.SHIPPED)

    def test_anonymous_user_cannot_list_orders(self):
        response = self.client.get("/api/orders/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_lines_and_initial_status_are_fixed_at_creation(self):
        self.authenticate(self.standard)

        empty = self.client.post("/api/orders/", {"lines": []}, format="json")
        created = self.create_order()
        changed = self.client.patch(
            f"/api/orders/{created.data['id']}/",
            {"lines": [{"product": self.box.id, "quantity": 1}]},
            format="json",
        )
        shipped = self.client.post(
            "/api/orders/",
            {
                "status": FulfillmentOrder.Status.SHIPPED,
                "lines": [{"product": self.crate.id, "quantity": 1}],
            },
            format="json",
        )
        pending = self.client.post(
            "/api/orders/",
            {
                "status": FulfillmentOrder.Status.PENDING,
                "lines": [{"product": self.crate.id, "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(empty.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(changed.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(shipped.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(pending.status_code, status.HTTP_201_CREATED)
        order = FulfillmentOrder.objects.get(pk=created.data["id"])
        self.assertEqual(str(order), f"Order {order.pk} (PENDING)")
        self.assertEqual(str(order.lines.get()), "CRATE-1 Crate x 2")
