from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Account, Role
from inventory.models import Product, StockMovement, Warehouse


class StockMovementTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create_user("keeper@example.com", "correct-horse")
        self.warehouse = Warehouse.objects.create(
            name="Main",
            location="Dock 1",
            capacity=100,
        )
        self.product = Product.objects.create(
            sku="CRATE-1",
            name="Crate",
            unit_price="5.00",
            stock_quantity=0,
        )

    def test_in_increases_stock(self):
        StockMovement.objects.create(
            account=self.account,
            product=self.product,
            warehouse=self.warehouse,
            direction=StockMovement.Direction.IN,
            quantity=4,
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 4)

    def test_out_decreases_stock(self):
        StockMovement.objects.create(
            account=self.account,
            product=self.product,
            warehouse=self.warehouse,
            direction=StockMovement.Direction.IN,
            quantity=4,
        )
        StockMovement.objects.create(
            account=self.account,
            product=self.product,
            warehouse=self.warehouse,
            direction=StockMovement.Direction.OUT,
            quantity=3,
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 1)

    def test_out_larger_than_stock_is_rejected(self):
        StockMovement.objects.create(
            account=self.account,
            product=self.product,
            warehouse=self.warehouse,
            direction=StockMovement.Direction.IN,
            quantity=2,
        )

        with self.assertRaises(ValidationError):
            StockMovement.objects.create(
                account=self.account,
                product=self.product,
                warehouse=self.warehouse,
                direction=StockMovement.Direction.OUT,
                quantity=3,
            )

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 2)
        self.assertEqual(StockMovement.objects.count(), 1)

    def test_saving_an_existing_movement_does_not_move_stock_again(self):
        movement = StockMovement.objects.create(
            account=self.account,
            product=self.product,
            warehouse=self.warehouse,
            direction=StockMovement.Direction.IN,
            quantity=4,
        )

        movement.note = "received"
        movement.save()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 4)


class WarehouseApiTests(APITestCase):
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
        self.warehouse = Warehouse.objects.create(
            name="Main",
            location="Dock 1",
            capacity=100,
        )

    def authenticate(self, account):
        login = self.client.post(
            "/api/auth/token/",
            {"email": account.email, "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def test_signed_in_user_can_list_and_retrieve(self):
        self.authenticate(self.standard)

        listing = self.client.get("/api/warehouses/")
        detail = self.client.get(f"/api/warehouses/{self.warehouse.id}/")

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(listing.data["results"][0]["name"], "Main")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["location"], "Dock 1")

    def test_anonymous_user_cannot_list(self):
        response = self.client.get("/api/warehouses/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"]["code"], "not_authenticated")

    def test_standard_user_cannot_change_warehouses(self):
        self.authenticate(self.standard)
        payload = {"name": "Annex", "location": "Dock 2", "capacity": 10}

        created = self.client.post("/api/warehouses/", payload, format="json")
        updated = self.client.patch(
            f"/api/warehouses/{self.warehouse.id}/",
            {"name": "Renamed"},
            format="json",
        )
        deleted = self.client.delete(f"/api/warehouses/{self.warehouse.id}/")

        self.assertEqual(created.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(updated.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(deleted.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(created.data["error"]["code"], "permission_denied")
        self.assertTrue(Warehouse.objects.filter(pk=self.warehouse.id).exists())

    def test_admin_can_create_update_and_delete(self):
        self.authenticate(self.admin)

        created = self.client.post(
            "/api/warehouses/",
            {"name": "Annex", "location": "Dock 2", "capacity": 10},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        warehouse_id = created.data["id"]

        updated = self.client.patch(
            f"/api/warehouses/{warehouse_id}/",
            {"capacity": 25},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["capacity"], 25)

        deleted = self.client.delete(f"/api/warehouses/{warehouse_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Warehouse.objects.filter(pk=warehouse_id).exists())
