from rest_framework.routers import DefaultRouter

from inventory.views import WarehouseViewSet

router = DefaultRouter()
router.register("warehouses", WarehouseViewSet, basename="warehouse")

urlpatterns = router.urls
