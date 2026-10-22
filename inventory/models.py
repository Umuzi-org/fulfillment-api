from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction

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
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    warehouses = models.ManyToManyField(
        Warehouse,
        related_name="products",
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_active"], name="product_is_active_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="product_price_gte_0",
            ),
        ]

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
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["product", "created_at"],
                name="movement_product_created_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="movement_qty_gte_1",
            ),
        ]

    def save(self, *args, **kwargs):
        # A movement is recorded once. Saving it again must not move stock twice.
        if self.pk is not None:
            super().save(*args, **kwargs)
            return

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=self.product_id)
            if self.direction == self.Direction.IN:
                product.stock_quantity += self.quantity
            elif self.direction == self.Direction.OUT:
                if self.quantity > product.stock_quantity:
                    raise ValidationError(
                        {"quantity": "Not enough stock to move out."}
                    )
                product.stock_quantity -= self.quantity
            else:
                raise ValidationError({"direction": "Direction must be IN or OUT."})
            product.save(update_fields=["stock_quantity"])
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.direction} {self.quantity} {self.product}"