from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from accounts.models import Role
from accounts.permissions import IsAdminRole
from inventory.models import Product, StockMovement, Warehouse
from inventory.serializers import (
    ProductSerializer,
    StockMovementSerializer,
    WarehouseSerializer,
)


class WarehouseViewSet(ModelViewSet):
    queryset = Warehouse.objects.order_by("name")
    serializer_class = WarehouseSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.prefetch_related("warehouses").order_by("sku")
    serializer_class = ProductSerializer

    def get_queryset(self):
        products = super().get_queryset()
        if getattr(self.request.user, "role", None) != Role.ADMIN:
            return products.filter(is_active=True)
        return products

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]


class StockMovementViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = StockMovementSerializer
    queryset = StockMovement.objects.order_by("-created_at")

    def get_permissions(self):
        if self.action == "create":
            return [IsAdminRole()]
        return [IsAuthenticated()]
