from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Account
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
