from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from inventory.models import Product, StockMovement, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ("id", "name", "location", "capacity")
        read_only_fields = ("id",)


class ProductSerializer(serializers.ModelSerializer):
    warehouses = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Warehouse.objects.all(),
        required=False,
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "description",
            "unit_price",
            "stock_quantity",
            "warehouses",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "stock_quantity", "created_at")


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = (
            "id",
            "account",
            "product",
            "warehouse",
            "direction",
            "quantity",
            "note",
            "created_at",
        )
        read_only_fields = ("id", "account", "created_at")

    def create(self, validated_data):
        try:
            return StockMovement.objects.create(
                account=self.context["request"].user,
                **validated_data,
            )
        except DjangoValidationError as exc:
            detail = getattr(exc, "message_dict", None) or exc.messages
            raise serializers.ValidationError(detail)
