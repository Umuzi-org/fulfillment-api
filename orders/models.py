from django.conf import settings
from django.db import models

from inventory.models import Product


class FulfillmentOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PICKED = "PICKED", "Picked"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="fulfillment_orders",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    products = models.ManyToManyField(
        Product,
        through="OrderLine",
        related_name="fulfillment_orders",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.pk} ({self.status})"


class OrderLine(models.Model):
    order = models.ForeignKey(
        FulfillmentOrder,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_lines",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product} x {self.quantity}"