from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from accounts.permissions import IsAdminRole
from inventory.models import Warehouse
from inventory.serializers import WarehouseSerializer


class WarehouseViewSet(ModelViewSet):
    queryset = Warehouse.objects.order_by("name")
    serializer_class = WarehouseSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdminRole()]
