from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from accounts.models import Role
from accounts.permissions import IsAdminRole
from inventory.models import Product, Warehouse
from inventory.serializers import ProductSerializer, WarehouseSerializer


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
