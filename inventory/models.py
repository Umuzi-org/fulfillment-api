from django.db import models
from django.conf import settings

class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    warehouses = models.ManyToManyField(
        Warehouse,
        related_name="products",
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sku} {self.name}"

class StockMovement(models.Model):
    class Direction(models.TextChoices):
        IN = "IN", "In"
        OUT = "OUT", "Out"

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )
    direction = models.CharField(max_length=3, choices=Direction.choices)
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.direction} {self.quantity} {self.product}"