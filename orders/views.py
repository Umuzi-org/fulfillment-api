from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from accounts.models import Role
from orders.models import FulfillmentOrder
from orders.serializers import FulfillmentOrderSerializer


class FulfillmentOrderViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = FulfillmentOrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = FulfillmentOrder.objects.prefetch_related(
        "lines",
    ).order_by("-created_at")

    def get_queryset(self):
        orders = super().get_queryset()
        if getattr(self.request.user, "role", None) != Role.ADMIN:
            return orders.filter(account=self.request.user)
        return orders
