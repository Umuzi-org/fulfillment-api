from django.conf import settings
from django.core.validators import MinValueValidator
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

    class Meta:
        indexes = [
            models.Index(
                fields=["account", "status"],
                name="order_account_status_idx",
            ),
            models.Index(fields=["created_at"], name="order_created_at_idx"),
        ]

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
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_product_per_order",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="order_line_qty_gte_1",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="order_line_price_gte_0",
            ),
        ]

    def __str__(self):
        return f"{self.product} x {self.quantity}"
