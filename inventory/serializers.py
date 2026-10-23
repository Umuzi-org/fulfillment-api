from rest_framework import serializers

from inventory.models import Product, Warehouse


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
