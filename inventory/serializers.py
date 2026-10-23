from rest_framework import serializers

from inventory.models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ("id", "name", "location", "capacity")
        read_only_fields = ("id",)
