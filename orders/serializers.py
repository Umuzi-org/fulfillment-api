from django.db import transaction
from rest_framework import serializers

from accounts.models import Role
from inventory.models import Product
from orders.models import FulfillmentOrder, OrderLine


class OrderLineSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
    )

    class Meta:
        model = OrderLine
        fields = ("id", "product", "quantity", "unit_price")
        read_only_fields = ("id", "unit_price")


class FulfillmentOrderSerializer(serializers.ModelSerializer):
    lines = OrderLineSerializer(many=True)

    class Meta:
        model = FulfillmentOrder
        fields = (
            "id",
            "account",
            "status",
            "lines",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "account", "created_at", "updated_at")

    def validate(self, attrs):
        lines = attrs.get("lines")
        if self.instance is None:
            if not lines:
                raise serializers.ValidationError(
                    {"lines": "An order needs at least one line."}
                )
            product_ids = [line["product"].pk for line in lines]
            if len(product_ids) != len(set(product_ids)):
                raise serializers.ValidationError(
                    {"lines": "A product can appear only once on an order."}
                )
        elif lines is not None:
            raise serializers.ValidationError(
                {"lines": "Order lines cannot be changed."}
            )
        return attrs

    def validate_status(self, value):
        if self.instance is None:
            if value != FulfillmentOrder.Status.PENDING:
                raise serializers.ValidationError("A new order starts as PENDING.")
            return value

        user = self.context["request"].user
        if getattr(user, "role", None) == Role.ADMIN:
            return value
        cancelling_pending = (
            self.instance.status == FulfillmentOrder.Status.PENDING
            and value == FulfillmentOrder.Status.CANCELLED
        )
        if cancelling_pending:
            return value
        raise serializers.ValidationError(
            "You can only cancel an order while it is pending."
        )

    def create(self, validated_data):
        lines = validated_data.pop("lines")
        with transaction.atomic():
            order = FulfillmentOrder.objects.create(
                account=self.context["request"].user,
                status=FulfillmentOrder.Status.PENDING,
            )
            for line in lines:
                product = line["product"]
                OrderLine.objects.create(
                    order=order,
                    product=product,
                    quantity=line["quantity"],
                    unit_price=product.unit_price,
                )
        return order

    def update(self, instance, validated_data):
        validated_data.pop("lines", None)
        return super().update(instance, validated_data)
