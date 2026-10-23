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


class ProductApiTests(APITestCase):
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
        self.active = Product.objects.create(
            sku="CRATE-1",
            name="Crate",
            unit_price="12.50",
        )
        self.inactive = Product.objects.create(
            sku="CRATE-2",
            name="Old crate",
            unit_price="4.00",
            is_active=False,
        )
        self.active.warehouses.add(self.warehouse)

    def authenticate(self, account):
        login = self.client.post(
            "/api/auth/token/",
            {"email": account.email, "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    def test_standard_user_sees_only_active_products(self):
        self.authenticate(self.standard)

        listing = self.client.get("/api/products/")
        active = self.client.get(f"/api/products/{self.active.id}/")
        inactive = self.client.get(f"/api/products/{self.inactive.id}/")

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [product["sku"] for product in listing.data["results"]],
            ["CRATE-1"],
        )
        self.assertEqual(active.status_code, status.HTTP_200_OK)
        self.assertEqual(active.data["warehouses"], [self.warehouse.id])
        self.assertEqual(inactive.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(inactive.data["error"]["code"], "not_found")

    def test_admin_sees_inactive_products(self):
        self.authenticate(self.admin)

        listing = self.client.get("/api/products/")
        inactive = self.client.get(f"/api/products/{self.inactive.id}/")

        self.assertEqual(
            [product["sku"] for product in listing.data["results"]],
            ["CRATE-1", "CRATE-2"],
        )
        self.assertEqual(inactive.status_code, status.HTTP_200_OK)
        self.assertFalse(inactive.data["is_active"])

    def test_anonymous_user_cannot_list_products(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_standard_user_cannot_change_products(self):
        self.authenticate(self.standard)

        response = self.client.post(
            "/api/products/",
            {"sku": "NEW-1", "name": "New", "unit_price": "1.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "permission_denied")

    def test_admin_can_create_a_product_in_a_warehouse(self):
        self.authenticate(self.admin)

        created = self.client.post(
            "/api/products/",
            {
                "sku": "BOX-1",
                "name": "Box",
                "description": "Cardboard",
                "unit_price": "3.25",
                "warehouses": [self.warehouse.id],
            },
            format="json",
        )

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["stock_quantity"], 0)
        self.assertEqual(created.data["warehouses"], [self.warehouse.id])
        product = Product.objects.get(sku="BOX-1")
        self.assertEqual(list(product.warehouses.all()), [self.warehouse])

    def test_admin_create_rejects_a_negative_price(self):
        self.authenticate(self.admin)

        response = self.client.post(
            "/api/products/",
            {"sku": "BOX-2", "name": "Box", "unit_price": "-1.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "validation_error")
        self.assertFalse(Product.objects.filter(sku="BOX-2").exists())
